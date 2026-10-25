"""Aplicación Dash para las figuras interactivas del panel React de predicciones."""
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs

from dash import dcc, html, Input, Output
from django_plotly_dash import DjangoDash

from .prediction_figures import empty, render


def asset(path):
    version = sha256((Path(__file__).parent / "static" / path).read_bytes()).hexdigest()[:12]
    return f"/static/{path}?v={version}"


app = DjangoDash("PredictionCharts", suppress_callback_exceptions=False,
    external_stylesheets=[asset("css/prediction_plotly.css"), asset("css/frame_cursor.css"), asset("css/frame_theme.css")],
    external_scripts=[asset("js/frame_theme.js"), asset("js/frame_cursor.js"), asset("js/prediction_plotly.js")])

app.layout = html.Div([
    dcc.Location(id="prediction-plot-location", refresh=False),
    html.Div([
        html.P("Elige cómo evaluar el modelo", className="plot-diagnostic-label"),
        dcc.RadioItems(id="prediction-diagnostic-type", value="parity", options=[
            {"label": "Real vs. estimado", "value": "parity"},
            {"label": "Distribución del error", "value": "residual"},
            {"label": "Comparar horizontes", "value": "horizon"},
            {"label": "Variación del error", "value": "box"},
        ], className="plot-diagnostic-tabs", inputClassName="plot-diagnostic-input", labelClassName="plot-diagnostic-option"),
    ], id="prediction-diagnostic-controls", style={"display": "none"}),
    dcc.Loading(dcc.Graph(id="prediction-plot-main", figure=empty("Cargando gráfico interactivo…"),
        responsive=True, style={"height": "430px", "width": "100%"}, config={"responsive": True, "displaylogo": False, "scrollZoom": False,
            "toImageButtonOptions": {"format": "png", "filename": "air_quality_bogota", "scale": 2},
            "modeBarButtonsToRemove": ["lasso2d", "select2d"]}), type="circle", color="#827b10"),
    html.P(id="prediction-plot-caption", className="plot-caption", **{"aria-live": "polite"}),
], id="prediction-plot-root")


@app.callback(Output("prediction-plot-main", "figure"), Output("prediction-plot-caption", "children"),
              Output("prediction-diagnostic-controls", "style"),
              Input("prediction-plot-location", "search"), Input("prediction-diagnostic-type", "value"))
def update_plot(search, kind):
    params = {key: values[-1] for key, values in parse_qs((search or "").lstrip("?")).items()}
    if not params.get("station"):
        return empty("Selecciona una consulta en Haz tus predicciones"), "Los gráficos se actualizan al aplicar los filtros.", {"display": "none"}
    try:
        figure, caption = render(params, kind)
        return figure, caption, {} if params.get("view") == "diagnostics" else {"display": "none"}
    except (ValueError, KeyError, IndexError, OSError):
        return empty("No hay datos válidos para esta consulta"), "Revisa los filtros o vuelve a aplicar la consulta.", {"display": "none"}
