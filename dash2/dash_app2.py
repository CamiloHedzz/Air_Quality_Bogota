import json
import random
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input, Patch

import plotly.express as px

app = DjangoDash('SimpleExamplee')

with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)

df = pd.read_csv("dash2/datasets/finalData.csv",
                   dtype={"code": str})

df2 = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')


selected_areas = []

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='bogota-map',)
    ], style={ 'display': 'inline-block'}),
    
    html.Div([
        dcc.Dropdown(df2.country.unique(), 'Canada', id='dropdown-selection'),
        dcc.Graph(id='regression'),
    ], style={'display': 'inline-block', 'width': '49%'}),
])

@app.callback(
    Output('bogota-map', 'figure'),
    [Input('bogota-map', 'clickData')]
)
def update_map_on_click(clickData):
    print("df")
    global selected_areas
    feature_areas = {'op': [], 'wid': [], 'col': []}
    if clickData is not None:
        selected_area = clickData['points'][0]['location']
        if selected_area in selected_areas:
            selected_areas.remove(selected_area)
        else:
            selected_areas.append(selected_area)
    elif len(selected_areas)==0:
        selected_areas.append(df.sample(n=1)['code'].values[0])
        
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
        mapbox_zoom=11,
        width=700, height=500,
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_center={"lat": 4.60971, "lon": -74.08175},
    )
    
    return updated_fig

@app.callback(
    Output('regression', 'figure'),
    Input('dropdown-selection', 'value'))
def update_regression(value):
    dff = df2[df2.country==value]
    return px.line(dff, x='year', y='pop')

if __name__ == '__main__':
    app.run_server(debug=True)


#***************** CONTROLLERS *****************



'''

@app.callback(
    Output('basic-interactions', 'figure'),
    Input('basic-interactions', 'clickData'))
def update_graph(clickData):
    
    if geo_sectors is not None and len(school)==0:
        fig = get_Choropleth(df, geo_sectors, arg, marker_opacity=1.0,
                             marker_line_width=3, marker_line_color='aqua', fig=fig)

    return fig
    
    if clickData is not None and "location" in clickData["points"][0]:
        sector = clickData["points"][0]["location"]
        if sector in postcodes:
            postcodes.remove(sector)
        elif len(postcodes) < cfg["topN"]:
            postcodes.append(sector)
    print(changed_id)
    if clickData:
        location = str(clickData['points'][0]['location'])
        print(country_count = list(df[df.code.isin(location)].index))
    #fig.data[1].locations = [location]
    #fig.data[1].marker_line_width = 5
    #fig.data[1].marker_line_color = 'aqua'
        
    return fig





@app.callback(Output('output-state', 'children'),
              Input('submit-button-state', 'n_clicks'))
def update_output(n_clicks):
    print("Entra")
    return f'The Button has been pressed {n_clicks} times'



@app.callback(
    Output('click-data', 'children'),
    Input('basic-interactions', 'clickData'))

def display_click_data(clickData):
    if clickData is not None:
        print(clickData['points'][0]['location'])
        id = clickData['points'][0]['location']
        for i in df['code']:
            if i==id:
                print("Entraa")
    
    #return json.dumps(clickData, indent=2)
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

#otro intento


'''
import json
import random
import pandas as pd
import plotly.graph_objs as go
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input
from shapely.geometry import Point, Polygon


# ******************* VISTA *******************

app = DjangoDash('SimpleExample')
feature_areas = {'op': [], 'wid': [], 'col': []}
selected_areas = []

with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)
    
    #coordinates = counties['features']
    #zones = {zone['properties']['DISPLAY_NAME']: zone['geometry']['coordinates'][0][0] for zone in coordinates}
    #zone_polygons = {zone_name: Polygon(zone_coords) for zone_name, zone_coords in zones.items()}

df_final = pd.read_csv("dash2/datasets/finalData.csv", dtype={"code": str})


app.layout = html.Div([
    dcc.Graph(
        id='basic-interactions',
    )
])

# ******************* FUNCIONES *******************

def get_figure(markerlinewidth, markerlinecolor, markeropacity):
    print(3 in markerlinewidth)
    #df_final = create_dataset()
    updated_fig = go.Figure(go.Choroplethmapbox(
        geojson=counties,
        locations=df_final.code,
        z=df_final.sampl,
        featureidkey='properties.DISPLAY_NAME',
        colorscale="Viridis",
        zmin=df_final.sampl.min(),
        zmax=df_final.sampl.max(),
        marker_opacity=markeropacity,
        marker_line_width=markerlinewidth,  
        marker_line_color=markerlinecolor,
    ))
    
    updated_fig = update_figure(updated_fig)
    
    return updated_fig

def update_figure(updated_fig):
    updated_fig.update_layout(
        mapbox_zoom=10,
        width=800, height=600,
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_center={"lat": 4.60971, "lon": -74.08175}
    )
   
    return updated_fig


# ******************* CALLBACKS *******************


@app.callback(
    Output('basic-interactions', 'figure'),
    Input('basic-interactions', 'clickData'))
def select_location(clickData):
    global selected_areas
    
    if clickData is not None:
        selected_area = clickData['points'][0]['location']
        if selected_area in selected_areas:
            selected_areas.remove(selected_area)
        else:
            selected_areas.append(selected_area)
    else:
        #ale = random.choice(counties['features'])['properties']['DISPLAY_NAME']        
        ale = df_final.sample(n=1)
        selected_areas.append(ale['code'].values[0])
        print("barrio random:", ale['code'].values[0])
    
    for feature in counties['features']:
        display_name = feature['properties']['DISPLAY_NAME']
        if display_name in selected_areas:
            feature_areas['op'].append(1)
            feature_areas['wid'].append(3)
            feature_areas['col'].append('red')
            print(display_name, "entra a cambio")
        else:
            feature_areas['op'].append(0.50)
            feature_areas['wid'].append(1)
            feature_areas['col'].append('black')
    
    updated_fig = get_figure(feature_areas['wid'], feature_areas['col'], feature_areas['op'])
    
    return updated_fig

if __name__ == '__main__':
    app.run_server(debug=True)

'''













