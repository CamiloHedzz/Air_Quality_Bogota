"""Ingesta y preparación de históricos de RMCAB con trazabilidad por variable.

Los reportes públicos son evidencia publicada, no certificación de validación final.
Este módulo nunca sobrescribe los CSV de dash2/datasets ni genera años sintéticos.
"""

from __future__ import annotations

from datetime import datetime, timezone
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

TIMEZONE = "America/Bogota"
VARIABLES = ["pm_25", "pm_10", "temperature", "humidity"]
UNITS = {"pm_25": "µg/m³", "pm_10": "µg/m³", "temperature": "°C", "humidity": "%"}
PORTAL = "https://rmcab.ambientebogota.gov.co/Report/HourlyReports"
# HR_2m usa otra altura; no se mezcla automáticamente con HR (p. ej. en Tunal).
# También se excluyen explícitamente Humedad Inter y Tempe Inter.
CHANNELS = {"PM2.5": "pm_25", "PM10": "pm_10", "Temperatura": "temperature", "HR": "humidity"}
EXPECTED_UNITS = {"pm_25": {"µg/m3", "μg/m3", "µg/m³", "μg/m³"}, "pm_10": {"µg/m3", "μg/m3", "µg/m³", "μg/m³"}, "temperature": {"°C"}, "humidity": {"%"}}


def audit_legacy(path):
    data = pd.read_csv(path)
    dates = pd.to_datetime(data["datetime"], errors="coerce", format="mixed")
    return {
        "source_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "rows": len(data), "date_min": str(dates.min()), "date_max": str(dates.max()),
        "years": {str(k): int(v) for k, v in dates.dt.year.value_counts().sort_index().items()},
        "distinct_days": int(dates.dt.normalize().nunique()),
        "neighborhoods": int(data["neighborhood"].nunique()),
        "duplicates": int(data.duplicated().sum()),
        "missing": {k: int(v) for k, v in data.isna().sum().items()},
        "negative_humidity": int(data["humidity"].lt(0).sum()),
        "pm25_above_pm10": int(data["pm_25"].gt(data["pm_10"]).sum()),
        "units_status": "unknown: no calibration or preprocessing metadata found",
    }


