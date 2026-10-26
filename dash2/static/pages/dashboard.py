import json
from pathlib import Path

import pandas as pd
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, State, no_update
import plotly.express as px
import plotly.graph_objs as go
import dash

from ..components.footer import footer_content
from .home import layout
from .rmcab import panel as rmcab_panel
from ...dash_figures import (
    VARIABLE_LABELS, empty_figure, get_figure, properties_figures,
    update_style_bar_figure, update_style_regression_figure,
)
from ...dash_logic import (
    MONTH_NAMES, aggregate_neighborhoods, available_years, create_bar_graph,
    create_time_series, filter_period, month_options, period_label, period_overview, valid_samples,
)
from ...maindash import app
from ... import neighborhood_data as history
from ...rmcab_data import VARIABLES


DATA_DIR = Path(__file__).resolve().parents[2] / "datasets"
with (DATA_DIR / "bogota_cadastral.json").open(encoding="utf-8") as file:
    counties = json.load(file)
neighborhoods = {feature["properties"]["DISPLAY_NAME"] for feature in counties["features"]}
DEFAULT_NEIGHBORHOODS = (
    "EL MADRIGAL, 005635 (299)",
    "LAS DELICIAS, 004544 (502)",
    "POLO CLUB, 007401 (813)",
)
samples = valid_samples(pd.read_csv(DATA_DIR / "final_rutes.csv"), neighborhoods)
years = list(range(2015, 2026))
default_year = 2025


def add_loading_overlay(elements):
    return dmc.LoadingOverlay(
            children=elements,
            loaderProps={'color': '#DBD22A', 'variant': 'oval'},
            overlayColor='rgba(0,0,0,0)',
            overlayOpacity=1,
            radius=8,
        )

bogota_map_div = html.Div([
    dcc.Store(id="selected-neighborhoods", data=list(DEFAULT_NEIGHBORHOODS)),
    dcc.Store(id="map-geometry-ready", data=None),
    html.Div([
        html.Label("Datos del mapa", htmlFor="map-data-mode"),
        dcc.Dropdown(id="map-data-mode", options=[{"label": label, "value": value} for value, label in history.MODES.items()],
                     value="estimated", clearable=False, searchable=False),
        html.P(id="map-source-note", className="map-history-note", role="status"),
    ], className="map-history-source"),
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
                    {"label": "Automático · tema del sitio", "value": "auto"},
                    {"label": "Liberty", "value": "color"},
                    {"label": "Positron", "value": "light"},
                    {"label": "Dark", "value": "dark"},
                ],
                value="auto", clearable=False, searchable=False,
                persistence="site-theme-v1", persistence_type="session",
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
                id="datetime", options=[{"label": "Todo el año", "value": "all"}]+[{"label": name, "value": number} for number, name in MONTH_NAMES.items()],
                value="all", clearable=False, searchable=False,
            ),
        ], className="map-control"),
    ], className="map-controls"),
    html.Div([
        html.Button("Descargar promedios por sector CSV ↓", id="map-export", n_clicks=0, type="button", className="rmcab-export-button"),
        html.A("Calendario por estación CSV.gz ↓", href="/api/maps/calendar/", className="rmcab-export-button"),
        html.A("Procedimiento notebook ↓", href="/api/maps/methodology/", className="rmcab-export-button"),
        dcc.Download(id="map-download"),
    ], className="map-history-download"),
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
            "Sectores con valor", "overview-neighborhoods",
            f"De {len(neighborhoods):,} sectores del mapa".replace(",", "."),
        ),
        overview_stat(
            "Mediciones de origen", "overview-records",
            "Según el año y el mes que elijas",
        ),
        overview_stat(
            "Días con fuentes / calendario", "overview-days",
            "Fechas disponibles", "overview-dates",
        ),
    ], className="overview-stats", role="group", **{"aria-label": "Resumen del periodo"}),
    html.Div([
        html.P([
            html.Strong("Cómo leer el mapa. "),
            "El color muestra el promedio temporal estimado en el centro de cada sector. "
            "La escala de color de cada variable se mantiene entre años. Los límites se conservan; las zonas sin valor aparecen en gris.",
        ], className="overview-map-reading"),
        html.Details([
            html.Summary("Cómo explorar y comparar barrios"),
            html.Ol([
                html.Li([html.Strong("Elige qué observar"),
                         html.P("Consulta PM2.5, PM10, temperatura o humedad y cambia el fondo del mapa.")]),
                html.Li([html.Strong("Define el periodo"),
                         html.P("Elige un año de 2015 a 2025 y un mes. Datos originales muestra las fechas disponibles; Datos con tratamiento completa el calendario y permite analizar la serie continua.")]),
                html.Li([html.Strong("Compara en el mapa"),
                         html.P("Acércate con el zoom y selecciona barrios para ver sus promedios y su evolución abajo.")]),
            ], className="overview-steps"),
        ], className="overview-help"),
    ], className="overview-guidance"),
    html.Details([
        html.Summary("Cómo se completaron los datos del mapa"),
        html.P("Datos originales usa las mediciones RMCAB disponibles, promediadas por estación y día. Datos con tratamiento conserva esas mediciones y completa los huecos para mostrar series de 2015–2025."),
        html.P("El tratamiento interpola primero los huecos cortos y usa KNN sin día de la semana para el resto. Los rellenos largos incluyen variación sintética suave por sector, con semilla fija y amplitud del 10 % del rango P5–P95 observado. Es una elección de tratamiento exploratorio, no incertidumbre calibrada. Las mediciones originales se conservan."),
        html.P("IDW combina las cuatro estaciones disponibles más cercanas en el centroide de cada sector. Son estimaciones espaciales, no mediciones del barrio ni promedios del área completa. Las zonas a más de 10 km de una estación requieren especial cautela."),
        html.P("La mayoría de años anteriores a 2025 tiene un solo día de fuente. Completar el calendario no recupera mediciones perdidas ni valida la estacionalidad anual. El tratamiento retrospectivo usa datos anteriores y posteriores; no alimenta el modelo HGB de pronósticos. Cada sector tiene una curva continua en Datos con tratamiento; al pasar el cursor se identifican las fechas de origen y los rellenos."),
        html.P("Se usan ubicaciones de referencia de estaciones; no se han verificado sus traslados históricos. La validación final de las mediciones publicadas sigue pendiente."),
        html.A("Ver procedimiento y comprobaciones en el notebook ↗", href="/api/maps/methodology/", target="_blank", rel="noopener noreferrer"),
    ], className="overview-help map-history-help"),
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
        add_loading_overlay(dcc.Graph(id='regression', responsive=True, style={'width':'100%', 'height':'450px'}, config={'responsive':True, 'displaylogo':False})),
],style={})


