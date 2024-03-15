import plotly.graph_objs as go
import pandas as pd
import json
with open('dash2/datasets/bogota_cadastral.json', 'r') as file:
    counties = json.load(file)

#Dataset que representa el mapa de bogota
df = pd.read_csv("dash2/datasets/final_geodata.csv",
                   dtype={"neighborhood": str})

#Dataset que representa las muestras
df2 = pd.read_csv("dash2/datasets/final_rutes.csv")

properties_figures = {
    'pm_25_mean': ['PM 2.5 <br> µg/m³', "Viridis"],
    'pm_10_mean': ['PM 10 <br> µg/m³', "Cividis "],
    'temperature_mean': ['Temperatura <br> Celcius', "Jet"],
    'humidity_mean': ['% Humedad', 'ice']
}

geo_fig_general = go.Figure(go.Choroplethmapbox(
    geojson=counties,
    locations=df['neighborhood'],
    featureidkey='properties.DISPLAY_NAME',
    z=df['pm_25_mean'],
    colorscale= "Viridis",
    zmin=df['pm_25_mean'].min(),
    zmax=df['pm_25_mean'].max(),
    colorbar_title = 'PM 2.5<br>µg/m³'
))

def get_figure(variable, title_bar, color_scale):
    global geo_fig_general
    print(df[variable])
    geo_fig_general.update_traces(
        z=df[variable],
        colorscale= color_scale,
        zmin=df[variable].min(),
        zmax=df[variable].max(),
        colorbar_title = title_bar
    )

    return geo_fig_general
     
def update_figure(geo_fig):
    global geo_fig_general
    
    geo_fig.update_layout(
        autosize=True, 
        mapbox_zoom=11,
        width=500, height=400,
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_center={"lat": 4.60971, "lon": -74.08175},
        paper_bgcolor="#F2F2F2",
        plot_bgcolor="#F2F2F2"
    )
    geo_fig_general = geo_fig
    return geo_fig