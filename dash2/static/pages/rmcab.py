"""Panel de observaciones RMCAB; no ejecuta el notebook ni genera predicciones."""

from dash import Input, Output, State, dcc, html, no_update
from dash.exceptions import PreventUpdate

from ...maindash import app
from ...rmcab_data import (DATA_PATH, FREQUENCIES, STATISTICS, VARIABLES, export_records,
    filter_period, load_samples, month_options, overview, period_title, station_options,
    station_summary, year_options)
from ...rmcab_figures import figures


from ...history_data import load_observations

samples = load_observations()
initial_years = year_options(samples, "pm_25")
initial_year = initial_years[-1]["value"] if initial_years else None


def control(label, component, class_name=""):
    return html.Div([html.Label(label, htmlFor=component.id), component], className=f"rmcab-control {class_name}")


def stat(label, value_id, detail_id):
    return html.Article([html.P(label), html.Strong("—", id=value_id), html.Small(id=detail_id)], className="rmcab-stat")


panel = html.Section([
    html.Div([
        html.Div([html.P("MEDICIONES POR ESTACIÓN", className="overview-eyebrow"),
                  html.H2("Históricos RMCAB", className="rmcab-heading"),
                  html.P("Compara partículas y clima con registros publicados por la Red de Monitoreo de Calidad del Aire de Bogotá.")]),
        html.Span("Histórico publicado", className="overview-source-tag"),
    ], className="rmcab-intro"),
    html.P([
        f"Esta colección reúne {samples.report_date.nunique()} reportes de {samples.report_date.dt.year.min()}–{samples.report_date.dt.year.max()}. ",
        "PM2.5 y PM10 incorporan las exportaciones horarias de SISAIRE/SDA. Los huecos de sensores se conservan. ",
        html.A("Fuente: RMCAB / SDA", href="https://rmcab.ambientebogota.gov.co/home/text/1516", target="_blank", rel="noopener noreferrer"),
        ". Validación final de las mediciones pendiente de comprobar.",
    ], className="rmcab-source-note"),
    html.Div([
        control("Variable", dcc.Dropdown(id="rmcab-variable", options=[{"label": f"{label} ({unit})", "value": value} for value, (label, unit) in VARIABLES.items()], value="pm_25", clearable=False, searchable=False)),
        control("Año", dcc.Dropdown(id="rmcab-year", options=initial_years, value=initial_year, clearable=False, searchable=False)),
        control("Mes del reporte", dcc.Dropdown(id="rmcab-month", options=month_options(samples, initial_year, "pm_25"), value="all", clearable=False, searchable=False)),
        control("Agrupar serie", dcc.Dropdown(id="rmcab-frequency", options=[{"label": label, "value": value} for value, (label, _) in FREQUENCIES.items()], value="hour", clearable=False, searchable=False)),
        control("Estaciones para comparar", dcc.Dropdown(id="rmcab-stations", options=[], value=None, multi=True, placeholder="Busca y selecciona estaciones"), "rmcab-station-control"),
        control("Estadística", dcc.Dropdown(id="rmcab-statistic", options=[{"label": label, "value": value} for value, label in STATISTICS.items()], value="mean", clearable=False, searchable=False)),
    ], className="rmcab-controls"),
    html.P(id="rmcab-summary", className="rmcab-period-summary", role="status"),
    html.Div([
        stat("Estaciones con mediciones", "rmcab-station-count", "rmcab-station-detail"),
        stat("Mediciones de la variable", "rmcab-record-count", "rmcab-record-detail"),
        stat("Días consultados / periodo", "rmcab-day-count", "rmcab-day-detail"),
        stat("Datos presentes en los reportes", "rmcab-presence", "rmcab-presence-detail"),
    ], className="rmcab-stats"),
    html.Div([
        html.Div([html.H3("Evolución por estación"), html.P("Los huecos quedan visibles. Cada punto resume únicamente mediciones disponibles."),
                  dcc.Graph(id="rmcab-series", responsive=True, config={"displaylogo": False})], className="rmcab-chart-card"),
        html.Div([html.H3("Comparación del periodo"), html.P("La misma variable y unidad para todas las estaciones seleccionadas."),
                  dcc.Graph(id="rmcab-comparison", responsive=True, config={"displaylogo": False})], className="rmcab-chart-card"),
    ], className="rmcab-charts"),
    html.Section([
        html.Div([html.Div([html.H3("Detalle y disponibilidad"), html.P("Mediciones presentes sobre horas de estación publicadas, para la variable elegida.")]),
                  html.Button("Descargar registros CSV ↓", id="rmcab-export", n_clicks=0, type="button", className="rmcab-export-button")], className="rmcab-detail-heading"),
        html.Div(id="rmcab-table", className="rmcab-table-scroll", role="region", tabIndex=0, **{"aria-label": "Disponibilidad por estación; desplazable horizontalmente"}),
        html.P("El CSV contiene las cuatro variables, unidades, valores originales, marcas de tratamiento y fuente de cada registro. No se rellenan ausencias ni se incluyen predicciones.", className="rmcab-export-note"),
        dcc.Download(id="rmcab-download"),
    ], className="rmcab-detail-card"),
    html.Details([
        html.Summary("Cómo interpretar esta muestra"),
        html.Ul([
            html.Li("Una estación es un punto de medición. Sus valores no son promedios de un barrio; el mapa por barrios sigue disponible en su pestaña."),
            html.Li("El año y el mes se filtran por fecha del reporte. Su hora 24 se muestra como 00:00 del día siguiente, en hora de Bogotá."),
            html.Li("Datos presentes indica cuántos valores hay en los reportes consultados. No mide la cobertura de todo el año ni certifica la calidad del sensor."),
            html.Li("No se combinan humedad ambiental con humedad interna del equipo ni canales de distinta altura. Un valor ausente permanece sin dato."),
        ]),
    ], className="rmcab-help"),
], className="rmcab-panel", **{"aria-label": "Históricos por estación de la RMCAB"})