bar_figure = html.Div([
    add_loading_overlay(dcc.Graph(id='bar_figure', responsive=True, style={'width':'100%', 'height':'450px'}, config={'responsive':True, 'displaylogo':False})),
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
                html.H1("Explora la calidad del aire de Bogotá", className="overview-title"),
                html.P(
                    "Explora PM2.5, PM10, temperatura y humedad. "
                    "Explora 2015–2025 por sectores y compara los datos originales con los datos con tratamiento y huecos rellenados.",
                    className="overview-description",
                ),
            ], className="overview-copy"),
        ], className="dashboard-overview"),
        dcc.Tabs(
            id="dashboard-source", value="legacy",
            className="dashboard-source-tabs",
            children=[
                dcc.Tab(label="Mapa por sectores · 2015–2025", value="legacy",
                        className="dashboard-source-tab", selected_className="dashboard-source-tab--selected",
                        children=[
        html.Section(
            [map_intro, bogota_map_div],
            className="map-explorer",
            **{"aria-label": "Explora la calidad del aire"},
        ),
        
        html.Div(["Aquí puedes examinar con detalle la información de las zonas seleccionadas en el mapa. ", 
                html.Span("Compara sectores y revisa la cobertura de las fuentes.", className="highlight"),
                " Las gráficas usan el mismo año, mes y modo del mapa. Los promedios se calculan sobre los días representados. Cada variable tiene su propia unidad y panel."]
                , className="paragraph_separator"),
        
        dbc.Row(
            [
                dbc.Col(bar_figure),
                dbc.Col(regression_map_div),
            ],
            className="g-0 align-items-center",
            align="center",
        )
                        ]),
                dcc.Tab(label="Históricos RMCAB · estaciones", value="rmcab",
                        className="dashboard-source-tab", selected_className="dashboard-source-tab--selected",
                        children=rmcab_panel),
            ],
        ),
        html.Section([
            html.Header([
                html.P("ENTIENDE LO QUE OBSERVAS", className="overview-eyebrow"),
                html.H2("Una guía para leer las partículas", className="guide-title"),
                html.P("Selecciona una categoría para conocer qué representa su tamaño.",
                       className="guide-description"),
            ], className="guide-heading"),
            dbc.Row([
                dbc.Col(sidebar, width=3),
                dbc.Col(content),
            ], className="g-0 variables-guide-row", align="start"),
        ], className="variables-guide", **{"aria-label": "Guía de partículas"}),
        
       footer_content
        
    ],
    fluid=True,
    className="airquality-dashboard",
)

