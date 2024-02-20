import json
import random
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input, Patch


from .rute_utils import *

import plotly.express as px

app = DjangoDash('SimpleExample')

with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)

df = pd.read_csv("dash2/datasets/finalData.csv",
                   dtype={"code": str})

df2 = pd.read_csv("dash2/datasets/final_rutes.csv")

selected_areas = {}

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='bogota-map')
    ], style={ 'display': 'inline-block'}),
    
    html.Div([
        dcc.Graph(id='regression', className='regression-container'),
    ],style={'display': 'inline-block', 'width': '49%', 'margin-left': '3%'}),
])

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
        colorbar_title = "Rango Particulas<br>PM2.5"
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
    dff['datetime'] = pd.to_datetime(dff['datetime'])
    window_size = 10
    dff['tendencia'] = dff['sampl'].rolling(window=window_size, min_periods=1).mean()
    
    #fig = px.line(dff, x='datetime', y=['sampl', 'tendencia'], color='neig', markers=True)
    
    
    #fig = px.scatter(dff, x="datetime", y="sampl", color='neig',
    #            title="Rolling Median")
    
    fig = px.scatter(dff, x="datetime", y="sampl", color='neig', trendline="rolling", trendline_options=dict(function="median", window=2),
                title="Rolling Median")
    
   # fig.update_traces(mode='lines', line=dict(color='red', dash='dash'), selector=dict(name='tendencia'), markers=False)
             
    fig.update_layout(title='Muestra de particulas PM2.5 por barrio',
                        xaxis_title="Time",
                        yaxis_title="PM 2.5 µg/m³",
                        legend_title="Barrios",
                        width=600,  
                        height=400,
                        paper_bgcolor="#F2F2F2",
                        plot_bgcolor="#F2F2F2"
        )
            
    fig.update_xaxes(rangeslider_visible=True)
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
            dff.loc[len(dff)] = new_row            
    selected_areas[dff['code'].iloc[0]] = dff #Se agrega todo al dataset
    dataframe_combinado = pd.concat(selected_areas.values())

    return dataframe_combinado

def get_regression(dff):
    #dff = pd.DataFrame(columns=['datetime', 'code', 'neig', 'sampl']
    ventana = 2 
    tendencia = dff['sampl'].rolling(window=ventana).mean()
    return tendencia

    
if __name__ == '__main__':
    app.run_server(debug=True)
    
