import math
import csv
import os
import numpy as np
import random
from shapely.geometry import Point, Polygon
from datetime import datetime, timedelta
import json
from urllib.request import urlopen

with urlopen('https://gist.githubusercontent.com/john-guerra/ee93225ca2c671b3550d62614f4978f3/raw/b1d556c39f3d7b6e495bf26b7fda815765ac110a/bogota_cadastral.json') as response:
    counties = json.load(response)

    coordinates = counties['features']

    zones = {zone['properties']['DISPLAY_NAME']: zone['geometry']['coordinates'][0][0] for zone in coordinates}

#crear rutas
num_rutes = 25
num_points = 50

headers = ['date','hour','longitude', 'latitude' ,'sampl']
csv_data = []

random_hour = datetime.now().replace(
    hour=random.randint(0, 23),
    minute=random.randint(0, 59),
    second=random.randint(0, 59)
)

def get_angle(A, B, C):
    vector_AB = (B[0] - A[0], B[1] - A[1])
    vector_BC = (C[0] - B[0], C[1] - B[1])
    angulo_AB = math.atan2(vector_AB[1], vector_AB[0])
    angulo_BC = math.atan2(vector_BC[1], vector_BC[0])
    angulo = angulo_BC - angulo_AB
    angulo = angulo % (2 * math.pi)
    angulo_grados = math.degrees(angulo)
    return angulo_grados

def get_rute(num_points):
  rute =[[ random.uniform(-74.117487, -74.087274), random.uniform(4.750566, 4.542512)]]
  while len(rute) < num_points:
      lon = random.uniform(-74.117487, -74.087274)
      lat = random.uniform(4.750566, 4.542512)
      if abs(rute[-1][0] - lon) <= 0.002 and abs(rute[-1][1] - lat) <= 0.002:
          if len(rute) >= 3:
              a = get_angle((rute[-2][0], rute[-2][1]),(rute[-1][0], rute[-1][1]), (lon, lat))
              if a<90 or a>270:
                  rute.append([lon, lat])
          else:
              rute.append([lon, lat])
  return rute

def create_rute():
    for i in range(num_rutes):
        rute = get_rute(num_points)
        for j in range(num_points):
            sampl = random.randint(0, 10)
            hours = random_hour + timedelta(minutes=j*2)
            csv_data.append([hours.strftime("%Y-%m-%d"),hours.strftime("%H:%M:%S"), rute[j][0], rute[j][1], sampl])

    # Se guardan los archivos dinamicamente
    csv_file_path = f'dash2/rutes_csv/rute{i}.csv'

    with open(csv_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(csv_data)

    csv_data = []

'''
Cuando se lleva a cabo una toma de muestra, ésta está asociada con una coordenada específica.
Por esta razón, resulta crucial identificar a qué zona (en este contexto, un barrio)
corresponde la muestra recogida.
'''
zone_polygons = {zone_name: Polygon(zone_coords) for zone_name, zone_coords in zones.items()}

def get_zone(lat, lon):
    point = Point(lon, lat)
    for zone_name, zone_polygon in zone_polygons.items():
        if zone_polygon.contains(point):
            return zone_name
    return "Unknown Zone"

# Funcion para obtener el total de muestras relacionadas con una zona
def sampl_rute(df_rute):
  samples = {}
  for i in df_rute.values:
    lon, lat = i[2], i[3]
    id = get_zone(lat, lon)
    if id in samples:
      samples[id].append(i[4])
    else:
      samples[id] = [i[4]]
  return samples

# Funcion para determinar el numero de rutas ya guardadas
def num_rute_files():
  folder = "dash2/rutes_csv"
  files = os.listdir(folder)
  archivos = [archivo for archivo in files if os.path.isfile(os.path.join(folder, archivo))]
  return len(archivos)

#funcion para obtener el promedio de las mustras en cada zona
def mean_sample():
  mean_rutes={}
  num_files = num_rute_files()
  for i in range (num_files):
    df_rute = pd.read_csv(f"dash2/rutes_csv/rute{i}.csv")
    for clave, valores in sampl_rute(df_rute).items():
      mean_rutes[clave]= np.mean(valores)
  return mean_rutes

'''
Finalmente, se obtiene un archivo csv despues de haber identificado el barrio al
que pertenece cada muestra. Este archivo tiene unicamente dos columnas, el
identificador del barrio y el promedio de muestras correspondientes al barrio
'''

def create_dataset():
    headers = ['code', 'sampl']
    csv_data = []
    for key, data in mean_sample().items():
        code = key
        sampl = data
        csv_data.append([code, sampl])

    csv_file_path = 'dash2/datasets/finalData.csv'
    with open(csv_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(csv_data)

def get_figure_rutes(fig):
    for i in range(num_rute_files()): #Numero de archivos
        rute = pd.read_csv(f"dash2/rutes_csv/rute{i}.csv")
        list_lat, list_lon, list_samples = [],[],[]

        for _,j in rute.iterrows():
            list_lat.append(j.latitude)
            list_lon.append(j.longitude)
            list_samples.append(j.sampl)

        fig.add_trace(go.Scattermapbox(
            mode = "markers+lines",
            lon = list_lon,
            lat = list_lat,
            customdata = list_samples,
            marker = {'size': 5},
            #name=f'Ruta {i + 1}',
            hovertemplate="Lat: %{lat}<br>Lon: %{lon}<br>PM2.5: %{customdata}<extra></extra>",
            ))

    fig.update_layout(
        mapbox_zoom=10,
        width=800, height=600,
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_center={"lat": 4.60971, "lon": -74.08175},
        showlegend=False  # opcional
    )
    
#Convertir todos los rutes.csv en uno solo    
def create_finaldata_rutes():
    directorio = 'dash2/rutes_csv'
    
    dataframes = []

    for archivo in os.listdir(directorio):
        if archivo.endswith('.csv'):
            ruta_completa = os.path.join(directorio, archivo)
            df = pd.read_csv(ruta_completa)
            dataframes.append(df)

    df_final = pd.concat(dataframes, ignore_index=True)

    df_final.to_csv('dash2/datasets/final_rutes.csv', index=False)
    
#identificar la zona a la que corresponde la muestra del final_rutes
def identify_final_rute_location():
    df2 = pd.read_csv("dash2/datasets/final_rutes.csv", dtype={"code": str})
    df['code'] = None
    for i, value in df2.iterrows():
        lat = value['latitude']
        lon = value['longitude']
        zone = str(get_zone(lat, lon))
        df2.at[i, 'code'] = zone
    
    df2.to_csv('dash2/datasets/final_rutes.csv', index=False)