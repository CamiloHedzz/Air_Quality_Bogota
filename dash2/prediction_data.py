"""Consultas de observaciones y pronósticos históricos, sin entrenar en Django."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from .rmcab_data import VARIABLES
from .history_data import load_observations, source_paths, observation_metadata
from .weather_data import load_weather, analysis_period

ROOT = Path(__file__).resolve().parents[1]
VIEWS = {"evolution", "comparison", "relationship", "hourly", "diagnostics"}
STATS = {"mean", "median", "max"}


def number(value):
    return float(value) if pd.notna(value) and np.isfinite(value) else None


@lru_cache(maxsize=1)
def store():
    paths = [ROOT / p for p in source_paths(ROOT)]
    observations = load_observations(ROOT)
    package = ROOT / "data/forecasts/hgb_historical.csv.gz"
    metadata = json.loads(package.with_name("hgb_historical.json").read_text(encoding="utf-8"))
    if hashlib.sha256(package.read_bytes()).hexdigest() != metadata["forecast_sha256"]:
        raise ValueError("El paquete de pronósticos no coincide con su manifiesto.")
    for path in paths:
        expected = metadata["input_sha256"][path.relative_to(ROOT).as_posix()]
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Los datos cambiaron desde la evaluación del modelo.")
    forecasts = pd.read_csv(package, dtype={"station_id": "string"})
    for column in ["datetime", "target_datetime", "train_target_max", "validation_origin_start"]:
        forecasts[column] = pd.to_datetime(forecasts[column], utc=True).dt.tz_convert("America/Bogota")
    if forecasts.duplicated(["station_id", "datetime", "target", "horizon_hours"]).any():
        raise ValueError("Hay pronósticos históricos duplicados.")
    if not np.isfinite(forecasts[["y_true", "y_pred", "baseline"]]).all().all():
        raise ValueError("Hay pronósticos sin valor numérico.")
    if not (forecasts.target_datetime - forecasts.datetime).eq(pd.to_timedelta(forecasts.horizon_hours, unit="h")).all():
        raise ValueError("El horizonte no coincide con la hora objetivo.")
    if not forecasts.train_target_max.lt(forecasts.datetime).all():
        raise ValueError("El entrenamiento alcanza el origen de validación.")
    for target in ["pm_25", "pm_10"]:
        truth_hash = f"{target}_source_sha256" if f"{target}_source_sha256" in observations else "source_sha256"
        truth = observations[["station_id", "datetime", target, truth_hash]].rename(columns={"datetime": "target_datetime", truth_hash: "source_sha256"})
        joined = forecasts.loc[forecasts.target.eq(target)].merge(truth, on=["station_id", "target_datetime"], validate="many_to_one", how="left")
        if not np.allclose(joined.y_true, joined[target]) or not joined.target_source_sha256.eq(joined.source_sha256).all():
            raise ValueError("La observación objetivo no coincide con la fuente publicada.")
    return observations.reset_index(drop=True), forecasts, metadata


def catalog():
    data, forecasts, model = store()
    stations = data.drop_duplicates("station_id", keep="last")
    years = []
    for year, part in data.groupby(data.report_date.dt.year):
        years.append({"year": int(year), "report_days": int(part.report_date.nunique()),
                      "rows": len(part), "pm_25": int(part.pm_25.count()), "pm_10": int(part.pm_10.count())})
    return {"variables": [{"value": key, "label": label, "unit": unit, "forecast": key in ["pm_25", "pm_10"]} for key, (label, unit) in VARIABLES.items()],
            "stations": [{"value": row.station_id, "label": row.station_label,
                          "forecast": bool(forecasts.station_id.eq(row.station_id).any())} for row in stations.sort_values("station_label").itertuples()],
            "coverage": {"years": years, "report_days": int(data.report_date.nunique()), "rows": len(data),
                         "start": str(data.report_date.min().date()), "end": str(data.report_date.max().date()), "complete": False,
                         "calendar_complete": bool((observation_metadata(ROOT) or {}).get("source_calendar_complete", False)),
                         "source": "SDA/RMCAB y SISAIRE", "weather_source": "Open-Meteo / ERA5 (reanálisis)"},
            "model": {"name": model["model"], "version": model["model_version"], "training_scope": model["training_scope"],
                      "evaluation_start": model["target_report_start"], "evaluation_end": model["target_report_end"],
                      "evaluation_label": model.get("evaluation_label", "25–31 de marzo de 2025"), "evaluation_periods": model.get("evaluation_periods", []),
                      "weather_features": model.get("weather_features", []), "predictor_scope": model.get("predictor_scope", ""),
                      "mode": model["serving_mode"], "iterations": model["parameters"]["max_iter"], "intervals_available": False},
            "defaults": {"station": "5", "variable": "pm_25", "horizon": "24", "history": "7", "aggregation": "hour", "statistic": "mean", "mode": "estimated"}}


def selection(params):
    data, _, _ = store()
    station, variable = params.get("station", "5"), params.get("variable", "pm_25")
    view = params.get("view", "evolution")
    if params.get("mode", "observed") not in {"observed", "estimated"}:
        raise ValueError("Selecciona datos originales o datos con tratamiento.")
    if station not in set(data.station_id.unique()) or variable not in VARIABLES or view not in VIEWS:
        raise ValueError("Selecciona una estación, variable y vista disponibles.")
    if view == "diagnostics" and variable not in {"pm_25", "pm_10"}:
        raise ValueError("La evaluación de HGB está disponible para PM2.5 y PM10.")
    horizon = params.get("horizon", "24")
    if str(horizon) not in {"24", "48", "72"}:
        raise ValueError("El horizonte debe ser 24, 48 o 72 horas.")
    return station, variable, view, int(horizon)


def options(params):
    station, variable, view, horizon = selection(params)
    predicting = view in {"evolution", "diagnostics"} and variable in ["pm_25", "pm_10"]
    mode = params.get("mode", "observed") if variable in {"temperature", "humidity"} and not predicting else "observed"
    return _date_options(station, variable, horizon if predicting else 0, predicting, mode)


@lru_cache(maxsize=8)
def _date_options(station, variable, horizon, predicting, mode):
    data, forecasts, _ = store()
    if predicting:
        part = forecasts.loc[forecasts.station_id.eq(station) & forecasts.target.eq(variable) & forecasts.horizon_hours.eq(horizon)]
    elif mode == "estimated" and variable in {"temperature", "humidity"}:
        weather, mapping, _ = load_weather(ROOT)
        grid = mapping.loc[mapping.station_id.eq(station), "grid_id"].iloc[0]
        part = weather.loc[weather.grid_id.eq(grid) & weather[variable].notna()]
    else:
        part = data.loc[data.station_id.eq(station) & data[variable].notna()]
    instants = part.datetime.sort_values().drop_duplicates().dt.tz_localize(None)
    # Agrupar horas numéricas evita dos strftime por cada una de las 96.432 horas.
    hours = pd.Series(instants.dt.hour.to_numpy(), index=pd.DatetimeIndex(instants.dt.normalize()))
    labels = [f"{hour:02d}:00" for hour in range(24)]
    times = {day.strftime("%Y-%m-%d"): [labels[int(hour)] for hour in group.to_numpy()]
             for day, group in hours.groupby(level=0, sort=True)}
    return {"dates": list(times), "hours": times, "predicting": predicting}


def parse_query(params):
    station, variable, view, horizon = selection(params)
    date, hour = params.get("date", ""), params.get("hour", "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or not re.fullmatch(r"(?:[01]\d|2[0-3]):00", hour):
        raise ValueError("Selecciona una fecha y hora de la lista.")
    available = options(params)
    if hour not in available["hours"].get(date, []):
        raise ValueError("No hay datos para esa estación, fecha y hora. Selecciona una opción disponible.")
    history, statistic, aggregation = str(params.get("history", "7")), params.get("statistic", "mean"), params.get("aggregation", "hour")
    if history not in {"7", "14", "30", "90"} or statistic not in STATS or aggregation not in {"hour", "day"}:
        raise ValueError("Los filtros del histórico no son válidos.")
    origin = pd.Timestamp(f"{date}T{hour}", tz="America/Bogota")
    data, forecasts, model = store()
    comparison = params.get("comparison", "11")
    related = params.get("related", "humidity")
    if comparison not in set(data.station_id.unique()) or related not in VARIABLES or related == variable:
        raise ValueError("Selecciona otra estación o una variable relacionada diferente.")
    if view == "comparison" and comparison == station:
        raise ValueError("Elige dos estaciones distintas para comparar.")
    part = data.loc[data.datetime.between(origin - pd.Timedelta(days=int(history)), origin)].copy()
    mode = params.get("mode", "observed")
    if mode == "estimated":
        part = analysis_period(data, origin - pd.Timedelta(days=int(history)), origin, list(dict.fromkeys([station, comparison])), ROOT)
    primary = part.loc[part.station_id.eq(station)].copy()
    return {"station": station, "variable": variable, "view": view, "horizon": horizon,
            "origin": origin, "history": int(history), "statistic": statistic, "aggregation": aggregation,
            "comparison": comparison, "related": related, "period": part, "primary": primary,
            "forecasts": forecasts, "model": model, "data_mode": mode, "predicting": available["predicting"]}


def series(frame, variable, query):
    origin = query["origin"]
    rule = "h" if query["aggregation"] == "hour" else "D"
    start = (origin - pd.Timedelta(days=query["history"])).floor(rule)
    index = pd.date_range(start, origin.floor(rule), freq=rule)
    values = frame.set_index("datetime")[variable].resample(rule).agg(query["statistic"]) if len(frame) else pd.Series(dtype=float)
    return [{"time": instant.isoformat(), "value": number(value)} for instant, value in values.reindex(index).items()]


def scalar(values, statistic):
    return number(getattr(values.dropna(), statistic)()) if values.notna().any() else None


def forecast(query):
    if not query["predicting"]:
        return None
    matches = query["forecasts"]
    row = matches.loc[matches.station_id.eq(query["station"]) & matches.target.eq(query["variable"]) & matches.horizon_hours.eq(query["horizon"]) & matches.datetime.eq(query["origin"])].iloc[0]
    def score(records, station=False):
        selected = [item for item in records if item["target"] == query["variable"] and item["horizon_hours"] == query["horizon"] and item["method"] == "hgb_native_missing" and (not station or str(item["station_id"]) == query["station"])]
        return {"mae": selected[0]["MAE_ug_m3"], "rmse": selected[0]["RMSE_ug_m3"], "n": selected[0]["n"]} if selected else None
    return {"time": row.target_datetime.isoformat(), "value": float(row.y_pred), "observed_after": float(row.y_true),
            "baseline": float(row.baseline), "absolute_error": abs(float(row.y_pred - row.y_true)),
            "training_end": row.train_target_max.isoformat(), "source_url": row.target_source_url,
            "source_sha256": row.target_source_sha256, "global_score": score(query["model"]["scores"]),
            "station_score": score(query["model"]["station_scores"], station=True)}


def query_result(params):
    query = parse_query(params)
    primary, variable = query["primary"], query["variable"]
    secondary = query["period"].loc[query["period"].station_id.eq(query["comparison"])]
    pairs = primary[["datetime", variable]].merge(secondary[["datetime", variable]], on="datetime", suffixes=("_a", "_b")).dropna()
    related = primary[["datetime", variable, query["related"]]].dropna()
    correlation = None
    if len(related) >= 3 and related[variable].nunique() > 1 and related[query["related"]].nunique() > 1:
        correlation = number(related[variable].corr(related[query["related"]]))
    cells = []
    for day in range(7):
        for block in range(8):
            values = primary.loc[primary.datetime.dt.dayofweek.eq(day) & primary.datetime.dt.hour.floordiv(3).eq(block), variable]
            cells.append({"day": day, "block": block, "value": scalar(values, query["statistic"]), "n": int(values.count())})
    observed = int(primary[variable].count())
    expected = query["history"] * 24 + 1
    result = {"origin": query["origin"].isoformat(), "unit": VARIABLES[variable][1],
              "station": query["station"], "station_name": primary.station_label.iloc[-1] if len(primary) else query["station"],
              "series": series(primary, variable, query), "comparison_series": series(secondary, variable, query),
              "scatter": [{"time": row.datetime.isoformat(), "x": float(row[query["related"]]), "y": float(row[variable])} for _, row in related.iterrows()],
              "heatmap": cells, "forecast": forecast(query),
              "data_mode": query["data_mode"],
              "metrics": {"measured": int(primary[f"{variable}_origin"].eq("observed").sum()),
                          "reanalysis": int(primary[f"{variable}_origin"].eq("weather_reanalysis").sum()), "observed": observed, "expected_hours": expected, "coverage_pct": 100 * observed / expected,
                          "statistic": scalar(primary[variable], query["statistic"]), "max": number(primary[variable].max()),
                          "correlation": correlation, "paired_values": len(related), "comparison_pairs": len(pairs),
                          "comparison_difference": scalar(pairs[f"{variable}_a"] - pairs[f"{variable}_b"], query["statistic"]) if len(pairs) else None},
              "record_count": len(primary), "rows": []}
    for row in primary.sort_values("datetime", ascending=False).head(120).itertuples():
        result["rows"].append({"time": row.datetime.isoformat(), "station": row.station_label,
                               **{key: number(getattr(row, key)) for key in VARIABLES},
                               "origins": {key: getattr(row, f"{key}_origin") for key in VARIABLES}, "source_url": getattr(row, f"{variable}_source_url") or row.source_url})
    if query["view"] == "diagnostics":
        evaluated = query["forecasts"]
        evaluated = evaluated.loc[evaluated.station_id.eq(query["station"]) & evaluated.target.eq(variable) & evaluated.horizon_hours.eq(query["horizon"])]
        errors = evaluated.y_pred - evaluated.y_true
        result["diagnostics"] = {"n": len(evaluated), "mae": number(errors.abs().mean()),
                                 "rmse": number(np.sqrt((errors ** 2).mean())), "bias": number(errors.mean()),
                                 "baseline_mae": number((evaluated.baseline - evaluated.y_true).abs().mean()),
                                 "target_report_start": query["model"]["target_report_start"],
                                 "target_report_end": query["model"]["target_report_end"]}
    return result