@app.callback([Output("map-year", "options"), Output("map-year", "value")],
              Input("map-data-mode", "value"), State("map-year", "value"))
def update_map_years(mode, current):
    options = available_years(samples) if mode == "legacy" else list(range(2015, 2026))
    return [{"label": str(year), "value": year} for year in options], no_update if current in options else options[-1]


@app.callback([Output("datetime", "options"), Output("datetime", "value")],
              [Input("map-year", "value"), Input("map-data-mode", "value")], State("datetime", "value"))
def update_month_options(year, mode, current_month):
    options = month_options(samples, year) if mode == "legacy" else [{"label": "Todo el año", "value": "all"}]+[{"label": label, "value": value} for value, label in MONTH_NAMES.items()]
    return options, no_update if current_month in {item["value"] for item in options} else "all"


@app.callback(
    [Output("bogota_map", "figure"), Output("selected-neighborhoods", "data"),
     Output("map-period-summary", "children"), Output("overview-neighborhoods", "children"),
     Output("overview-records", "children"), Output("overview-days", "children"),
     Output("overview-dates", "children"), Output("map-source-note", "children"), Output("map-geometry-ready", "data")],
    [Input("bogota_map", "clickData"), Input("variable_map", "value"), Input("map-year", "value"),
     Input("datetime", "value"), Input("map-basemap", "value"), Input("map-data-mode", "value")],
    [State("selected-neighborhoods", "data"), State("map-geometry-ready", "data")])
def update_map_on_click(click_data, variable, year, month, basemap, mode, selected_areas, geometry_ready):
    if mode == "legacy":
        period = filter_period(samples, year, month)
        aggregates = aggregate_neighborhoods(period)
    else:
        if year not in range(2015, 2026): year = 2025
        aggregates, info = history.aggregates(year, month, mode)
    selected = list(DEFAULT_NEIGHBORHOODS) if selected_areas is None else list(selected_areas)
    triggered = dash.callback_context.triggered
    if triggered and triggered[0]["prop_id"] == "bogota_map.clickData" and click_data:
        name = click_data["points"][0].get("location")
        if name in neighborhoods:
            selected.remove(name) if name in selected else selected.append(name)
    if mode == "legacy":
        figure = history.map_figure(aggregates, variable, counties, selected, basemap, 'legacy')
        if geometry_ready and geometry_ready.get('loaded'):
            figure = history.figure_update(figure)
        overview = period_overview(period, year, month)
        summary = f"{period_label(year, month)} · {len(aggregates)} sectores · {len(period):,} registros originales."
        dates = f"{overview['start']:%d/%m/%Y} – {overview['end']:%d/%m/%Y}" if overview['start'] is not None else "Sin fechas disponibles"
        return figure, selected, summary, str(overview['neighborhoods']), f"{overview['records']:,}", f"{overview['days']} / {overview['calendar_days']}", dates, "Recorridos originales de 2024. Fuente y unidades del conjunto de trabajo pendientes de confirmar.", {"loaded": True}
    metric = properties_figures[variable][2]
    counts = info[metric]
    figure = history.map_figure(aggregates, variable, counties, selected, basemap, mode)
    if geometry_ready and geometry_ready.get('loaded'):
        figure = history.figure_update(figure)
    title = period_label(year, month)
    summary = (f"{title} · {len(aggregates):,} sectores conservados · {counts['represented_days']} días representados · "
               f"{counts['source_days']} días con mediciones de origen · {counts['days_added']} días rellenados.")
    if mode in {"estimated", "simulated"}:
        note = ("Datos con tratamiento · calendario completo con huecos rellenados. "
                "Conserva las mediciones; completa clima con reanálisis ERA5 y PM sin cobertura con estimaciones identificadas. ")
    else:
        note = "Datos originales SDA/RMCAB y SISAIRE · solo mediciones disponibles, sin relleno temporal. El mapa estima valores por sector a partir de estaciones."
    source_dates = f"Fuentes: {counts['source_start']} – {counts['source_end']}" if counts['source_start'] else "Sin días de origen para esta variable"
    return (figure, selected, summary, f"{aggregates[variable].notna().sum():,}", f"{counts['observed_hours']:,}",
            f"{counts['source_days']} / {info['calendar_days']}", source_dates, note, {"loaded": True})


def chart_result(line, bars):
    return line, bars, {"width":"100%", "height":f"{line.layout.height or 450}px"}, {"width":"100%", "height":f"{bars.layout.height or 450}px"}


