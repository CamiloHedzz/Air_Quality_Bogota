import json
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import Dash, html, dcc, callback, Output, Input

with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)

df = pd.read_csv("https://raw.githubusercontent.com/CamiloHedzz/Procesamiento-de-imagenes/main/bogota_cadastral2.csv",
                   dtype={"DISPLAY_NAME": str})

app = DjangoDash('SimpleExample')

app.layout = html.Div([
    html.Div([
        dcc.Graph(
            id='choropleth-map',
            figure={
                'data': [
                    go.Choroplethmapbox(
                        geojson=counties,
                        locations=df.code,
                        z=df.sampl,
                        featureidkey='properties.DISPLAY_NAME',
                        colorscale="Viridis",
                        zmin=df.sampl.min(),
                        zmax=df.sampl.max(),
                        marker_opacity=0.5,
                    )
                ],
                'layout': go.Layout(
                    mapbox_style="open-street-map",
                    mapbox_zoom=10,
                    mapbox_center={"lat": 4.60971, "lon": -74.08175},
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    width=800,
                    height=600
                )
            }
        )
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)