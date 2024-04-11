import pandas as pd
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, Input, Output
import plotly.express as px

#Clases y componentes
from ..components.switch import switch
from ..components.footer import footer_content

from ...dash_figures import *
from ...dash_logic import *
from ...maindash import app


geo_fig = update_figure(geo_fig_general)


def add_loading_overlay(elements):
    return dmc.LoadingOverlay(
            children=elements,
            loaderProps={'color': '#DBD22A', 'variant': 'oval'},
            overlayColor='rgba(0,0,0,0)',
            overlayOpacity=1,
            radius=8,
        )

bogota_map_div = html.Div([
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id="variable_map",
                options={
                        'pm_25_mean': 'PM 2.5',
                        'pm_10_mean': 'PM 10',
                        'temperature_mean': 'Temperatura',
                        'humidity_mean': 'Humedad'
                    },
                placeholder="Variable",
                value="pm_25_mean",
                clearable=False,
            ),
            width=3
        ),
        dbc.Col(
            dcc.Dropdown(
                id="datetime",
                options= month_filter,
                value="Diario",
                clearable=False,
                placeholder="Mes",
            ),
            width=4
        ),   
    ],style={'marginBottom': '10px'}),
    
    dcc.Graph(id='bogota_map')
],)


left_map_content = html.Div([
    
    html.H2("Explora"),
    html.P("Este mapa interactivo te permite explorar los barrios de Bogotá con mayores niveles de contaminación por partículas PM 1, PM2.5 y PM.10, a demas puedes chequear los barrios con mayor humedad o temperatura. "),
    html.H2("¿Qué información puedes obtener?"),
    html.Div([
        "Puedes explorar el mapa haciendo zoom, ",
        html.Span("moviéndote con el clic izquierdo,", className="highlight"),
        " y cambiando ",
        html.Span("la perspectiva con el clic derecho.", className="highlight"),
        " Además, puedes ",
        html.Span("seleccionar un barrio",className="highlight"),
        " para acceder a mediciones detalladas y obtener información adicional en la sección inferior del dashboard."
    ]),
    html.Br(),
    html.Div(["También puedes ",
           html.Span("aplicar filtros según la variable de tu interés", className="highlight"),
           " y las muestras recolectadas en meses anteriores para un análisis más específico y detallado."]),
    
    ], className="target_explication")