@app.callback([Output("regression", "figure"), Output("bar_figure", "figure"), Output("regression", "style"), Output("bar_figure", "style")],
    [Input("selected-neighborhoods", "data"), Input("variable_map", "value"), Input("map-year", "value"),
     Input("datetime", "value"), Input("varible_regression", "value"), Input("frecuency", "value"), Input("map-data-mode", "value")])
def update_regression_figure(selected_areas, variable, year, month, variables, frequency, mode, variation=10):
    if mode != "legacy":
        if year not in range(2015, 2026): year = 2025
        return chart_result(*history.charts(year, month, mode, selected_areas, variable, variables, frequency, variation))
    period = filter_period(samples, year, month)
    data = create_time_series(period, selected_areas, frequency)
    if data.empty: return chart_result(empty_figure("Selecciona un sector con datos"), empty_figure("Selecciona un sector con datos"))
    value = properties_figures[variable][2]
    fig = px.line(data, x="datetime", y=value, color="name", markers=True)
    if isinstance(variables, str): variables = [variables]
    for extra in variables or []:
        if extra in VARIABLES and extra != value:
            for name, group in data.groupby("name"):
                fig.add_trace(go.Scatter(x=group.datetime, y=group[extra], mode="lines+markers", name=f"{name} · {extra}"))
    bars = create_bar_graph(aggregate_neighborhoods(period), selected_areas)
    bars["variable"] = bars["variable"].map(VARIABLE_LABELS)
    bar = px.bar(bars, x="variable", y="value", color="neighborhood", text_auto=".2f")
    return chart_result(update_style_regression_figure(fig, variable, period_label(year, month)), update_style_bar_figure(bar, period_label(year, month)))


@app.callback(Output("map-download", "data"), Input("map-export", "n_clicks"),
              [State("map-year", "value"), State("datetime", "value"), State("map-data-mode", "value")], prevent_initial_call=True)
def download_map(n_clicks, year, month, mode, variation=10):
    if mode == "legacy":
        frame = aggregate_neighborhoods(filter_period(samples, year, month))
    else:
        frame = history.export_aggregates(year, month, mode, variation)
    suffix = f"_v{history.variation_rate(variation):g}_seed{history.SIMULATION_SEED}" if mode in {"estimated", "simulated"} else ""
    return dcc.send_data_frame(frame.to_csv, f"sectores_{year}_{month}_{mode}{suffix}.csv", index=False, encoding="utf-8-sig")


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
            html.H3("PM 1"),
            html.P(
                "Las partículas (PM) de tamaño inferior a 1 micra se denominan PM1 (a veces PM1.0). Las PM1 se consideran especialmente peligrosas debido a su tamaño extremadamente pequeño. Cuanto menor es el diámetro de una partícula, mayor es el daño que puede causar. Las partículas diminutas transportadas por el aire, como las PM1, son lo suficientemente pequeñas como para penetrar en el tejido pulmonar y llegar al torrente sanguíneo. Las PM1 pueden entonces circular por todo el cuerpo y causar efectos sistémicos sobre la salud.",
            )             
        ],className="des_message_card")                         
    if button_id == "btn_PM10":
        message = html.Div([
                html.H3("PM 10"),
                html.P(
                    "Son aquellas partículas sólidas o líquidas de polvo, cenizas, hollín, partículas metálicas, cemento o polen, dispersas en la atmósfera, y cuyo diámetro varía entre 2,5 y 10 µm (1 micrómetro corresponde la milésima parte de 1 milímetro). Están formadas principalmente por compuestos inorgánicos como silicatos y aluminatos, metales pesados entre otros, y material orgánico asociado a partículas de carbono (hollín). Se caracterizan por poseer un pH básico debido a la combustión no controlada de materiales.",
                )
            ],className="des_message_card") 
    elif button_id == "btn_PM25":
        message = html.Div([
            html.H3("PM 2.5"),
                html.P(
                "La materia particulada o PM (por sus siglas en inglés) 2.5, son partículas muy pequeñas en el aire que tiene un diámetro de 2.5 micrómetros (aproximadamente 1 diezmilésimo de pulgada) o menos de diámetro. Esto es menos que el grosor de un cabello humano. La materia particulada, uno de los seis  criterios de contaminantes del aire de la U.S. EPA, es una mezcla que puede incluir sustancias químicas orgánicas, polvo, hollín y metales. Estas partículas pueden provenir de los automóviles, camiones, fábricas, quema de madera y otras actividades.",
                )
            ],className="des_message_card") 
    return message
