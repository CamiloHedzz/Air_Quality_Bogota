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

#df2 = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

df2 = pd.read_csv("dash2/datasets/final_rutes.csv")

selected_areas = []

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='bogota-map',)
    ], style={ 'display': 'inline-block'}),
    
    html.Div([
        #dcc.Dropdown(df2.country.unique(), 'Canada', id='dropdown-selection'),
        dcc.Graph(id='regression'),
    ], style={'display': 'inline-block', 'width': '49%'}),
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
    [Input('bogota-map', 'clickData')]
)
def update_regression_figure(clickData):
    return update_regression()
        

def update_regression():
    
    dff = create_time_series()
    
    fig = px.line(dff, x='date', y='sampl', title='Time Series with Rangeslider')

    fig.update_xaxes(rangeslider_visible=True)
    
    return fig

def create_time_series():
    
    global selected_areas, df2
    
    dff = pd.DataFrame(columns=['date', 'sampl', 'code'])
    
    for i, value in df2.iterrows():
        if value['code'] in selected_areas:
            new_row = {
                'date': pd.to_datetime(value['date'] + ' ' + value['hour']),
                'code': value['code'],
                'sampl': value['sampl']
            }
            dff = dff.append(new_row, ignore_index=True)
    
    return dff

if __name__ == '__main__':
    app.run_server(debug=True)
    
'''

def update_regression(value):
    dff = df2[df2.country==value]
    create_finaldata_rutes()
    return px.line(dff, x='year', y='pop')


#def create_regression(dff):
    
 #   pass


def create_time_series(dff, axis_type, title):

    fig = px.scatter(dff, x='Year', y='Value')

    fig.update_traces(mode='lines+markers')

    fig.update_xaxes(showgrid=False)

    fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')

    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                       xref='paper', yref='paper', showarrow=False, align='left',
                       text=title)

    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})

    return fig


@callback(
    Output('x-time-series', 'figure'),
    Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-xaxis-column', 'value'),
    Input('crossfilter-xaxis-type', 'value'))
def update_x_timeseries(hoverData, xaxis_column_name, axis_type):
    country_name = hoverData['points'][0]['customdata']
    dff = df[df['Country Name'] == country_name]
    dff = dff[dff['Indicator Name'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(country_name, xaxis_column_name)
    return create_time_series(dff, axis_type, title)
'''