class _ReportTables(HTMLParser):
    """Lee únicamente las tablas visibles; no ejecuta scripts ni atributos onclick."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.report_date = None
        self.station = None
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("id") == "pageDate":
            self.report_date = attrs.get("value")
        if tag == "div" and "TableStation" in attrs.get("class", "").split():
            self.station = {"station_id": attrs.get("id", "").removeprefix("S_"), "station_name": attrs.get("data-station", "")}
        if tag == "table" and "DataTable" in attrs.get("class", "").split():
            if not self.station or not self.station["station_id"]:
                raise ValueError("Tabla sin identificador de estación; revisar el formato del portal.")
            self.table = {**self.station, "rows": []}
            self.tables.append(self.table)
        if self.table is not None:
            if tag == "tr":
                self.row = []
            if tag in ("th", "td"):
                self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None and self.table is not None:
            self.table["rows"].append(self.row)
            self.row = None
        if tag == "table":
            self.table = None


def report_url(day):
    day = pd.Timestamp(day).date().isoformat()
    return PORTAL + "?" + urlencode({"UserDateString": day, "id": 1})


def parse_hourly_report(raw: bytes, day: str):
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        # El portal sirve caracteres españoles y µ en Windows-1252.
        html = raw.decode("cp1252")
    parser = _ReportTables()
    parser.feed(html)
    expected_date = pd.Timestamp(day).strftime("%d-%m-%Y")
    if parser.report_date != expected_date or not parser.tables:
        raise ValueError(f"Reporte de fecha incorrecta o sin tablas: se esperaba {expected_date}, llegó {parser.report_date}.")
    records = []
    for table in parser.tables:
        rows = table["rows"]
        if not rows or rows[0][5:] != [f"{hour:02d}" for hour in range(1, 25)]:
            raise ValueError("Las columnas horarias cambiaron; no se importó el reporte.")
        channels = {}
        channel_names = {}
        for row in rows[1:]:
            if len(row) < 3 or row[1] not in CHANNELS:
                continue
            variable = CHANNELS[row[1]]
            if len(row) != 29 or row[2] not in EXPECTED_UNITS[variable]:
                raise ValueError(f"Unidad o columnas desconocidas: {table['station_name']} {row[1:3]}")
            if variable in channels:
                raise ValueError(f"Dos sensores para {variable} en {table['station_name']}; elegir y documentar el canal antes de unirlos.")
            channels[variable] = row[5:]
            channel_names[variable] = row[1]
        for hour in range(1, 25):
            # El propio portal etiqueta la hora 24 como 00:00 del día siguiente.
            instant = pd.Timestamp(day).tz_localize(TIMEZONE) + pd.Timedelta(hours=hour)
            record = {"datetime": instant, "report_date": pd.Timestamp(day).date().isoformat(), "station_id": table["station_id"], "station_name": table["station_name"]}
            for variable in VARIABLES:
                text = channels.get(variable, [""] * 24)[hour - 1]
                if text in ("", "-", "--", "N/D", "ND"):
                    value = np.nan
                else:
                    try:
                        value = float(text.replace(",", "."))
                    except ValueError as error:
                        raise ValueError(f"Valor no reconocido en {variable}: {text!r}") from error
                record[variable] = value
                record[f"{variable}_channel"] = channel_names.get(variable, "not_listed")
            record.update(source="RMCAB/SDA", source_url=report_url(day), source_sha256=hashlib.sha256(raw).hexdigest(), record_type="station_observation", validation_status="published_quality_not_verified")
            records.append(record)
    data = pd.DataFrame(records)
    if data.duplicated(["station_id", "datetime"]).any():
        raise ValueError("Estación y fecha duplicadas dentro del reporte.")
    return data


def fetch_report(day, cache_dir, *, allow_network=False):
    """Caché comprimida + URL, fecha de descarga y SHA256 del contenido original."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    day = pd.Timestamp(day).date().isoformat()
    content_path = cache_dir / f"{day}.html.gz"
    manifest_path = cache_dir / f"{day}.json"
    if content_path.exists() and manifest_path.exists():
        raw = gzip.decompress(content_path.read_bytes())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
            raise ValueError(f"La caché de {day} no coincide con su hash.")
    else:
        if not allow_network:
            raise FileNotFoundError(f"No hay caché para {day}. Ejecuta la recolección con red habilitada.")
        request = Request(report_url(day), headers={"User-Agent": "AirQualityBogotaResearch/0.1 (public research; cached sequential requests)"})
        with urlopen(request, timeout=45) as response:
            raw = response.read(16_000_001)
        if len(raw) > 16_000_000:
            raise ValueError("El reporte excede el tamaño esperado; revisar antes de procesar.")
        # Validar antes de persistir evita guardar login, error o la fecha actual.
        parse_hourly_report(raw, day)
        manifest = {"source": "RMCAB/SDA", "report_date": day, "url": report_url(day), "downloaded_at_utc": datetime.now(timezone.utc).isoformat(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "validation_status": "published_quality_not_verified"}
        content_path.write_bytes(gzip.compress(raw, mtime=0))
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        time.sleep(2)  # Sin paralelismo contra el servicio público.
    return parse_hourly_report(raw, day), manifest


def collect_reports(days, cache_dir, *, allow_network=False):
    frames, manifests = [], []
    for day in sorted({pd.Timestamp(day).date().isoformat() for day in days}):
        frame, manifest = fetch_report(day, cache_dir, allow_network=allow_network)
        frames.append(frame)
        manifests.append(manifest)
    if not frames:
        raise ValueError("Selecciona al menos una fecha.")
    data = pd.concat(frames, ignore_index=True).sort_values(["datetime", "station_id"])
    if data.duplicated(["station_id", "datetime"]).any():
        raise ValueError("Hay observaciones repetidas; resolver la procedencia antes de combinar.")
    return data.reset_index(drop=True), manifests


def clean_measurements(data):
    """Marca rangos imposibles o de revisión; conserva el valor original en *_raw."""
    result = data.copy()
    result["datetime"] = pd.to_datetime(result["datetime"], utc=True).dt.tz_convert(TIMEZONE)
    for variable in VARIABLES:
        if f"{variable}_raw" in result and f"{variable}_origin" in result:
            # Al concatenar un lote nuevo con uno ya limpio, el lote nuevo no
            # tiene *_raw ni *_origin. No perder sus observaciones publicadas.
            prior = result[f"{variable}_origin"].notna()
            source_values = result[f"{variable}_raw"].where(prior, result[variable])
        else:
            source_values = result.get(f"{variable}_raw", result[variable])
        values = pd.to_numeric(source_values, errors="coerce")
        result[f"{variable}_raw"] = values
        if variable == "humidity":
            valid = values.between(0, 100)
        elif variable == "temperature":
            # Filtro de revisión amplio, no criterio oficial de validación RMCAB.
            valid = values.between(-50, 60)
        else:
            valid = values.ge(0) & np.isfinite(values)
        result[f"{variable}_origin"] = np.select([values.isna(), valid], ["missing", "observed"], default="range_review")
        result[variable] = values.where(valid)
    result["pm25_above_pm10_review"] = result["pm_25"].gt(result["pm_10"])
    return result


def coverage_by_year(data):
    frame = data.copy()
    # Agrupar por fecha del reporte evita contar su hora 24 como otro día consultado.
    frame["year"] = pd.to_datetime(frame["report_date"]).dt.year
    rows = []
    for year, part in frame.groupby("year"):
        days = int(part["report_date"].nunique())
        calendar_days = int(pd.Timestamp(int(year), 12, 31).dayofyear)
        row = {"year": int(year), "report_days": days, "calendar_days": calendar_days, "sampled_calendar_pct": round(100 * days / calendar_days, 2), "listed_stations": int(part.station_id.nunique()), "station_hours": len(part)}
        row.update({f"{variable}_observed": int(part[variable].notna().sum()) for variable in VARIABLES})
        rows.append(row)
    return pd.DataFrame(rows)


def compare_humidity_imputers(data, *, cutoff="2025-01-01", seed=42):
    """Experimento retrospectivo: ocultar bloques conocidos de HR solo en validación.

    Aprende escalas y vecinos exclusivamente de años anteriores. No rellena el
    dataset de salida ni usa valores imputados como verdad para entrenar un target.
    """
    from sklearn.impute import KNNImputer, SimpleImputer
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.preprocessing import StandardScaler

    frame = data.copy()
    cutoff = pd.Timestamp(cutoff).tz_localize(TIMEZONE)
    train = frame.loc[frame.datetime.lt(cutoff), VARIABLES].copy()
    validation = frame.loc[frame.datetime.ge(cutoff)].copy()
    if len(train) < 30 or train.humidity.notna().sum() < 30 or validation.humidity.notna().sum() < 10:
        return pd.DataFrame(), {"status": "insufficient_observed_data"}
    # Máscara de bloques de 3 horas por estación/día: no confundir con test MCAR.
    rng = np.random.default_rng(seed)
    block = validation.datetime.dt.hour.floordiv(3)
    keys = validation.station_id.astype(str) + "|" + validation.datetime.dt.strftime("%Y-%m-%d") + "|" + block.astype(str)
    selected = rng.choice(keys.unique(), size=max(1, int(len(keys.unique()) * 0.25)), replace=False)
    masked = keys.isin(selected) & validation.humidity.notna()
    if masked.sum() < 5:
        return pd.DataFrame(), {"status": "insufficient_masked_observations"}
    if train.notna().sum().eq(0).any():
        return pd.DataFrame(), {"status": "empty_training_feature"}
    features = validation[VARIABLES].copy()
    truth = features.loc[masked, "humidity"].to_numpy()
    features.loc[masked, "humidity"] = np.nan
    scaler = StandardScaler().fit(train)
    train_scaled, test_scaled = scaler.transform(train), scaler.transform(features)
    rows = []
    for name, imputer in [("Mediana", SimpleImputer(strategy="median")), ("KNN escalado", KNNImputer(n_neighbors=5, weights="distance"))]:
        imputer.fit(train_scaled)
        restored = scaler.inverse_transform(imputer.transform(test_scaled))
        prediction = restored[masked.to_numpy(), VARIABLES.index("humidity")]
        rows.append({"method": name, "MAE_percentage_points": mean_absolute_error(truth, prediction), "RMSE_percentage_points": np.sqrt(mean_squared_error(truth, prediction)), "masked_values": int(masked.sum())})
    return pd.DataFrame(rows), {"status": "research_only", "train_rows": len(train), "validation_rows": len(validation), "cutoff": cutoff.isoformat(), "mask": "25% of station/day/3-hour blocks; seed 42", "limitation": "Not station-held-out; historical pilot not a forecasting score or full-year representativeness test."}


def build_forecast_table(data, *, target="pm_25", horizon_hours=24):
    """Prepara X(t), y(t+h) por coincidencia exacta de estación y hora.

    No shift por número de filas: los saltos de años o datos faltantes no equivalen
    a horas. Los objetivos siempre provienen de observaciones y nunca se imputan.
    """
    if target not in VARIABLES or horizon_hours not in (1, 24, 48, 72):
        raise ValueError("Variable u horizonte no soportado.")
    keys = ["station_id", "datetime"]
    frame = data.sort_values(keys).copy()
    if frame.duplicated(keys).any():
        raise ValueError("Estación/hora duplicada en la tabla de modelado.")
    if any(frame[f"{v}_origin"].eq("imputed").any() for v in VARIABLES):
        raise ValueError("La tabla base debe conservar observaciones; imputar predictores dentro del Pipeline.")
    for lag in (1, 24):
        history = frame[keys + [target]].rename(columns={target: f"{target}_lag_{lag}h"})
        history["datetime"] += pd.Timedelta(hours=lag)
        frame = frame.merge(history, on=keys, how="left", validate="one_to_one")
    source_url = f"{target}_source_url" if f"{target}_source_url" in data else "source_url"
    source_hash = f"{target}_source_sha256" if f"{target}_source_sha256" in data else "source_sha256"
    future = data.loc[data[f"{target}_origin"].eq("observed"), keys + [target, source_url, source_hash]].copy()
    future = future.rename(columns={source_url: "source_url", source_hash: "source_sha256"})
    future = future.rename(columns={"datetime": "target_datetime", target: "target_value", "source_url": "target_source_url", "source_sha256": "target_source_sha256"})
    frame["target_datetime"] = frame["datetime"] + pd.Timedelta(hours=horizon_hours)
    frame = frame.merge(future, on=["station_id", "target_datetime"], how="inner", validate="one_to_one")
    frame = frame.loc[frame.target_value.notna()].copy()
    frame["hour_sin"] = np.sin(2 * np.pi * frame.datetime.dt.hour / 24)
    frame["hour_cos"] = np.cos(2 * np.pi * frame.datetime.dt.hour / 24)
    frame["month_sin"] = np.sin(2 * np.pi * frame.datetime.dt.month / 12)
    frame["month_cos"] = np.cos(2 * np.pi * frame.datetime.dt.month / 12)
    frame["weekday"] = frame.datetime.dt.dayofweek
    return frame.sort_values(["datetime", "station_id"]).reset_index(drop=True)


def purged_time_splits(frame, n_splits=3):
    """Mantiene la misma hora de todas las estaciones en un único bloque temporal."""
    from sklearn.model_selection import TimeSeriesSplit

    times = frame.datetime.drop_duplicates().sort_values().to_numpy()
    for train_times, validation_times in TimeSeriesSplit(n_splits=n_splits).split(times):
        validation_start = times[validation_times[0]]
        train = np.flatnonzero(frame.datetime.isin(times[train_times]) & frame.target_datetime.lt(validation_start))
        validation = np.flatnonzero(frame.datetime.isin(times[validation_times]))
        if len(train) and len(validation):
            yield train, validation
