"""Publica resultados históricos reproducibles de HGB para la aplicación web.

No entrena al consultar la web ni convierte el experimento en pronóstico actual.
Ejecutar después de todas las celdas del notebook 03.
"""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def publish(root):
    root = Path(root)
    reports = root / "data/reports/hgb_2025_q1"
    metadata = json.loads((reports / "experiment.json").read_text(encoding="utf-8"))
    for relative, expected in metadata["input_sha256"].items():
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != expected:
            raise ValueError("El dataset cambió: repetir el notebook antes de publicar resultados.")
    predictions = pd.read_csv(root / "data/processed/hgb_2025_q1_holdout_predictions.csv", dtype={"station_id": "string"})
    predictions = predictions.loc[predictions.horizon_hours.isin([24, 48, 72])].copy()
    keys = ["target", "horizon_hours", "fold", "station_id", "datetime", "target_datetime"]
    native = predictions.loc[predictions.method.eq("hgb_native_missing")].copy()
    baseline = predictions.loc[predictions.method.eq("persistence"), keys + ["y_true", "y_pred"]].rename(columns={"y_pred": "baseline", "y_true": "baseline_truth"})
    native = native.merge(baseline, on=keys, validate="one_to_one")
    if not np.allclose(native.y_true, native.baseline_truth):
        raise ValueError("Los comparadores no comparten los mismos objetivos.")
    folds = pd.read_csv(reports / "holdout_folds.csv")
    native = native.merge(folds[["target", "horizon_hours", "fold", "train_target_max", "validation_origin_start"]],
                          on=["target", "horizon_hours", "fold"], validate="many_to_one")
    if not (pd.to_datetime(native.train_target_max, utc=True) < pd.to_datetime(native.datetime, utc=True)).all():
        raise ValueError("Etiquetas de entrenamiento posteriores al origen del pronóstico.")
    columns = ["datetime", "target_datetime", "station_id", "station_name", "target", "horizon_hours",
               "y_pred", "y_true", "baseline", "train_target_max", "validation_origin_start",
               "target_source_url", "target_source_sha256"]
    native = native[columns].sort_values(["target", "horizon_hours", "station_id", "datetime"])
    destination = root / "data/forecasts"
    destination.mkdir(parents=True, exist_ok=True)
    content = gzip.compress(native.to_csv(index=False).encode("utf-8"), mtime=0)
    (destination / "hgb_historical.csv.gz").write_bytes(content)
    package = {
        "schema_version": 1, "model": "HistGradientBoostingRegressor",
        "model_version": metadata["experiment"], "serving_mode": "precomputed_historical_backtest",
        "forecast_sha256": hashlib.sha256(content).hexdigest(), "forecast_rows": len(native),
        "input_sha256": metadata["input_sha256"], "training_years": [2025],
        "training_scope": "Reportes de enero–marzo de 2025; corte temporal específico por horizonte",
        "target_report_start": "2025-03-25", "target_report_end": "2025-03-31",
        "full_history_collected": False, "target_years": [2015, 2025],
        "parameters": metadata["hgb_parameters"],
        "scores": pd.read_csv(reports / "holdout_scores.csv").to_dict("records"),
        "station_scores": pd.read_csv(reports / "holdout_per_station.csv", dtype={"station_id": "string"}).to_dict("records"),
        "source_quality": "published_quality_not_verified", "live_forecast": False,
        "intervals_available": False,
    }
    (destination / "hgb_historical.json").write_text(json.dumps(package, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return package


if __name__ == "__main__":
    package = publish(Path(__file__).resolve().parents[1])
    print(f"Publicados {package['forecast_rows']} pronósticos históricos; sin entrenamiento en el servidor web.")
