import json
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input, Patch

app = DjangoDash('SimpleExample')

with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)

df = pd.read_csv("https://raw.githubusercontent.com/CamiloHedzz/Procesamiento-de-imagenes/main/bogota_cadastral2.csv",
                   dtype={"code": str})

selected_areas = []

fig = go.Figure()

app.layout = html.Div([
    dcc.Graph(
        id='basic-interactions',
    )
])

def get_figure(markerlinewidth, markerlinecolor, markeropacity):
    updated_fig = go.Figure(go.Choroplethmapbox(
        geojson=counties,
        locations=df.code,
        z=df.sampl,
        featureidkey='properties.DISPLAY_NAME',
        colorscale="Viridis",
        zmin=df.sampl.min(),
        zmax=df.sampl.max(),
        marker_opacity = markeropacity,
        marker_line_width = markerlinewidth,  # Adjust border width based on selection
        marker_line_color = markerlinecolor,  # Adjust border color based on selection
        #mapbox_center={"lat": 4.60971, "lon": -74.08175}
    ))
    return updated_fig

@app.callback(
    Output('basic-interactions', 'figure'),
    Input('basic-interactions', 'clickData'))
def update_map_on_click(clickData):
    global selected_areas
    markeropacity = 0.5
    markerlinew = 1
    markerlinec = 'black'
    
    if clickData is not None:
        print("Mkaaaa")
        selected_area = clickData['points'][0]['location']
        if selected_area in selected_areas:
            selected_areas.remove(selected_area)
            updated_fig = get_figure(markerlinew, markerlinec, markeropacity)
            for i, feature in enumerate(counties['features']):
                display_name = feature['properties']['DISPLAY_NAME']
                if display_name in selected_areas:
                    counties['features'][i]['properties']['selected'] = True
                    markeropacity = 1
                    markerlinew = 3
                    markerlinec = 'aqua'
                else:
                    counties['features'][i]['properties']['selected'] = False
        else:
            selected_areas.append(selected_area)
            
    updated_fig = get_figure(markerlinew, markerlinec, markeropacity)
    
    updated_fig.update_layout(
        mapbox_zoom=10,
        width=800, height=600,
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_center={"lat": 4.60971, "lon": -74.08175}
    )
    
    return updated_fig

if __name__ == '__main__':
    app.run_server(debug=True)
    

