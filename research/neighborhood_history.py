"""Paquete exploratorio para el mapa: agregados diarios, KNN temporal y geometrías.

Los valores completados nunca se presentan como observaciones ni se publican al
paquete HGB. La reconstrucción retrospectiva usa datos anteriores y posteriores.
"""
from datetime import datetime, timezone
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.neighbors import KNeighborsRegressor

from dash2.rmcab_data import VARIABLES
from dash2.history_data import load_observations, source_paths
from dash2.weather_data import daily_station_weather
from dash2.map_scenarios import fill_short_gaps, SHORT_GAP_DAYS, SIMULATION_SEED, AR_COEFFICIENT

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://www.ambientebogota.gov.co/es/web/sda/estaciones-rmcab'
INPUTS = ['data/samples/rmcab_pilot_2015_2025.csv', 'data/samples/rmcab_2025_q1.csv']
ALIASES = {'usaquen': '1', 'suba': '11', 'puente aranda': '13', 'minambiente': '17',
           'san cristobal': '24', 'bolivia': '27', 'carvajal sevillana': '3', 'tunal': '4',
           'centro de alto rendimiento': '5', 'las ferias': '6', 'guaymaral': '8', 'kennedy': '9',
           'estacion movil 7ma': '26', 'fontibon': '30', 'usme': '32', 'el jazmin': '34',
           'ciudad bolivar': '37', 'colina': '38', 'movil fontibon': '39'}


