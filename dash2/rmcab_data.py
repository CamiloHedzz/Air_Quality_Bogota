"""Datos de estaciones para Dash: lectura local, sin descargas ni entrenamiento."""

import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .dash_logic import MONTH_NAMES


DATA_PATH = Path(__file__).resolve().parents[1] / "data/samples/rmcab_pilot_2015_2025.csv"
VARIABLES = {
    "pm_25": ("PM2.5", "µg/m³"),
    "pm_10": ("PM10", "µg/m³"),
    "temperature": ("Temperatura", "°C"),
    "humidity": ("Humedad relativa", "%"),
}
STATISTICS = {"mean": "Promedio", "median": "Mediana", "max": "Máximo"}
FREQUENCIES = {"hour": ("Horaria", "h"), "day": ("Diaria", "D"), "week": ("Semanal", "W-MON"), "month": ("Mensual", "MS")}


def load_samples(path=DATA_PATH):
    """Verifica el contrato y manifiesto antes de exponer valores publicados."""
    path = Path(path)
    data = pd.read_csv(path, dtype={"station_id": "string"})
    required = {"datetime", "report_date", "station_id", "station_name", "source_url", "source_sha256", "record_type", "validation_status", *VARIABLES}
    required.update(f"{variable}_origin" for variable in VARIABLES)
    if not required.issubset(data):
        raise ValueError(f"Faltan columnas RMCAB: {sorted(required - set(data))}")
    data["datetime"] = pd.to_datetime(data["datetime"], utc=True, errors="raise").dt.tz_convert("America/Bogota")
    data["report_date"] = pd.to_datetime(data["report_date"], errors="raise").dt.normalize()
    if data[["datetime", "report_date", "station_id", "station_name"]].isna().any().any():
        raise ValueError("Hay estaciones o fechas ausentes en la muestra RMCAB.")
    if data.duplicated(["station_id", "datetime"]).any():
        raise ValueError("Hay observaciones repetidas por estación y hora.")
    local_time = data["datetime"].dt.tz_localize(None)
    if not (local_time.gt(data.report_date) & local_time.le(data.report_date + pd.Timedelta(days=1))).all():
        raise ValueError("La hora de la medición no corresponde a su reporte diario.")
    if not data.record_type.eq("station_observation").all():
        raise ValueError("Este panel solo admite observaciones de estación.")
    for variable in VARIABLES:
        origin = data[f"{variable}_origin"]
        if not origin.isin(["observed", "missing", "range_review"]).all():
            raise ValueError("No se admiten valores imputados como mediciones del panel.")
        values = pd.to_numeric(data[variable], errors="raise")
        if (origin.eq("observed") & (values.isna() | ~np.isfinite(values))).any():
            raise ValueError(f"Una observación de {variable} no tiene valor numérico.")
        if (origin.ne("observed") & values.notna()).any():
            raise ValueError(f"Un valor no observado de {variable} conserva una medición.")
        if variable == "humidity" and values.dropna().between(0, 100).eq(False).any():
            raise ValueError("Humedad fuera de 0–100 % en observaciones.")
        if variable in ("pm_25", "pm_10") and values.dropna().lt(0).any():
            raise ValueError("Concentración negativa en observaciones.")
        data[variable] = values
    sources = json.loads(path.with_suffix(".sources.json").read_text(encoding="utf-8"))
    by_date = {entry["report_date"]: entry for entry in sources}
    for day, group in data.groupby("report_date"):
        source = by_date.get(day.strftime("%Y-%m-%d"))
        if not source or not group.source_sha256.eq(source["sha256"]).all() or not group.source_url.eq(source["url"]).all():
            raise ValueError("La procedencia de un reporte no coincide con el manifiesto.")
    data["station_label"] = data.station_name.str.title()
    return data.sort_values(["datetime", "station_id"]).reset_index(drop=True)


def year_options(data, variable):
    years = data.loc[data[variable].notna(), "report_date"].dt.year.unique()
    return [{"label": str(year), "value": int(year)} for year in sorted(years)]


def filter_period(data, year, month="all", stations=None):
    result = data.loc[data.report_date.dt.year.eq(int(year))] if year is not None else data.iloc[:0]
    if month not in (None, "all"):
        result = result.loc[result.report_date.dt.month.eq(int(month))]
    if stations is not None:
        result = result.loc[result.station_id.isin([str(station) for station in stations])]
    return result.copy()


def month_options(data, year, variable):
    period = filter_period(data, year)
    months = period.loc[period[variable].notna(), "report_date"].dt.month.unique()
    return [{"label": "Todos los reportes del año", "value": "all"}] + [
        {"label": MONTH_NAMES[month], "value": int(month)} for month in sorted(months)
    ]


def station_options(period, variable):
    counts = period.loc[period[variable].notna()].groupby(["station_id", "station_label"])[variable].count()
    return [{"label": f"{name} · {int(count)} mediciones", "value": station} for (station, name), count in counts.sort_values(ascending=False).items()]


def period_title(year, month="all"):
    if year is None:
        return "Sin periodo disponible"
    return f"Reportes de {year}" if month in (None, "all") else f"{MONTH_NAMES[int(month)]} de {year}"


def overview(period, variable, year, month="all"):
    observed = period.loc[period[variable].notna()]
    expected_days = (366 if calendar.isleap(int(year)) else 365) if year is not None else 0
    if year is not None and month not in (None, "all"):
        expected_days = calendar.monthrange(int(year), int(month))[1]
    return {"stations": int(observed.station_id.nunique()), "observations": len(observed), "slots": len(period),
            "report_days": int(period.report_date.nunique()), "calendar_days": expected_days,
            "presence_pct": 100 * len(observed) / len(period) if len(period) else 0,
            "start": period.report_date.min() if not period.empty else None,
            "end": period.report_date.max() if not period.empty else None}


def time_series(period, variable, frequency="hour", statistic="mean"):
    rule = FREQUENCIES[frequency][1]
    rows = []
    for station, group in period.groupby("station_id", sort=True):
        values = group.set_index("datetime")[variable].sort_index()
        values = values.resample(rule).agg([statistic, "count"]).rename(columns={statistic: "value", "count": "observations"})
        values["station_id"] = station
        values["station_label"] = group.station_label.iloc[0]
        rows.append(values.reset_index())
    if not rows:
        return pd.DataFrame(columns=["datetime", "value", "observations", "station_id", "station_label"])
    return pd.concat(rows, ignore_index=True)


def station_summary(period, variable, statistic="mean"):
    if period.empty:
        return pd.DataFrame(columns=["station_id", "station_label", "value", "observations", "slots", "presence_pct"])
    result = period.groupby(["station_id", "station_label"], as_index=False).agg(
        value=(variable, statistic), observations=(variable, "count"), slots=(variable, "size"))
    result["presence_pct"] = 100 * result.observations / result.slots
    return result


def export_records(period):
    exported = period.drop(columns=["station_label"], errors="ignore").copy()
    for variable, (_, unit) in VARIABLES.items():
        exported[f"{variable}_unit"] = unit
    return exported
