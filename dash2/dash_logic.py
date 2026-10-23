"""Period filtering shared by the map, comparisons and time series."""

import calendar

import pandas as pd


METRICS = {
    "pm_25_mean": "pm_25",
    "pm_10_mean": "pm_10",
    "temperature_mean": "temperature",
    "humidity_mean": "humidity",
}
MONTH_NAMES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def valid_samples(samples, valid_neighborhoods=None):
    data = samples.copy()
    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce", format="mixed")
    data = data.loc[
        data["datetime"].notna()
        & data["neighborhood"].notna()
        & data["neighborhood"].ne("Unknown Zone")
    ]
    if valid_neighborhoods is not None:
        data = data.loc[data["neighborhood"].isin(valid_neighborhoods)]
    return data.copy()


def available_years(samples):
    return sorted(valid_samples(samples)["datetime"].dt.year.unique().tolist())


def month_options(samples, year):
    data = filter_period(samples, year)
    months = sorted(data["datetime"].dt.month.unique().tolist())
    return [{"label": "Todo el año", "value": "all"}] + [
        {"label": MONTH_NAMES[month], "value": month} for month in months
    ]


def filter_period(samples, year, month="all"):
    data = valid_samples(samples)
    if year is None:
        return data.iloc[:0].copy()
    data = data.loc[data["datetime"].dt.year.eq(int(year))]
    if month not in (None, "all"):
        data = data.loc[data["datetime"].dt.month.eq(int(month))]
    return data.copy()


def aggregate_neighborhoods(samples):
    return samples.groupby("neighborhood", sort=True).agg(
        **{mean: (column, "mean") for mean, column in METRICS.items()}
    ).reset_index()


def create_time_series(samples, selected_areas, frequency="Diaria"):
    data = samples.loc[samples["neighborhood"].isin(selected_areas or [])].copy()
    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce", format="mixed")
    rule = {"Diaria": "D", "Semanal": "W-MON", "Mensual": "MS"}[frequency]
    if not data.empty:
        data = (
            data.groupby(["neighborhood", pd.Grouper(key="datetime", freq=rule)])[
                list(METRICS.values())
            ].mean().reset_index().sort_values(["neighborhood", "datetime"])
        )
    data["name"] = data["neighborhood"].str.split(",").str[0]
    return data


def create_bar_graph(aggregates, selected_areas):
    data = aggregates.loc[
        aggregates["neighborhood"].isin(selected_areas or [])
    ].copy()
    data["neighborhood"] = data["neighborhood"].str.split(",").str[0]
    return data.melt(
        id_vars="neighborhood", value_vars=list(METRICS),
        var_name="variable", value_name="value",
    )


def period_label(year, month="all"):
    if year is None:
        return "Sin datos disponibles"
    if month in (None, "all"):
        return f"Todo el año {year}"
    return f"{MONTH_NAMES[int(month)]} de {year}"


def period_overview(samples, year, month="all"):
    """Count available records and dates, without implying continuous monitoring."""
    data = filter_period(samples, year, month)
    if year is None:
        expected = 0
    elif month in (None, "all"):
        expected = 366 if calendar.isleap(int(year)) else 365
    else:
        expected = calendar.monthrange(int(year), int(month))[1]
    return {
        "neighborhoods": int(data["neighborhood"].nunique()),
        "records": len(data),
        "days": int(data["datetime"].dt.normalize().nunique()),
        "calendar_days": expected,
        "start": data["datetime"].min() if not data.empty else None,
        "end": data["datetime"].max() if not data.empty else None,
    }