def normalized(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', value).split())


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.row, self.cell = [], None, None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.depth += 1
            return
        if self.depth != 1: return
        if tag == 'tr': self.row = []
        if tag in {'td', 'th'} and self.row is not None: self.cell = []

    def handle_data(self, text):
        if self.cell is not None: self.cell.append(text)

    def handle_endtag(self, tag):
        if tag == 'table':
            self.depth -= 1
            return
        if self.depth != 1: return
        if tag in {'td', 'th'} and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def dms(value):
    parts = re.findall(r'\d+(?:\.\d+)?', value)
    if len(parts) != 3: raise ValueError(f'Coordenada no reconocida: {value}')
    degrees, minutes, seconds = map(float, parts)
    return (-1 if re.search('[WSO]', value.upper()) else 1) * (degrees + minutes/60 + seconds/3600)


def station_locations(*, network=False, root=ROOT):
    path = root / 'data/references/rmcab_station_locations.json'
    if path.exists(): return json.loads(path.read_text(encoding='utf-8'))
    if not network: raise FileNotFoundError('Falta la referencia de estaciones; ejecutar una vez con --network.')
    cache = root / '.local/research/station_locations.html.gz'
    if cache.exists(): raw = gzip.decompress(cache.read_bytes())
    else:
        request = Request(SOURCE, headers={'User-Agent': 'AirQualityBogotaResearch/0.1 (station reference; cached)'})
        with urlopen(request, timeout=45) as response: raw = response.read(4_000_001)
    if len(raw) > 4_000_000: raise ValueError('Respuesta de estaciones demasiado grande.')
    parser = Tables()
    try: text = raw.decode('utf-8')
    except UnicodeDecodeError: text = raw.decode('cp1252')
    parser.feed(text)
    stations = []
    for row in parser.rows:
        if len(row) < 4 or normalized(row[0]) not in ALIASES: continue
        coordinates = [cell for cell in row if '°' in cell]
        if len(coordinates) != 2: continue
        stations.append({'station_id': ALIASES[normalized(row[0])], 'station_name': row[0],
                         'latitude': dms(coordinates[0]), 'longitude': dms(coordinates[1]),
                         'latitude_dms': coordinates[0], 'longitude_dms': coordinates[1]})
    if {p['station_id'] for p in stations} != set(ALIASES.values()):
        raise ValueError(f'La tabla oficial no permite ubicar todas las estaciones: {stations}')
    payload = {'source_url': SOURCE, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
               'source_sha256': hashlib.sha256(raw).hexdigest(),
               'position_scope': 'fixed_reference_positions_historical_relocations_not_verified',
               'stations': sorted(stations, key=lambda p: int(p['station_id']))}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    cache = root / '.local/research/station_locations.html.gz'
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(gzip.compress(raw, mtime=0))
    return payload


def observations(root=ROOT):
    return load_observations(root)


def daily_observations(raw, locations):
    aggregation = {var: (var, 'mean') for var in VARIABLES}
    aggregation.update({f'{var}_hours': (var, 'count') for var in VARIABLES})
    aggregation.update(source_sha256=('source_sha256', 'first'), source_url=('source_url', 'first'))
    daily = raw.groupby(['station_id', 'report_date'], as_index=False).agg(**aggregation)
    daily = daily.loc[daily[list(VARIABLES)].notna().any(axis=1)]
    coords = pd.DataFrame(locations['stations'])[['station_id', 'station_name', 'latitude', 'longitude']]
    return daily.merge(coords, on='station_id', how='left', validate='many_to_one')


def features(frame):
    day = frame.report_date.dt.dayofyear.to_numpy()
    phase = 2*np.pi*day/365.25
    # Escalas explícitas fijadas antes de la comprobación temporal; no se ajustan
    # con el test. Son una hipótesis exploratoria, no distancias ambientales.
    return np.column_stack([(frame.latitude.to_numpy()-4.65)/0.06,
                            (frame.longitude.to_numpy()+74.1)/0.06,
                            (frame.report_date.dt.year.to_numpy()-2015)/3,
                            0.5*np.sin(phase), 0.5*np.cos(phase)])


def complete_calendar(daily, start='2015-01-01', end='2025-12-31'):
    blocks = []
    for year in range(pd.Timestamp(start).year, pd.Timestamp(end).year+1):
        present = daily.loc[daily.report_date.dt.year.eq(year)]
        station_ids = sorted(present.station_id.unique(), key=int)
        dates = pd.date_range(max(pd.Timestamp(start), pd.Timestamp(year, 1, 1)), min(pd.Timestamp(end), pd.Timestamp(year, 12, 31)))
        blocks.append(pd.MultiIndex.from_product([station_ids, dates], names=['station_id', 'report_date']).to_frame(index=False))
    grid = pd.concat(blocks, ignore_index=True)
    metadata = daily.drop_duplicates('station_id')[['station_id', 'station_name', 'latitude', 'longitude']]
    values = daily.drop(columns=['station_name', 'latitude', 'longitude'])
    grid = grid.merge(values, on=['station_id', 'report_date'], how='left', validate='one_to_one').merge(metadata, on='station_id', validate='many_to_one')
    for var in VARIABLES:
        training = daily.loc[daily[var].notna()]
        if training.empty: raise ValueError(f'No hay ejemplos para {var}.')
        # Conservar un contrato independiente para el relleno corto: nunca
        # reutiliza la base KNN ni rellena parte de un tramo largo.
        grid[f'{var}_short_gap'] = grid.groupby('station_id')[var].transform(fill_short_gaps)
        missing = grid[var].isna()
        grid[f'{var}_origin'] = np.where(missing, 'knn_scenario_baseline', 'observed_daily_aggregate')
        grid[f'{var}_hours'] = grid[f'{var}_hours'].fillna(0).astype('int16')
        model = KNeighborsRegressor(n_neighbors=min(5, len(training)), weights='distance', algorithm='kd_tree', n_jobs=1)
        model.fit(features(training), training[var])
        query = features(grid.loc[missing])
        if len(query):
            grid.loc[missing, var] = model.predict(query)
            indices = model.kneighbors(query, return_distance=False)
            training_days = training.report_date.to_numpy(dtype='datetime64[D]')
            gaps = np.abs(training_days[indices] - grid.loc[missing, 'report_date'].to_numpy(dtype='datetime64[D]')[:, None]).astype('timedelta64[D]').astype(int)
            grid.loc[missing, f'{var}_neighbor_gap_days'] = gaps.max(axis=1)
        grid[f'{var}_neighbor_gap_days'] = grid[f'{var}_neighbor_gap_days'].fillna(0).astype('int16')
        if var in {'pm_25', 'pm_10'} and grid[var].lt(0).any(): raise ValueError('Concentración negativa.')
        if var == 'humidity' and not grid[var].between(0, 100).all(): raise ValueError('Humedad fuera del rango físico.')
    grid['record_type'] = 'exploratory_station_day_calendar'
    return grid.sort_values(['report_date', 'station_id']).reset_index(drop=True)


def temporal_check(daily):
    # Un bloqueo de fechas posterior al corte: ninguna etiqueta del bloque se
    # usa al ajustar KNN. No valida los meses/años ausentes ni los barrios.
    train = daily.loc[daily.report_date.le('2025-03-21')]
    test = daily.loc[daily.report_date.between('2025-03-25', '2025-03-31')]
    records = []
    for var in VARIABLES:
        a, b = train.loc[train[var].notna()], test.loc[test[var].notna()]
        model = KNeighborsRegressor(n_neighbors=min(5, len(a)), weights='distance', algorithm='kd_tree', n_jobs=1)
        model.fit(features(a), a[var])
        predicted = model.predict(features(b))
        baseline = b.station_id.map(a.sort_values('report_date').drop_duplicates('station_id', keep='last').set_index('station_id')[var]).fillna(a[var].mean())
        records.append({'variable': var, 'unit': VARIABLES[var][1], 'n': len(b),
                        'mae': float(mean_absolute_error(b[var], predicted)),
                        'rmse': float(np.sqrt(mean_squared_error(b[var], predicted))),
                        'baseline_last_available_mae': float(mean_absolute_error(b[var], baseline)),
                        'train_report_end': '2025-03-21', 'test_report_start': '2025-03-25', 'test_report_end': '2025-03-31'})
    return records


def geometry_centroid(geometry):
    polygons = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
    components = []
    for polygon in polygons:
        for index, coordinates in enumerate(polygon):
            ring = np.asarray(coordinates, dtype=float)
            x, y = ring[:, 0], ring[:, 1]
            # Trasladar cerca de cero evita cancelación de áreas pequeñas.
            ox, oy = x[0], y[0]
            x, y = x-ox, y-oy
            cross = x*np.roll(y, -1)-np.roll(x, -1)*y
            twice_area = cross.sum()
            if abs(twice_area) > 1e-15:
                cx = ((x+np.roll(x, -1))*cross).sum()/(3*twice_area)+ox
                cy = ((y+np.roll(y, -1))*cross).sum()/(3*twice_area)+oy
                components.append((abs(twice_area)*(1 if index == 0 else -1), cx, cy))
    if not components: raise ValueError('Geometría sin área para calcular un centroide.')
    weight = sum(c[0] for c in components)
    return sum(c[0]*c[1] for c in components)/weight, sum(c[0]*c[2] for c in components)/weight


def build(*, network=False, root=ROOT):
    location = station_locations(network=network, root=root)
    raw = observations(root)
    daily = daily_observations(raw, location)
    completed = complete_calendar(daily)
    weather = daily_station_weather(root).rename(columns={v: f'{v}_era5' for v in ['temperature', 'humidity']})
    completed = completed.merge(weather, on=['station_id', 'report_date'], how='left', validate='one_to_one')
    for var in ['temperature', 'humidity']:
        use = completed[f'{var}_origin'].ne('observed_daily_aggregate') & completed[f'{var}_era5'].notna()
        completed.loc[use, var] = completed.loc[use, f'{var}_era5']
        completed.loc[use, f'{var}_origin'] = 'weather_reanalysis'
    completed = completed.drop(columns=['temperature_era5', 'humidity_era5'])
    target = root/'data/maps'
    target.mkdir(parents=True, exist_ok=True)
    csv = completed.to_csv(index=False, float_format='%.8f', lineterminator='\n').encode('utf-8')
    (target/'station_daily_2015_2025.csv.gz').write_bytes(gzip.compress(csv, mtime=0))
    geo_path = root/'dash2/datasets/bogota_cadastral.json'
    geo = json.loads(geo_path.read_text(encoding='utf-8'))
    centroids = []
    for feature in geo['features']:
        longitude, latitude = geometry_centroid(feature['geometry'])
        centroids.append({'neighborhood': feature['properties']['DISPLAY_NAME'],
                          'sector_code': feature['properties']['scacodigo'], 'longitude': longitude, 'latitude': latitude})
    pd.DataFrame(centroids).to_csv(target/'neighborhood_centroids.csv', index=False, float_format='%.8f')
    coverage = []
    for year, group in completed.groupby(completed.report_date.dt.year):
        item = {'year': int(year), 'calendar_days': int(group.report_date.nunique()), 'reference_stations': int(group.station_id.nunique())}
        for var in VARIABLES:
            observed = group[f'{var}_hours'].gt(0)
            item[var] = {'observed_hours': int(group[f'{var}_hours'].sum()), 'source_days': int(group.loc[observed, 'report_date'].nunique()),
                         'station_days_observed': int(observed.sum()), 'station_days_reconstructed': int((~observed).sum())}
        coverage.append(item)
    manifest = {'schema_version': 2, 'mode': 'original_and_treated_calendar',
                'calendar_start': '2015-01-01', 'calendar_end': '2025-12-31', 'neighborhoods': len(centroids),
                'station_days': len(completed), 'source_reports': int(raw.report_date.nunique()),
                'units': {var: meta[1] for var, meta in VARIABLES.items()},
                'color_ranges': {var: ([0, 100] if var == 'humidity' else
                                      [0, float(np.ceil(completed[var].max()/10)*10)] if var in {'pm_25', 'pm_10'} else
                                      [float(np.floor(completed[var].min())), float(np.ceil(completed[var].max()))]) for var in VARIABLES},
                'temporal_method': 'KNeighborsRegressor', 'neighbors': 5, 'weights': 'distance',
                'features': ['latitude/0.06', 'longitude/0.06', 'year/3', 'annual_sin*0.5', 'annual_cos*0.5'],
                'knn_scope': 'baseline_for_treated_gaps_not_used_for_HGB',
                'product_modes': {'observed': 'Datos originales', 'estimated': 'Datos con tratamiento'},
                'default_mode': 'estimated',
                'short_gap_method': {'method': 'linear_between_observations', 'max_consecutive_days': SHORT_GAP_DAYS, 'extrapolate': False},
                'simulation': {'seed': SIMULATION_SEED, 'generator': 'PCG64_SHA256_per_sector_variable',
                               'ar_coefficient': AR_COEFFICIENT, 'kernel_days': 21, 'common_weight': 0.5,
                               'variation_percent_default': 10, 'variation_percent_max': 30,
                               'scale': 'P95_minus_P5_observed_station_daily_means',
                               'scale_by_variable': {var: float(daily[var].quantile(.95)-daily[var].quantile(.05)) for var in VARIABLES},
                               'applies_to': 'days_without_observed_or_short_gap_spatial_values',
                               'calibrated_uncertainty': False, 'cross_variable_physical_consistency_validated': False},
                'spatial_method': 'centroid_IDW', 'spatial_neighbors': 4, 'idw_power': 2,
                'spatial_distance_floor_km': 0.1, 'far_station_flag_km': 10,
                'uses_future_observations_for_reconstruction': True, 'used_to_train_forecast_model': False,
                'intervals_available': False, 'station_positions_scope': location['position_scope'],
                'reanalysis': {'source': 'Open-Meteo / ECMWF ERA5', 'resolution_degrees': .25, 'variables': ['temperature', 'humidity'], 'synthetic_noise_applied': False},
                'limitations': ['Published PM hours have sensor gaps; consult observed coverage by year.',
                               'ERA5 weather is retrospective coarse-grid reanalysis, not a station measurement.',
                               'Original mode preserves gaps; treated mode includes estimated and synthetic gap values.',
                               'Random variation is a user-selected scenario amplitude, not calibrated uncertainty.',
                               'KNN has no weekday features; annual/calendar features remain an unvalidated simulation baseline.',
                               'Centroid IDW is not a measured neighborhood mean or area-weighted polygon average.',
                               'No terrain/emissions model or historical station relocation validation.',
                               'Days and sensors with few source hours remain partial daily aggregates.'],
                'coverage': coverage, 'temporal_check': temporal_check(daily),
                'input_sha256': {path: hashlib.sha256((root/path).read_bytes()).hexdigest() for path in [*source_paths(root), 'data/weather/era5_hourly_2015_2025.csv.gz', 'data/weather/station_grids.csv', 'data/weather/era5_manifest.json', 'data/references/rmcab_station_locations.json', 'dash2/datasets/bogota_cadastral.json']},
                'output_sha256': {name: hashlib.sha256((target/name).read_bytes()).hexdigest() for name in ['station_daily_2015_2025.csv.gz', 'neighborhood_centroids.csv']}}
    (target/'history_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--network', action='store_true')
    args = parser.parse_args()
    result = build(network=args.network)
    print(json.dumps({key: result[key] for key in ['mode', 'source_reports', 'station_days', 'neighborhoods', 'temporal_check']}, ensure_ascii=False, indent=2))
