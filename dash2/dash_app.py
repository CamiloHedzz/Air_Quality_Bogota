import json
import random
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input, Patch
import dash_bootstrap_components as dbc
from dash2 import dash_app2

from .rute_utils import *
from .dash_figures import *
from .dash_logic import *

import plotly.express as px

app = DjangoDash('SimpleExample', external_stylesheets=[dbc.themes.BOOTSTRAP])

#external_stylesheets = ['/assets/stylesheet.css']

#Rutas seleccionadas
df3 = None

df_map_volatile = df

selected_areas = {}

geo_fig = update_figure(geo_fig_general)

month_filter = pd.to_datetime(df2['datetime']).dt.strftime('%B').unique().tolist()
month_filter.append("Diario")    
actual_val = "pm_25_mean"
actual_month = "Diario"

bogota_map_div = html.Div([
    html.Div(
        "Este mapa interactivo te permite explorar los barrios de Bogotá con mayores niveles de contaminación por partículas PM2.5. Puedes hacer zoom, moverte por el mapa e incluso seleccionar un barrio para ver las mediciones detalladas y obtener más información.",
        style={'fontFamily': 'Oswald Light', 'textAlign': 'justify', 'fontSize': '18px', 'marginBottom': '20px'}),
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
    
    dbc.Col(dcc.Graph(id='bogota-map'))
])
    
regression_map_dib = html.Div([
        html.Div("Aquí puedes examinar con detalle la información de las zonas seleccionadas en el mapa. Realiza comparaciones y obtén información precisa. Las unidades en el eje Y son microgramos por metro cúbico, con cada muestra tomada en una hora específica del día.",
                 style={'fontFamily': 'Oswald Light', 'textAlign': 'justify', 'fontSize': '18px', 'marginBottom': '20px'}),
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
                        'pm_25_mean': 'PM 2.5',
                        'pm_10_mean': 'PM 10',
                        'temperature_mean': 'Temperatura',
                        'humidity_mean': 'Humedad'
                    },
                    value='pm_25_mean',
                    multi=True,
                    clearable=False
                ),width=9
            ),
        ],style={'marginBottom': '10px'}),
        dcc.Graph(id='regression'),
],style={})
    
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(bogota_map_div, md=5,),
                dbc.Col(regression_map_dib, md=5, style={"margin-left": "90px"}),
            ],
            #justify="between", 
            align="center",
            style={"background-color": "#F2F2F2"}
        ),  
    ],
    fluid=True,
    style={"overflow": "hidden","background-color": "#F2F2F2"}
)

@app.callback(
    Output('bogota-map', 'figure'),
    [Input('bogota-map', 'clickData'),
     Input('variable_map', 'value'),
     Input('datetime', 'value')]
)
def update_map_on_click(clickData, variable_map, datetime):
    global selected_areas, geo_fig, actual_val, actual_month,df_map_volatile
    fig_data = properties_figures[variable_map]
    
    if clickData is not None:
        selected_area = clickData['points'][0]['location']
        if selected_area in selected_areas.keys():
            del selected_areas[selected_area]
        else:
            selected_areas[selected_area] = None
    elif len(selected_areas.keys())==0:
        selected_areas[df.sample(n=1)['neighborhood'].values[0]] = None
        
    feature_areas = get_areas_border(df_map_volatile, selected_areas)
    
    if actual_val != variable_map:
        actual_val = variable_map
    
    if actual_month != datetime:
        actual_month = datetime
        df_map_volatile = get_month_data(df, df2, datetime)
    
    geo_fig = get_figure(df_map_volatile, variable_map, fig_data[0], fig_data[1])  
        
    geo_fig.update_traces(marker_opacity=feature_areas['op'],
                       marker_line_width=feature_areas['wid'],
                       marker_line_color=feature_areas['col']) 
    return geo_fig


#@app.callback(
#    Output('regression', 'figure'),
#    [Input('bogota-map', 'clickData')]
#)
def update_regression_figure(clickData):
    selected_area = ''
    if clickData is not None:
        selected_area = clickData['points'][0]['location']
    return update_regression(selected_area)
        
        
def update_regression(selected_area):
    global selected_areas, df3
   
    fig = go.Figure()
    
    
    dff = create_time_series()
    
    df3 = dff
    
    fig = px.line(dff, x='datetime', y=['pm_25'], color='neig', markers=True) # , line_shape='spline'
    
    '''
    fig = px.scatter(dff, x="datetime", y="sampl", color='neig', trendline="rolling", 
                 trendline_options=dict(window=2, win_type="gaussian", function_args=dict(std=2)),
                title="Rolling Mean with Gaussian Window")
   
    fig.add_trace(go.Scatter(x=dff['datetime'], y=dff['sampl'],
                         line=dict(color='royalblue', width=1)))
    '''
                 
    fig.update_layout(title='Muestra de particulas PM2.5 por barrio',
                        xaxis_title="Time",
                        yaxis_title="PM 2.5 µg/m³",
                        legend_title="Barrios",
                        width=600,  
                        height=400,
                        paper_bgcolor="#F2F2F2",
                        plot_bgcolor="#F2F2F2"
        )
            
    #fig.update_xaxes(rangeslider_visible=True)
    return fig

def create_time_series():
    
    global selected_areas, df2
    
    df3 = pd.DataFrame(columns=['datetime', 'neighborhood', 'neig', 'pm_25'])
    
    for j in selected_areas.keys():
        if selected_areas[j] is None:
            for i, value in df2.iterrows():
                if value['neighborhood'] in selected_areas:
                    name = value['neighborhood'].split(',')[0]
                    new_row = {
                        'datetime': value['datetime'],
                        'neighborhood': value['neighborhood'],
                        'neig': name,
                        'pm_25': value['pm_25'],
                    }
                    if j == value['neighborhood']:                
                        df3 = pd.concat([df3, pd.DataFrame([new_row])], ignore_index=True)
        
            selected_areas[j] = df3 #Se agrega todo al dataset
    
    dataframe_combinado = pd.concat(selected_areas.values(), ignore_index=True)
   
    dataframe_combinado.sort_values(by='datetime', inplace=True)

    #print(dataframe_combinado)
   
    return dataframe_combinado

def get_stadictic():
    
    aux_rutes = df2
    
    aux_rutes['datetime'] = pd.to_datetime(aux_rutes['datetime'])
    aux_rutes['hour'] = aux_rutes['datetime'].dt.strftime('%Y-%m-%d %H')
    hourly_avg_rutes = aux_rutes.groupby(aux_rutes['datetime'].dt.time)['pm_25'].mean()

    
    std_dash_figures = {"max_pm" : df.loc[df['pm_25_mean'] == df['pm_25_mean'].max()], #La maxima muestra de PM2.5 a nivel de barrios
        "min_pm" : df.loc[df['pm_25_mean'] == df['pm_25_mean'].min()],
        "min_hour": hourly_avg_rutes.idxmin(), #La maxima hora promedio con mas contaminacion
        "max_hour": hourly_avg_rutes.idxmax()}
      
    return std_dash_figures
    
if __name__ == '__main__':
    
    app.run_server(debug=True)
    
