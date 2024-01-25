import json
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input
import random
from dash.exceptions import PreventUpdate


app = DjangoDash('SimpleExample')

with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)

df = pd.read_csv("https://raw.githubusercontent.com/CamiloHedzz/Procesamiento-de-imagenes/main/bogota_cadastral2.csv", dtype={"code": str})

selected_areas = []

fig = go.Figure(go.Choroplethmapbox())

app.layout = html.Div([
    dcc.Graph(
        id='basic-interactions',
    )
])

cont = 0

def get_figure(markerlinewidth, markerlinecolor, markeropacity): 
    fig = go.Figure(go.Choroplethmapbox(
        geojson=counties,
        locations=df.code,
        z=df.sampl,
        featureidkey='properties.DISPLAY_NAME',
        colorscale="Viridis",
        zmin=df.sampl.min(),
        zmax=df.sampl.max(),
        marker_opacity=markeropacity,
        marker_line_width=markerlinewidth,  
        marker_line_color=markerlinecolor,
    ))
    
    return update_figure(fig)

def update_figure(updated_fig):
    if cont is 0:    
        updated_fig.update_layout(
            mapbox_zoom=10,
            width=800, height=600,
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            mapbox_center={"lat": 4.60971, "lon": -74.08175}
        )
    cont+=1
    return updated_fig

@app.callback(
    Output('basic-interactions', 'figure'),
    Input('basic-interactions', 'clickData'))
def select_location(clickData):
    if clickData is not None:
        selected_area = clickData['points'][0]['location']
        if selected_area in selected_areas:
            selected_areas.remove(selected_area)
        else:
            selected_areas.append(selected_area)
    else:
        ale = random.choice(counties['features'])['properties']['DISPLAY_NAME']
        selected_areas.append(ale)
    
    feature_areas = {'op': [], 'wid': [], 'col': []}
    for feature in counties['features']:
        display_name = feature['properties']['DISPLAY_NAME']
        if display_name in selected_areas:
            feature_areas['op'].append(1)
            feature_areas['wid'].append(3)
            feature_areas['col'].append('red')
        else:
            feature_areas['op'].append(0.50)
            feature_areas['wid'].append(1)
            feature_areas['col'].append('black')
            
    if fig is None:
        updated_fig = get_figure(1,'black',0.5)
    else:
        updated_fig = get_figure(feature_areas['wid'], feature_areas['col'], feature_areas['op'])
    
    return updated_fig

if __name__ == '__main__':
    app.run_server(debug=True)
