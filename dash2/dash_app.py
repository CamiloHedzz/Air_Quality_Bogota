import json
import random
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input, Patch

app = DjangoDash('SimpleExample')

with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)

df = pd.read_csv("dash2/datasets/finalData.csv",
                   dtype={"code": str})



selected_areas = []


fig = go.Figure()

app.layout = html.Div([
    dcc.Graph(
        id='basic-interactions',
    )
])


@app.callback(
    Output('basic-interactions', 'figure'),
    [Input('basic-interactions', 'clickData')]
)
def update_map_on_click(clickData):
    global selected_areas
    
    if clickData is not None:
        selected_area = clickData['points'][0]['location']

        if selected_area in selected_areas:
            selected_areas.remove(selected_area)
        else:
            selected_areas.append(selected_area)
    elif len(selected_areas)==0:
        ale = df.sample(n=1)
        selected_areas.append(ale['code'].values[0])
        
        
    print(selected_areas)   
    feature_areas = {'op': [], 'wid': [], 'col': []}
    
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
        colorbar_title = "Particulas"

    ))
    
    updated_fig.update_layout(
        
        autosize=True,
        width=800, height=600,
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_center={"lat": 4.60971, "lon": -74.08175},
    )

    return updated_fig

if __name__ == '__main__':
    app.run_server(debug=True)
