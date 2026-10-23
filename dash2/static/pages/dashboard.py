import json
from pathlib import Path

import pandas as pd
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
import dash

from ..components.footer import footer_content
from .home import layout
from ...dash_figures import (
    VARIABLE_LABELS, empty_figure, get_figure, properties_figures,
    update_style_bar_figure, update_style_regression_figure,
)
from ...dash_logic import (
    aggregate_neighborhoods, available_years, create_bar_graph,
    create_time_series, filter_period, month_options, period_label, period_overview, valid_samples,
)
from ...maindash import app


DATA_DIR = Path(__file__).resolve().parents[2] / "datasets"
with (DATA_DIR / "bogota_cadastral.json").open(encoding="utf-8") as file:
    counties = json.load(file)
neighborhoods = {feature["properties"]["DISPLAY_NAME"] for feature in counties["features"]}
samples = valid_samples(pd.read_csv(DATA_DIR / "final_rutes.csv"), neighborhoods)
years = available_years(samples)
default_year = years[-1] if years else None


def add_loading_overlay(elements):
    return dmc.LoadingOverlay(
            children=elements,
            loaderProps={'color': '#DBD22A', 'variant': 'oval'},
            overlayColor='rgba(0,0,0,0)',
            overlayOpacity=1,
            radius=8,
        )

bogota_map_div = html.Div([
    dcc.Store(id="selected-neighborhoods", data=None),
    html.Div([
        html.Div([
            html.Label("Variable", htmlFor="variable_map"),
            dcc.Dropdown(
                id="variable_map",
                options={
                    "pm_25_mean": "PM2.5", "pm_10_mean": "PM10",
                    "temperature_mean": "Temperatura", "humidity_mean": "Humedad",
                },
                value="pm_25_mean", clearable=False,
            ),
        ], className="map-control"),
        html.Div([
            html.Label("Tema", htmlFor="map-basemap"),
            dcc.Dropdown(
                id="map-basemap",
                options=[
                    {"label": "Liberty", "value": "color"},
                    {"label": "Positron", "value": "light"},
                ],
                value="color", clearable=False, searchable=False,
                persistence=True, persistence_type="session",
            ),
        ], className="map-control"),
        html.Div([
            html.Label("Año", htmlFor="map-year"),
            dcc.Dropdown(
                id="map-year",
                options=[{"label": str(year), "value": year} for year in years],
                value=default_year, clearable=False, searchable=False,
                disabled=not years,
            ),
        ], className="map-control"),
        html.Div([
            html.Label("Mes", htmlFor="datetime"),
            dcc.Dropdown(
                id="datetime", options=month_options(samples, default_year),
                value="all", clearable=False, searchable=False,
            ),
        ], className="map-control"),
    ], className="map-controls"),
    html.Div(id="map-period-summary", className="map-period-summary", role="status"),
    dcc.Graph(
        id="bogota_map", className="airquality-map", responsive=True,
        config={"displaylogo": False, "scrollZoom": True},
    ),
    html.P([
        html.A("OpenFreeMap", href="https://openfreemap.org/", target="_blank", rel="noopener noreferrer"),
        " · ",
        html.A("© OpenMapTiles", href="https://www.openmaptiles.org/", target="_blank", rel="noopener noreferrer"),
        " · Datos de ",
        html.A("OpenStreetMap", href="https://www.openstreetmap.org/copyright", target="_blank", rel="noopener noreferrer"),
    ], className="map-attribution"),
], className="map-panel")


def overview_stat(label, value_id, detail, detail_id=None):
    detail_props = {"id": detail_id} if detail_id else {}
    return html.Article([
        html.P(label, className="overview-stat-label"),
        html.Strong("—", id=value_id, className="overview-stat-value"),
        html.P(detail, className="overview-stat-detail", **detail_props),
    ], className="overview-stat")


map_intro = html.Div([
    html.Div([
        overview_stat(
            "Barrios con registros", "overview-neighborhoods",
            f"De {len(neighborhoods):,} sectores del mapa".replace(",", "."),
        ),
        overview_stat(
            "Registros del periodo", "overview-records",
            "Según el año y el mes que elijas",
        ),
        overview_stat(
            "Días con registros", "overview-days",
            "Fechas disponibles", "overview-dates",
        ),
    ], className="overview-stats", role="group", **{"aria-label": "Resumen del periodo"}),
    html.Div([
        html.P([
            html.Strong("Cómo leer el mapa. "),
            "El color muestra el promedio por barrio de la variable seleccionada. "
            "Las zonas sin registros permanecen sin color.",
        ], className="overview-map-reading"),
        html.Details([
            html.Summary("Cómo explorar y comparar barrios"),
            html.Ol([
                html.Li([html.Strong("Elige qué observar"),
                         html.P("Consulta PM2.5, PM10, temperatura o humedad y cambia el fondo del mapa.")]),
                html.Li([html.Strong("Define el periodo"),
                         html.P("Filtra por año y mes. Todo el año resume los registros disponibles de ese año.")]),
                html.Li([html.Strong("Compara en el mapa"),
                         html.P("Acércate con el zoom y selecciona barrios para ver sus promedios y su evolución abajo.")]),
            ], className="overview-steps"),
        ], className="overview-help"),
    ], className="overview-guidance"),
    html.P([
        html.Span("Fuente en revisión", className="overview-source-tag"),
        "Los datos pertenecen al conjunto de trabajo actual; su fuente y validación están pendientes de confirmar.",
    ], className="overview-source-note"),
], className="map-intro overview-intro")