@app.callback([Output("rmcab-year", "options"), Output("rmcab-year", "value")],
              Input("rmcab-variable", "value"), State("rmcab-year", "value"))
def update_years(variable, current):
    options = year_options(samples, variable)
    allowed = [option["value"] for option in options]
    return options, current if current in allowed else (allowed[-1] if allowed else None)


@app.callback([Output("rmcab-month", "options"), Output("rmcab-month", "value")],
              [Input("rmcab-year", "value"), Input("rmcab-variable", "value")], State("rmcab-month", "value"))
def update_months(year, variable, current):
    options = month_options(samples, year, variable)
    return options, current if current in {option["value"] for option in options} else "all"


@app.callback([Output("rmcab-stations", "options"), Output("rmcab-stations", "value")],
              [Input("rmcab-year", "value"), Input("rmcab-month", "value"), Input("rmcab-variable", "value")],
              State("rmcab-stations", "value"))
def update_stations(year, month, variable, selected):
    options = station_options(filter_period(samples, year, month), variable)
    allowed = {option["value"] for option in options}
    if selected == []:
        return options, []
    preserved = [str(station) for station in selected or [] if str(station) in allowed]
    return options, preserved or [option["value"] for option in options[:3]]


@app.callback(
    [Output("rmcab-summary", "children"), Output("rmcab-station-count", "children"),
     Output("rmcab-station-detail", "children"), Output("rmcab-record-count", "children"),
     Output("rmcab-record-detail", "children"), Output("rmcab-day-count", "children"),
     Output("rmcab-day-detail", "children"), Output("rmcab-presence", "children"),
     Output("rmcab-presence-detail", "children"), Output("rmcab-series", "figure"),
     Output("rmcab-comparison", "figure"), Output("rmcab-table", "children"),
     Output("rmcab-export", "disabled")],
    [Input("rmcab-year", "value"), Input("rmcab-month", "value"), Input("rmcab-variable", "value"),
     Input("rmcab-stations", "value"), Input("rmcab-frequency", "value"), Input("rmcab-statistic", "value")],
)
def update_results(year, month, variable, stations, frequency, statistic):
    period = filter_period(samples, year, month, stations or [])
    info = overview(period, variable, year, month)
    label, unit = VARIABLES[variable]
    dates = f"{info['start']:%d/%m/%Y} – {info['end']:%d/%m/%Y}" if info["start"] is not None else "Sin fechas seleccionadas"
    title = period_title(year, month)
    summary = f"{title} · {label} ({unit}) · {STATISTICS[statistic].lower()} · Fechas de reporte: {dates}."
    if not stations:
        summary += " Selecciona estaciones para comenzar."
    series, bars = figures(period, variable, frequency, statistic)
    details = station_summary(period, variable, statistic)
    header = html.Thead(html.Tr([html.Th("Estación", scope="col"), html.Th(f"{STATISTICS[statistic]} ({unit})", scope="col"), html.Th("Mediciones", scope="col"), html.Th("Horas publicadas", scope="col"), html.Th("Datos presentes", scope="col")]))
    rows = [html.Tr([html.Th(row.station_label, scope="row"), html.Td(f"{row.value:.2f}" if row.observations else "Sin dato"), html.Td(str(row.observations)), html.Td(str(row.slots)), html.Td(f"{row.presence_pct:.1f} %")]) for row in details.itertuples()]
    if not rows:
        rows = [html.Tr(html.Td("Selecciona una estación con datos para este periodo.", colSpan=5))]
    table = html.Table([html.Caption(f"Disponibilidad de {label}: estaciones seleccionadas"), header, html.Tbody(rows)])
    return (summary, str(info["stations"]), f"De {len(stations or [])} seleccionadas",
            f"{info['observations']:,}".replace(",", "."), f"{label} · {unit}",
            f"{info['report_days']} / {info['calendar_days']}", "Días consultados frente a días calendario",
            f"{info['presence_pct']:.1f} %", f"{info['observations']} de {info['slots']} horas publicadas",
            series, bars, table, not bool(info["observations"]))


@app.callback(Output("rmcab-download", "data"), Input("rmcab-export", "n_clicks"),
              [State("rmcab-year", "value"), State("rmcab-month", "value"), State("rmcab-stations", "value")],
              prevent_initial_call=True)
def download_records(clicks, year, month, stations):
    if not clicks:
        raise PreventUpdate
    period = filter_period(samples, year, month, stations or [])
    if period.empty:
        return no_update
    return dcc.send_data_frame(export_records(period).to_csv, f"rmcab_historico_{year}_{month}.csv", index=False)
