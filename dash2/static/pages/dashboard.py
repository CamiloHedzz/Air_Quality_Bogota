import pandas as pd
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, Input, Output
import plotly.express as px
import dash

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
                style={'color': 'black'}
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
                style={'color': 'black'}
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
                    value='pm_25',
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
)

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