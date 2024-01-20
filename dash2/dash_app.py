import json
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import Dash, html, dcc, Output, Input


app = DjangoDash('SimpleExample')


with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)

df = pd.read_csv("https://raw.githubusercontent.com/CamiloHedzz/Procesamiento-de-imagenes/main/bogota_cadastral2.csv",
                   dtype={"DISPLAY_NAME": str})

fig = go.Figure(go.Choroplethmapbox(
    geojson=counties,
    locations=df.code,
    z=df.sampl,
    featureidkey='properties.DISPLAY_NAME',
    colorscale="Viridis",
    zmin=df.sampl.min(),
    zmax=df.sampl.max(),
    marker_opacity=0.5,
    #marker_line_width=3,
    #marker_line_color='aqua'
))

fig.update_layout(
    mapbox_zoom=10,
    width=800, height=600,
    mapbox_style="open-street-map",
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    mapbox_center={"lat": 4.60971, "lon": -74.08175}
)

app.layout = html.Div([
    
    dcc.Graph(
        id='basic-interactions',
        figure=fig
    ),

     html.Button(id='submit-button-state', n_clicks=0, children='Submit'),
     html.Div(id='output-state'),
     html.Div([
            dcc.Markdown( ),
            html.Pre(id='click-data'),
        ], className='three columns'),
])

@app.callback(Output('output-state', 'children'),
              Input('submit-button-state', 'n_clicks'))
def update_output(n_clicks):
    print("Entra")
    return f'The Button has been pressed {n_clicks} times'

@app.callback(
    Output('click-data', 'children'),
    Input('basic-interactions', 'clickData'))
def display_click_data(clickData):
    return json.dumps(clickData, indent=2)

if __name__ == '__main__':
    app.run_server(debug=True)

'''
app.layout = html.Div([
    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        df['year'].min(),
        df['year'].max(),
        step=None,
        value=df['year'].min(),
        marks={str(year): str(year) for year in df['year'].unique()},
        id='year-slider'
    )
])

@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('year-slider', 'value'))

def update_figure(selected_year):
    filtered_df = df[df.year == selected_year]

    fig = px.scatter(filtered_df, x="gdpPercap", y="lifeExp",
                     size="pop", color="continent", hover_name="country",
                     log_x=True, size_max=55)

    fig.update_layout(transition_duration=500)

    return fig


if __name__ == '__main__':
    app.run(debug=True)
'''

