"""Gráficas de una variable y su unidad; los huecos nunca se convierten en cero."""

import plotly.graph_objs as go

from .dash_figures import empty_figure
from .rmcab_data import STATISTICS, VARIABLES, station_summary, time_series


COLORS = ["#827b10", "#4d7c89", "#9b6481", "#48644b", "#b06a36", "#686ca2"]


def _style(figure, variable, height):
    label, unit = VARIABLES[variable]
    figure.update_layout(
        autosize=True, height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="OSWALD-LIGHT, sans-serif", color="#2d2d2d", size=13),
        margin=dict(l=60, r=20, t=16, b=90),
        yaxis=dict(title=f"{label} ({unit})", gridcolor="#deded5", zerolinecolor="#deded5"),
        xaxis=dict(gridcolor="#e6e6df"),
        legend=dict(title=None, orientation="h", y=-0.25, x=0, font=dict(size=12)),
    )
    return figure


def figures(period, variable, frequency="hour", statistic="mean"):
    if period.empty or period[variable].notna().sum() == 0:
        return empty_figure("Selecciona estaciones con mediciones para este periodo"), empty_figure("Sin mediciones para comparar")
    series = time_series(period, variable, frequency, statistic)
    line = go.Figure()
    label, unit = VARIABLES[variable]
    for index, (_, group) in enumerate(series.groupby("station_id", sort=True)):
        line.add_trace(go.Scatter(
            # Ejes en hora local explícita, independientemente de la zona del navegador.
            x=group.datetime.dt.tz_localize(None), y=group.value,
            customdata=group.observations, name=group.station_label.iloc[0],
            mode="lines+markers", connectgaps=False,
            line=dict(color=COLORS[index % len(COLORS)], width=2), marker=dict(size=4),
            hovertemplate="%{x|%d/%m/%Y %H:%M}<br>%{y:.2f} " + unit + "<br>%{customdata} mediciones<extra>%{fullData.name}</extra>",
        ))
    line.update_layout(hovermode="x unified", xaxis_title="Hora de Bogotá (UTC−5)")
    line = _style(line, variable, 440)

    summary = station_summary(period, variable, statistic)
    summary = summary.loc[summary.observations.gt(0)].sort_values("value")
    bars = go.Figure(go.Bar(
        x=summary.value, y=summary.station_label, orientation="h",
        customdata=summary.observations, marker_color="#827b10",
        hovertemplate="%{y}<br>" + STATISTICS[statistic] + ": %{x:.2f} " + unit + "<br>%{customdata} mediciones<extra></extra>",
    ))
    bars = _style(bars, variable, 350)
    bars.update_layout(xaxis_title=f"{label} ({unit})", yaxis_title=None,
                       yaxis_automargin=True, showlegend=False,
                       margin=dict(l=12, r=20, t=16, b=55))
    return line, bars
