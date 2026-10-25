"""Independent figures; no shared mutable map or selection state."""

import plotly.graph_objs as go


BASEMAPS = {
    "auto": "https://tiles.openfreemap.org/styles/liberty",
    "dark": "https://tiles.openfreemap.org/styles/dark",
    "color": "https://tiles.openfreemap.org/styles/liberty",
    "light": "https://tiles.openfreemap.org/styles/positron",
}
properties_figures = {
    "pm_25_mean": ["PM2.5 · µg/m³", "Viridis", "pm_25", "PM2.5 por barrio"],
    "pm_10_mean": ["PM10 · µg/m³", "Cividis", "pm_10", "PM10 por barrio"],
    "temperature_mean": ["Temperatura · °C", "Jet", "temperature", "Temperatura por barrio"],
    "humidity_mean": ["Humedad relativa · %", "ice", "humidity", "Humedad por barrio"],
}
VARIABLE_LABELS = {
    "pm_25_mean": "PM2.5 (µg/m³)", "pm_10_mean": "PM10 (µg/m³)",
    "temperature_mean": "Temperatura (°C)", "humidity_mean": "Humedad (%)",
}


def empty_figure(message):
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font=dict(size=15, color="#53534a"),
    )
    fig.update_layout(xaxis_visible=False, yaxis_visible=False)
    return _chart_style(fig)


def get_figure(data, variable, counties, selected_areas=None, basemap="color"):
    label, scale, _, _ = properties_figures[variable]
    selected = set(selected_areas or [])
    # Locations, values and outlines must use the SAME filtered rows and order.
    fig = go.Figure(go.Choroplethmapbox(
        geojson=counties,
        locations=data["neighborhood"].tolist(),
        featureidkey="properties.DISPLAY_NAME",
        z=data[variable].tolist(),
        colorscale=scale,
        colorbar=dict(title=label, thickness=15, len=0.86),
        marker_opacity=[1 if name in selected else 0.72 for name in data["neighborhood"]],
        marker_line_width=[2.5 if name in selected else 0.5 for name in data["neighborhood"]],
        marker_line_color=["#bc3838" if name in selected else "#454453" for name in data["neighborhood"]],
        customdata=data["neighborhood"].str.split(",").str[0].tolist(),
        hovertemplate="%{customdata}<br>%{z:.2f} " + label + "<extra></extra>",
    ))
    fig.update_layout(
        mapbox=dict(
            style=BASEMAPS.get(basemap, BASEMAPS["color"]),
            zoom=9.5, pitch=0, center=dict(lat=4.67071, lon=-74.08175),
        ),
        meta={"airqualityAutoBasemap": basemap == "auto"},
        uirevision="bogota-map-view",
        autosize=True, height=510,
        margin=dict(r=0, t=8, l=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2d2d2d", family="OSWALD-LIGHT, sans-serif"),
    )
    if data.empty:
        fig.add_annotation(
            text="No hay datos para este periodo", x=0.5, y=0.5,
            xref="paper", yref="paper", showarrow=False, bgcolor="white",
        )
    return fig


def _chart_style(fig):
    fig.update_layout(
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2d2d2d", family="OSWALD-LIGHT, sans-serif"),
        xaxis_gridcolor="#d8d8d8", yaxis_gridcolor="#d8d8d8",
    )
    return fig


def update_style_regression_figure(fig, variable_map, period=""):
    fig.update_layout(
        title=f"{properties_figures[variable_map][3]} · {period}",
        xaxis_title="Fecha", yaxis_title=properties_figures[variable_map][0],
        legend_title="Barrios / variables",
    )
    return _chart_style(fig)


def update_style_bar_figure(fig, period=""):
    fig.update_layout(
        title=f"Promedios del periodo · {period}",
        xaxis_title="Variable y unidad", yaxis_title="Promedio", legend_title="Barrios",
        barmode="group",
    )
    return _chart_style(fig)
