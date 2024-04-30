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
    'pm_25_mean': ['PM 2.5 <br> µg/m³', "Viridis", "pm_25", 'Particulas PM 2.5 µg/m³ por Barrio'],
    'pm_10_mean': ['PM 10 <br> µg/m³', "Cividis", "pm_10", 'Particulas PM 10 µg/m³ por Barrio'],
    'temperature_mean': ['Temperatura <br> Celcius', "Jet", 'temperature', 'Temperatura en C° por Barrio'],
    'humidity_mean': ['% Humedad', 'ice', 'humidity', 'Porcentaje de humedad por Barrio']
}

geo_fig_general = go.Figure(go.Choroplethmapbox(
    geojson=counties,
    locations=df['neighborhood'],
    featureidkey='properties.DISPLAY_NAME',
    z=df['pm_25_mean'],
    colorscale= "Viridis",
    zmin=df['pm_25_mean'].min(),
    zmax=df['pm_25_mean'].max(),
    colorbar_title = 'PM 2.5<br>µg/m³',
))

def get_figure(dff, variable):
    global geo_fig_general, properties_figures
    fig_data = properties_figures[variable]
    
    geo_fig_general.update_traces(
        #template='plotly_dark',
        #  mapbox_style='carto-positron',    
        z=dff[variable],
        colorscale= fig_data[1],
        zmin=dff[variable].min(),
        zmax=dff[variable].max(),
        colorbar_title = fig_data[0]
    )

    return geo_fig_general
     
def update_figure(geo_fig):
    global geo_fig_general
    
    geo_fig.update_layout(
        #autosize=False, 
        mapbox_zoom=10,
        #width=750, height=400,
        mapbox_style="carto-darkmatter",
        #mapbox_style="dark", mapbox_accesstoken=token,
        #mapbox_style="open-street-map",
        #mapbox_style='carto-positron', 
        autosize=True,
        mapbox_pitch=50,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_center={"lat": 4.67071, "lon": -74.08175},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )
    
    #geo_fig.update_geos(projection_type='mercator')
    
    geo_fig_general = geo_fig
    
    return geo_fig_general


#**************** Regression  ********************

def update_style_regression_figure(fig, variable_map):
    
    fig.update_layout(title=properties_figures[variable_map][3],
                        xaxis_title="Time",
                        yaxis_title=properties_figures[variable_map][0],
                        legend_title="Barrios",
                        autosize=True,
                        paper_bgcolor="rgba(0,0,0,0)",  # Fondo del área del gráfico transparente
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="white"),
                        yaxis_gridcolor="#212121",  # Color de la malla en el eje Y
                        xaxis_gridcolor="#212121" 
    )
    
    return fig

#**************** BarGraph  ********************

def update_style_bar_figure(fig):
    
    fig.update_layout(title="Comparacion general",
                        xaxis_title="Variable",
                        yaxis_title="Promedio",
                        legend_title="Barrios",
                        autosize=True,
                        paper_bgcolor="rgba(0,0,0,0)",  # Fondo del área del gráfico transparente
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="white"),
                        yaxis_gridcolor="#212121",  # Color de la malla en el eje Y
                        xaxis_gridcolor="#212121"   # Color de la malla en el eje X 
                        
    )
    
    return fig