import json
import random
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input, Patch
from scipy.interpolate import griddata


from .rute_utils import *

import plotly.express as px

app = DjangoDash('SimpleExample')

external_stylesheets = ['dash2/static/dash_style.css']

with open('dash2/datasets/bogota_cadastral.json', 'r') as file:
    counties = json.load(file)

df = pd.read_csv("dash2/datasets/finalData.csv",
                   dtype={"code": str})

df2 = pd.read_csv("dash2/datasets/final_rutes.csv")

selected_areas = {}


app.layout = html.Div([ 
    html.Div([
        html.Div("Este mapa interactivo te permite explorar los barrios de Bogotá con mayores niveles de contaminación por partículas PM2.5. Puedes hacer zoom, moverte por el mapa e incluso seleccionar un barrio para ver las mediciones detalladas y obtener más información.",
                style={'fontFamily': 'Oswald Light', 'textAlign': 'justify', 'fontStyle': 'light', 'fontSize': '18px', 'marginBottom': '20px'}
                ),
        dcc.Graph(id='bogota-map')
    ], style={ 'display': 'inline-block', 'width': '45%'}),
    
    html.Div([
        html.Div("Aquí puedes examinar con detalle la información de las zonas seleccionadas en el mapa. Realiza comparaciones y obtén información precisa. Las unidades en el eje Y son microgramos por metro cúbico, con cada muestra tomada en una hora específica del día.",
                 style={'fontFamily': 'Oswald Light', 'textAlign': 'justify', 'fontStyle': 'light', 'fontSize': '18px', 'marginBottom': '20px'}),
        dcc.Graph(id='regression'),
    ],style={'display': 'inline-block', 'width': '45%', 'margin-left': '3%'})
    
],style={'overflow': 'hidden', 'display': 'flex', 'flexWrap': 'wrap'})

'''
    html.Div([
            dcc.Graph(figure=fig_3d),
    ],style={ 'width': '49%', 'height': '500px', 'display': 'inline-block'}),
'''

@app.callback(
    Output('bogota-map', 'figure'),
    [Input('bogota-map', 'clickData')]
)
def update_map_on_click(clickData):
    global selected_areas
    feature_areas = {'op': [], 'wid': [], 'col': []}
    if clickData is not None:
        selected_area = clickData['points'][0]['location']
        if selected_area in selected_areas.keys():
            del selected_areas[selected_area]
        else:
            print(selected_area)
            selected_areas[selected_area] = None
    elif len(selected_areas.keys())==0:
        selected_areas[df.sample(n=1)['code'].values[0]]= None
        
    for display_name in df.code.items():
        if display_name[1] in selected_areas:
            feature_areas['op'].append(1)
            feature_areas['wid'].append(3)
            feature_areas['col'].append('red')
        else:
            feature_areas['op'].append(0.50)
            feature_areas['wid'].append(1)
            feature_areas['col'].append('black')
    
    updated_fig = go.Figure(go.Choroplethmapbox(
        geojson=counties,
        locations=df.code,
        z=df.sampl,
        featureidkey='properties.DISPLAY_NAME',
        colorscale="Viridis",
        zmin=df.sampl.min(),
        zmax=df.sampl.max(),
        marker_opacity=feature_areas['op'],
        marker_line_width=feature_areas['wid'],
        marker_line_color=feature_areas['col'],
        colorbar_title = "PM 2.5<br>µg/m³"
    ))
 
    updated_fig.update_layout(
        autosize=True,
        mapbox_zoom=11,
        width=600, height=400,
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_center={"lat": 4.60971, "lon": -74.08175},
        paper_bgcolor="#F2F2F2",
        plot_bgcolor="#F2F2F2"
    )
    
    return updated_fig

@app.callback(
    Output('regression', 'figure'),
    [Input('bogota-map', 'clickData')]
)
def update_regression_figure(clickData):
    selected_area = ''
    if clickData is not None:
        selected_area = clickData['points'][0]['location']
    return update_regression(selected_area)
        
        
def update_regression(selected_area):
    global selected_areas
   
    fig = go.Figure()
    
    #if selected_area == '' and len(selected_areas.keys())>0:       
    #    pass
    dff = create_time_series()
    
    fig = px.line(dff, x='datetime', y=['sampl'], color='neig', markers=True, line_shape='spline')
    
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
    
    dff = pd.DataFrame(columns=['datetime', 'code', 'neig', 'sampl'])
    
    for i, value in df2.iterrows():
        if value['code'] in selected_areas:
            name = value['code'].split(',')[0]
            new_row = {
                'datetime': value['datetime'],
                'code': value['code'],
                'neig': name,
                'sampl': value['sampl'],
                
            }
            #dff = dff.append(new_row, ignore_index=True)  # Añadir fila al DataFrame

            dff.loc[len(dff)] = new_row            
    selected_areas[dff['code'].iloc[0]] = dff #Se agrega todo al dataset
    dataframe_combinado = pd.concat(selected_areas.values())

    return dataframe_combinado

def get_figures():
    regression = update_regression_figure(None)
    bogotamap = update_map_on_click(None)
    return bogotamap, regression
    
    
if __name__ == '__main__':
    app.run_server(debug=True)
    