regression_map_div = html.Div([
        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                    id="frecuency",
                    options=["Diaria", "Semanal", "Mensual"],
                    value="Diaria",
                    clearable=False,
                    placeholder="Frecuencia",
                    style={'color': 'black'}
                ),width=3
            ),
            dbc.Col(
                dcc.Dropdown(
                    id="varible_regression",
                    options={
                        'pm_25': 'PM 2.5',
                        'pm_10': 'PM 10',
                        'temperature': 'Temperatura',
                        'humidity': 'Humedad'
                    },
                    value=['pm_25'],
                    style={'color': 'black'},
                    multi=True,
                    clearable=False
                ),width=9
            ),
        ],), #style={'marginBottom': '10px', "overflow-x": "hidden"}
        add_loading_overlay(dcc.Graph(id='regression')),
],style={})


bar_figure = html.Div([
    add_loading_overlay(dcc.Graph(id='bar_figure')),
],style={})


sidebar = html.Div(
    [
        dbc.Button("PM 1", id="btn_PM1", n_clicks=0, className="nav_link_info btn btn-primary btn-block"),
        dbc.Button("PM 2.5", id="btn_PM25", n_clicks=0, className="nav_link_info btn btn-primary btn-block"),
        dbc.Button("PM 10", id="btn_PM10", n_clicks=0, className="nav_link_info btn btn-primary btn-block"),
    ],
    className="nav_info_container"
)

content = html.Div(id="page-content", className="container_content")
 
dashboard = dbc.Container(
    [
        layout,
        html.Header([
            html.Div([
                html.P("EXPLORADOR AMBIENTAL · BOGOTÁ", className="overview-eyebrow"),
                html.H1("Calidad del aire, barrio a barrio", className="overview-title"),
                html.P(
                    "Explora PM2.5, PM10, temperatura y humedad. "
                    "Elige un periodo y descubre cómo cambian los registros entre barrios.",
                    className="overview-description",
                ),
            ], className="overview-copy"),
        ], className="dashboard-overview"),
        html.Section(
            [map_intro, bogota_map_div],
            className="map-explorer",
            **{"aria-label": "Explora la calidad del aire"},
        ),
        
        html.Div(["Aquí puedes examinar con detalle la información de las zonas seleccionadas en el mapa. ", 
                html.Span("Realiza comparaciones y obtén información precisa.", className="highlight"),
                " Las gráficas usan el mismo año y mes del mapa. Puedes agrupar la serie por día, semana o mes; cada variable indica su unidad."]
                , className="paragraph_separator"),
        
        dbc.Row(
            [
                dbc.Col(bar_figure),
                dbc.Col(regression_map_div),
            ],
            className="g-0 align-items-center",
            align="center",
        ), 
        html.Div(
            [
                html.Div([
                    html.H1("Una guia para tener en cuenta", className="title_section_2"),
                    html.H2("Informacion que te puede ser util", className="sub_title_section_2"),
                    ], className="titles_section_2"
                )
            ],
            className="my-4",  # Agrega clases de margen para espaciar los elementos
        ),
        
        dbc.Row(
            [
                dbc.Col(sidebar, width=3),
                dbc.Col(content),
            ],
            className="g-0 align-items-center",
            align="center",
        ), 
        
       footer_content
        
    ],
    fluid=True,
    className="airquality-dashboard",
)

@app.callback(
    [Output("datetime", "options"), Output("datetime", "value")],
    Input("map-year", "value"), State("datetime", "value"),
)
def update_month_options(year, current_month):
    options = month_options(samples, year)
    allowed = {option["value"] for option in options}
    return options, current_month if current_month in allowed else "all"