regression_map_div = html.Div([
        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                    id="frecuency",
                    options=["Diaria", "Semanal", "Mensual"],
                    value="Diaria",
                    clearable=False,
                    placeholder="Frecuencia",
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
                    value='pm_25',
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

SIDEBAR_STYLE = {
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "rgba(0,0,0,0)",
}

sidebar = html.Div(
    [
        dbc.Nav(
            [
                dbc.NavLink("PM 1", href="PM_1", active="exact", className="nav_link_info"),
                dbc.NavLink("PM 2.5", href="PM_2.5", active="exact", className="nav_link_info"),
                dbc.NavLink("PM 10", href="PM_10", active="exact", className="nav_link_info"),
                dbc.NavLink("Indice de Calidad del Aire", href="ICA", active="exact", className="nav_link_info"),
            ],
            vertical=True,
            pills=True,
            className="nav_info"
        ),
    ],
    #style=SIDEBAR_STYLE,
    className="nav_info_container"
)

content = html.Div(id="page-content")

dashboard = dbc.Container(
    [
        html.Div(
            [
                html.Div([
                    html.H1("Dashboard Interactivo", className="title_section_2"),
                    html.H2("Análisis de Contaminación y Clima en Barrios de Bogotá", className="sub_title_section_2"),
                    ], className="titles_section_2"
                )
            ],
            className="my-4",  # Agrega clases de margen para espaciar los elementos
        ),
        dbc.Row(
            [
                dbc.Col(left_map_content),
                dbc.Col(bogota_map_div),
            ],
            className="g-0 align-items-center",
            align="center",
        ), 
        
        html.Div(["Aquí puedes examinar con detalle la información de las zonas seleccionadas en el mapa. ", 
                html.Span("Realiza comparaciones y obtén información precisa.", className="highlight"),
                " Las unidades en el eje Y son microgramos por metro cúbico, con cada muestra tomada en una hora específica del día."]
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
        
       html.Div([dcc.Location(id="url"), sidebar, content]),
       
       footer_content
        
    ],
    fluid=True,
)

'''dbc.Row(
    [
        dcc.Location(id="url"),
        dbc.Col(sidebar, width=3),
        dbc.Col(content),
    ],

), '''

@app.callback(
    Output('bogota_map', 'figure'),
    [Input('bogota_map', 'clickData'),
     Input('variable_map', 'value'),
     Input('datetime', 'value')]
)
def update_map_on_click(clickData, variable_map, datetime):
    global selected_areas, geo_fig, actual_val, actual_month,df_map_volatile
    
    if clickData is not None:
        selected_neigh = clickData['points'][0]['location']
        if selected_neigh not in selected_areas:
            selected_areas.append(selected_neigh)
        else:
            if actual_val == variable_map and actual_month==datetime:
                selected_areas.remove(selected_neigh)
    elif len(selected_areas)==0:
        selected_areas.append(df.sample(n=1)['neighborhood'].values[0])
    
    if actual_val != variable_map:
        actual_val = variable_map
        
    if actual_month != datetime:
        actual_month = datetime
        df_map_volatile = get_month_data(df, df2, datetime)
    
    feature_areas = get_areas_border(df, selected_areas)
    
    geo_fig = get_figure(df_map_volatile, variable_map)  
        
    geo_fig.update_traces(marker_opacity=feature_areas['op'], 
                       marker_line_width=feature_areas['wid'],
                       marker_line_color=feature_areas['col']) 
    return geo_fig



@app.callback(
    [Output('regression', 'figure'),
     Output('bar_figure', 'figure')],
    [Input('bogota_map', 'clickData'),
     Input('variable_map', 'value'),
     Input('datetime', 'value'),
     Input('varible_regression', 'value'),
     Input('frecuency', 'value')]
)
def update_regression_figure(clickData, variable_map, datetime, varible_regression, frecuency):

    global selected_areas, df3
    
    dff = create_time_series(datetime)
    
    dff['datetime'] = pd.to_datetime(dff['datetime'])
    
    if frecuency == "Semanal":
        dff = dff.groupby([dff['neighborhood'], dff['name'], dff['datetime'].dt.strftime('%Y-%U')]).agg({
            'pm_25': 'mean',
            'pm_10': 'mean',
            'temperature': 'mean',
            'humidity': 'mean',
        }).reset_index()
        
    elif frecuency == "Mensual":
        dff = dff.groupby([dff['neighborhood'], dff['name'], dff['datetime'].dt.strftime('%Y-%m')]).agg({
            'pm_25': 'mean',
            'pm_10': 'mean',
            'temperature': 'mean',
            'humidity': 'mean',
        }).reset_index()
    
    dff.reset_index(inplace=True) 
    
    fig = go.Figure()
    
    fig = px.line(dff, x='datetime', y=dff[properties_figures[variable_map][2]], color='name', markers=True) # , line_shape='spline'

    if isinstance(varible_regression, list):
        for i in varible_regression:
            if i != properties_figures[variable_map][2]:
                fig.add_trace(go.Scatter(x=dff['datetime'], y=dff[i], mode='lines+markers', name=i.capitalize()))
                 
    dfe = create_bar_graph()
    
    figg = px.bar(dfe, x="variable", y="value", color="neighborhood", text_auto=True)

    return update_style_regression_figure(fig, variable_map), update_style_bar_figure(figg)


#Aqui voy, hay un scroll automotico, mka termina esta mierda yaaa

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def update_url(pathname):
    print(pathname)
    if pathname == "/django_plotly_dash/app/SimpleExamplee/PM_1":
        return html.P("This is the content of the home page!")
    elif pathname == "/django_plotly_dash/app/SimpleExamplee/PM_2.5":
        return html.P("This is the content of page 1. Yay!")
    elif pathname == "/django_plotly_dash/app/SimpleExamplee/PM_10":
        return html.P("Oh cool, this is page 2!")
