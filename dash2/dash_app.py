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
df3 = pd.DataFrame(columns=['id_rute','datetime','pm_25','pm_10','temperature','humidity','neighborhood', 'name'])


df_map_volatile = df

selected_areas = []

geo_fig = update_figure(geo_fig_general)

month_filter = pd.to_datetime(df2['datetime']).dt.strftime('%B').unique().tolist()
month_filter.append("Diario")    

actual_val = "pm_25_mean"
actual_month = "Diario"

actual_month_reg = "Diario"

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
    
    dbc.Col(dcc.Graph(id='bogota_map'))
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
    Output('regression', 'figure'),
    [Input('bogota_map', 'clickData'),
     Input('variable_map', 'value'),
     Input('datetime', 'value'),
     Input('varible_regression', 'value'),
     Input('frecuency', 'value')]
)
def update_regression_figure(clickData, variable_map, datetime, varible_regression, frecuency):

    global selected_areas, df3
    
    dff = create_time_series(datetime) 

    columnas_numericas = dff.select_dtypes(include=[np.number])

    columnas_numericas['datetime'] = pd.to_datetime(dff['datetime'])

    columnas_numericas.set_index('datetime', inplace=True)

    if frecuency == "Semanal":
        dff = columnas_numericas.resample('W').mean()
    elif frecuency == "Mensual":
        dff = columnas_numericas.resample('M').mean()
        
    print(dff)    
    
    fig = px.line(dff, x='datetime', y=dff[properties_figures[variable_map][2]], color='name', markers=True) # , line_shape='spline'
                 
    fig.update_layout(title=properties_figures[variable_map][3],
                        xaxis_title="Time",
                        yaxis_title=properties_figures[variable_map][0],
                        legend_title="Barrios",
                        width=600,  
                        height=400,
                        paper_bgcolor="#F2F2F2",
                        plot_bgcolor="#F2F2F2"
    )
            
    #fig.update_xaxes(rangeslider_visible=True)
    return fig

def create_time_series(datetime):
    
    global selected_areas, df2, df3, actual_month_reg, actual_val, actual_month

    for selected_neigh in selected_areas:
             
    #if selected_neigh not in df3['neighborhood'].values:
        
        filter_neigh = df2.loc[df2['neighborhood'] == selected_neigh]
        
        filter_neigh['name'] = filter_neigh['neighborhood'].str.split(',').str[0]
                                
        df3 = pd.concat([df3, filter_neigh], ignore_index=True)

    df3.sort_values(by='datetime', inplace=True) 
    
    if actual_month_reg != datetime:
        if datetime != "Diario":
            actual_month_reg = datetime
            df_aux = df3.copy()
            df_aux['datetime'] = pd.to_datetime(df_aux['datetime'])
            df_aux = df_aux[(df3['datetime'].dt.strftime('%B') == datetime) & (df3['neighborhood'] != 'Unknown Zone')]
            return df_aux
        else:
            return df3
        
    return df3    

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
    
