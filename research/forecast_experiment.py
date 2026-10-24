"""Pronóstico exploratorio con etiquetas observadas y cortes temporales purgados.

No descarga, completa años, modifica mediciones ni publica un modelo en la web.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from threadpoolctl import threadpool_limits

from research.air_quality import VARIABLES, build_forecast_table


MODEL_PARAMS = dict(max_iter=80, max_leaf_nodes=15, min_samples_leaf=20,
                    learning_rate=0.05, l2_regularization=1.0,
                    early_stopping=False, random_state=42)
METHODS = ("persistence", "hgb_native_missing", "hgb_train_median")


def feature_columns(target):
    return ["station_id", *VARIABLES, f"{target}_lag_1h", f"{target}_lag_24h",
            "hour_sin", "hour_cos", "month_sin", "month_cos", "weekday"]


def make_model(target, *, impute=False):
    """Categorías e imputador (si se usa) se aprenden solo del entrenamiento."""
    columns = feature_columns(target)
    numeric = SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True) if impute else "passthrough"
    preprocessing = ColumnTransformer([
        ("station", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan), ["station_id"]),
        ("measurements", numeric, columns[1:]),
    ])
    return Pipeline([
        ("features", preprocessing),
        ("model", HistGradientBoostingRegressor(categorical_features=[0], **MODEL_PARAMS)),
    ])


def observed_forecast_table(data, target, horizon):
    """Rechaza estimaciones como verdad y exige una lectura actual para la base."""
    for variable in VARIABLES:
        origin = data[f"{variable}_origin"]
        if not origin.isin(["observed", "missing", "range_review"]).all():
            raise ValueError("No se admiten datos sintéticos o imputados en la tabla base.")
        values = data[variable]
        if (origin.eq("observed") & (values.isna() | ~np.isfinite(values))).any():
            raise ValueError("Observación sin valor finito.")
        if (origin.ne("observed") & values.notna()).any():
            raise ValueError("Una entrada no observada conserva un valor.")
    frame = build_forecast_table(data, target=target, horizon_hours=horizon)
    # La misma cohorte sirve al modelo y a persistencia: no comparar filas distintas.
    return frame.loc[frame[target].notna() & frame[f"{target}_origin"].eq("observed")].reset_index(drop=True)


def temporal_windows(frame, *, last_time, horizon, n_folds=3, validation_hours=24):
    """Ventanas de origen disjuntas; toda etiqueta de train precede a validación."""
    if n_folds < 1 or validation_hours < 1:
        raise ValueError("Selecciona al menos una ventana y una hora.")
    end = last_time - pd.Timedelta(hours=horizon) + pd.Timedelta(hours=1)
    for fold in range(1, n_folds + 1):
        validation_start = end - pd.Timedelta(hours=(n_folds - fold + 1) * validation_hours)
        validation_end = validation_start + pd.Timedelta(hours=validation_hours)
        train = frame.loc[frame.datetime.lt(validation_start) & frame.target_datetime.lt(validation_start)].copy()
        validation = frame.loc[frame.datetime.ge(validation_start) & frame.datetime.lt(validation_end)].copy()
        # Esta primera prueba evalúa estaciones conocidas, no extrapolación espacial.
        unseen = ~validation.station_id.isin(train.station_id.unique())
        yield fold, validation_start, validation_end, train, validation.loc[~unseen].copy(), int(unseen.sum())


def summarize_predictions(predictions, group_columns):
    rows = []
    if predictions.empty:
        return pd.DataFrame()
    for key, part in predictions.groupby(group_columns, sort=True):
        if not isinstance(key, tuple):
            key = (key,)
        rows.append(dict(zip(group_columns, key)) | {
            "n": len(part), "MAE_ug_m3": mean_absolute_error(part.y_true, part.y_pred),
            "RMSE_ug_m3": np.sqrt(mean_squared_error(part.y_true, part.y_pred)),
        })
    return pd.DataFrame(rows)


def run_pilot_benchmark(data, *, targets=("pm_25", "pm_10"), horizons=(1, 24, 48, 72),
                        n_folds=3, validation_hours=24, min_train_hours=48, min_train_rows=200, methods=METHODS):
    """Parámetros fijos, sin búsqueda ni selección sobre las ventanas evaluadas.

    Las predicciones son valores a t+h, no curvas completas emitidas desde un t.
    Las ventanas usan observaciones publicadas como si estuvieran disponibles en t;
    no hay archivo de latencias/revisiones históricas que pruebe esa disponibilidad.
    """
    if data.empty:
        raise ValueError("No hay observaciones para el experimento.")
    if len(set(methods)) != len(methods) or not set(methods).issubset(METHODS) or "persistence" not in methods:
        raise ValueError("Métodos únicos conocidos e incluir persistencia como referencia.")
    last_time = data.datetime.max()
    evaluations, fold_rows = [], []
    for target in targets:
        columns = feature_columns(target)
        for horizon in horizons:
            frame = observed_forecast_table(data, target, horizon)
            for fold, start, end, train, validation, unseen in temporal_windows(
                frame, last_time=last_time, horizon=horizon, n_folds=n_folds, validation_hours=validation_hours
            ):
                row = dict(target=target, horizon_hours=horizon, fold=fold,
                           validation_origin_start=start, validation_origin_end_exclusive=end,
                           train_rows=len(train), train_origin_hours=train.datetime.nunique(),
                           validation_rows=len(validation), unseen_station_rows_excluded=unseen,
                           train_target_max=train.target_datetime.max())
                if train.datetime.nunique() < min_train_hours or len(train) < min_train_rows:
                    row.update(status="skipped", reason="insufficient_past_training_data")
                elif validation.empty:
                    row.update(status="skipped", reason="no_observed_validation_targets")
                else:
                    if not train.target_datetime.max() < validation.datetime.min():
                        raise AssertionError("Una etiqueta de entrenamiento alcanza el periodo validado.")
                    row.update(status="evaluated", reason="exploratory_short_history")
                    estimates = {"persistence": validation[target].to_numpy()}
                    with threadpool_limits(limits=2):
                        for method, impute in [(METHODS[1], False), (METHODS[2], True)]:
                            if method not in methods:
                                continue
                            model = make_model(target, impute=impute)
                            model.fit(train[columns], train.target_value)
                            estimates[method] = model.predict(validation[columns])
                    keys = ["datetime", "target_datetime", "station_id", "station_name", "target_source_url", "target_source_sha256"]
                    for method, values in estimates.items():
                        evaluation = validation[keys].copy()
                        evaluation["y_true"] = validation.target_value.to_numpy()
                        evaluation["y_pred"] = values
                        evaluation = evaluation.assign(target=target, horizon_hours=horizon, fold=fold,
                                                       method=method, record_type="historical_forecast_evaluation")
                        evaluations.append(evaluation)
                fold_rows.append(row)
    predictions = pd.concat(evaluations, ignore_index=True) if evaluations else pd.DataFrame()
    folds = pd.DataFrame(fold_rows)
    scores = summarize_predictions(predictions, ["target", "horizon_hours", "method"])
    per_station = summarize_predictions(predictions, ["target", "horizon_hours", "station_id", "station_name", "method"])
    if not scores.empty:
        reference = scores.loc[scores.method.eq("persistence"), ["target", "horizon_hours", "MAE_ug_m3"]].rename(columns={"MAE_ug_m3": "baseline_MAE"})
        scores = scores.merge(reference, on=["target", "horizon_hours"], validate="many_to_one")
        scores["MAE_skill_vs_persistence"] = np.where(scores.baseline_MAE.gt(0), 1 - scores.MAE_ug_m3 / scores.baseline_MAE, np.nan)
    return {"predictions": predictions, "folds": folds, "scores": scores, "per_station": per_station}