@app.callback(
    [Output("bogota_map", "figure"),
     Output("selected-neighborhoods", "data"),
     Output("map-period-summary", "children"),
     Output("overview-neighborhoods", "children"),
     Output("overview-records", "children"),
     Output("overview-days", "children"),
     Output("overview-dates", "children")],
    [Input("bogota_map", "clickData"), Input("variable_map", "value"),
     Input("map-year", "value"), Input("datetime", "value"),
     Input("map-basemap", "value")],
    State("selected-neighborhoods", "data"),
)
def update_map_on_click(click_data, variable, year, month, basemap, selected_areas):
    period = filter_period(samples, year, month)
    aggregates = aggregate_neighborhoods(period)
    if selected_areas is None:
        # Start with the best sampled sector, consistently across page loads.
        selected = period["neighborhood"].value_counts().head(1).index.tolist()
    else:
        selected = list(selected_areas)

    triggered = dash.callback_context.triggered
    is_map_click = bool(triggered and triggered[0]["prop_id"] == "bogota_map.clickData")
    if is_map_click and click_data:
        name = click_data["points"][0].get("location")
        if name in neighborhoods:
            if name in selected:
                selected.remove(name)
            else:
                selected.append(name)

    figure = get_figure(aggregates, variable, counties, selected, basemap)
    title = period_label(year, month)
    if period.empty:
        summary = f"{title} · Sin registros disponibles."
    else:
        start = period["datetime"].min().strftime("%d/%m/%Y")
        end = period["datetime"].max().strftime("%d/%m/%Y")
        count = f"{len(period):,}".replace(",", ".")
        summary = (
            f"{title} · {len(aggregates)} barrios · {count} registros. "
            f"Cobertura: {start} – {end}."
        )
    overview = period_overview(period, year, month)
    dates = (
        f"{overview['start']:%d/%m/%Y} – {overview['end']:%d/%m/%Y}"
        if overview["start"] is not None else "Sin fechas disponibles"
    )
    return (
        figure, selected, summary,
        f"{overview['neighborhoods']:,}".replace(",", "."),
        f"{overview['records']:,}".replace(",", "."),
        f"{overview['days']} / {overview['calendar_days']}",
        dates,
    )


@app.callback(
    [Output("regression", "figure"), Output("bar_figure", "figure")],
    [Input("selected-neighborhoods", "data"), Input("variable_map", "value"),
     Input("map-year", "value"), Input("datetime", "value"),
     Input("varible_regression", "value"), Input("frecuency", "value")],
)
def update_regression_figure(selected_areas, variable, year, month, variables, frequency):
    period = filter_period(samples, year, month)
    data = create_time_series(period, selected_areas, frequency)
    title = period_label(year, month)
    if data.empty:
        message = "Selecciona un barrio con datos para este periodo"
        return empty_figure(message), empty_figure(message)

    value = properties_figures[variable][2]
    fig = px.line(data, x="datetime", y=value, color="name", markers=True)
    if isinstance(variables, str):
        variables = [variables]
    for extra in variables or []:
        if extra != value:
            for name, group in data.groupby("name"):
                fig.add_trace(go.Scatter(
                    x=group["datetime"], y=group[extra], mode="lines+markers",
                    name=f"{name} · {extra}",
                ))

    bars = create_bar_graph(aggregate_neighborhoods(period), selected_areas)
    bars["variable"] = bars["variable"].map(VARIABLE_LABELS)
    bar = px.bar(bars, x="variable", y="value", color="neighborhood", text_auto=".2f")
    return (
        update_style_regression_figure(fig, variable, title),
        update_style_bar_figure(bar, title),
    )


@app.callback(
    Output("page-content", "children"),
    [Input("btn_PM1", "n_clicks"),
     Input("btn_PM25", "n_clicks"),
     Input("btn_PM10", "n_clicks")]
)
def update_output(btn_PM1, btn_PM25, btn_PM10):
    button_id = ""
    
    if len(dash.callback_context.triggered) > 0:
        button_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        
    message = html.Div([            
            html.H1("PM 1"),
            html.P(
                "Las partículas (PM) de tamaño inferior a 1 micra se denominan PM1 (a veces PM1.0). Las PM1 se consideran especialmente peligrosas debido a su tamaño extremadamente pequeño. Cuanto menor es el diámetro de una partícula, mayor es el daño que puede causar. Las partículas diminutas transportadas por el aire, como las PM1, son lo suficientemente pequeñas como para penetrar en el tejido pulmonar y llegar al torrente sanguíneo. Las PM1 pueden entonces circular por todo el cuerpo y causar efectos sistémicos sobre la salud.",
            )             
        ],className="des_message_card")                         
    if button_id == "btn_PM10":
        message = html.Div([
                html.H1("PM 10"),   
                html.P(
                    "Son aquellas partículas sólidas o líquidas de polvo, cenizas, hollín, partículas metálicas, cemento o polen, dispersas en la atmósfera, y cuyo diámetro varía entre 2,5 y 10 µm (1 micrómetro corresponde la milésima parte de 1 milímetro). Están formadas principalmente por compuestos inorgánicos como silicatos y aluminatos, metales pesados entre otros, y material orgánico asociado a partículas de carbono (hollín). Se caracterizan por poseer un pH básico debido a la combustión no controlada de materiales.",
                )
            ],className="des_message_card") 
    elif button_id == "btn_PM25":
        message = html.Div([
            html.H1("PM 2.5"),   
                html.P(
                "La materia particulada o PM (por sus siglas en inglés) 2.5, son partículas muy pequeñas en el aire que tiene un diámetro de 2.5 micrómetros (aproximadamente 1 diezmilésimo de pulgada) o menos de diámetro. Esto es menos que el grosor de un cabello humano. La materia particulada, uno de los seis  criterios de contaminantes del aire de la U.S. EPA, es una mezcla que puede incluir sustancias químicas orgánicas, polvo, hollín y metales. Estas partículas pueden provenir de los automóviles, camiones, fábricas, quema de madera y otras actividades.",
                )
            ],className="des_message_card") 
    return message

