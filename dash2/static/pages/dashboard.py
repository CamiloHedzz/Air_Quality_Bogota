import pandas as pd
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output

#Clases y componentes
from ..components.switch import switch


from ...dash_figures import *
from ...dash_logic import *
from ...maindash import app

df_map_volatile = df

selected_areas = []

geo_fig = update_figure(geo_fig_general)

month_filter = pd.to_datetime(df2['datetime']).dt.strftime('%B').unique().tolist()
month_filter.append("Diario")    

actual_val = "pm_25_mean"
actual_month = "Diario"

actual_month_reg = "Diario"

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
    html.P("Puedes explorar el mapa haciendo zoom, moviéndote con el clic izquierdo, y cambiando la perspectiva con el clic derecho. Además, puedes seleccionar un barrio para acceder a mediciones detalladas y obtener información adicional en la sección inferior del dashboard. "),
    html.Br(),
    html.P("También puedes aplicar filtros según la variable de tu interés y las muestras recolectadas en meses anteriores para un análisis más específico y detallado."),
    
    ], className="target_explication")

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
                dbc.Col(left_map_content, className="g-0 align-items-center",),
                dbc.Col(bogota_map_div),
            ],
            className="g-0 align-items-center",
            align="center",
        ), 
        
        html.P("Aquí puedes examinar con detalle la información de las zonas seleccionadas en el mapa. Realiza comparaciones y obtén información precisa. Las unidades en el eje Y son microgramos por metro cúbico, con cada muestra tomada en una hora específica del día.")
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
    print("entraaa")
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

