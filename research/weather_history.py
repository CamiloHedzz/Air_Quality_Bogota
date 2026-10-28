"""ERA5 horario para covariables; nunca se convierte en medición de estación.

La malla nativa se solicita sin ajuste de elevación, se guarda una sola vez por
celda y se relaciona con las estaciones mediante una tabla explícita.
"""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

ENDPOINT = 'https://archive-api.open-meteo.com/v1/archive'
DOCS = 'https://open-meteo.com/en/docs/historical-weather-api'
CHANNELS = {'temperature_2m': 'temperature', 'relative_humidity_2m': 'humidity',
            'precipitation': 'precipitation', 'wind_speed_10m': 'wind_speed',
            'wind_direction_10m': 'wind_direction'}
UNITS = {'temperature_2m': '°C', 'relative_humidity_2m': '%', 'precipitation': 'mm',
         'wind_speed_10m': 'm/s', 'wind_direction_10m': '°'}
ZONE = 'America/Bogota'


def grid_reference(stations):
    rows = []
    for station in stations:
        lat, lon = [round(float(station[key]) * 4) / 4 for key in ('latitude', 'longitude')]
        rows.append({**station, 'grid_id': f'era5_{lat:.2f}_{lon:.2f}',
                     'grid_latitude': lat, 'grid_longitude': lon})
    mapping = pd.DataFrame(rows)
    grids = mapping[['grid_id', 'grid_latitude', 'grid_longitude']].drop_duplicates().sort_values('grid_id').reset_index(drop=True)
    return mapping, grids


def parse_weather(raw, grids, start, end):
    payload = json.loads(raw)
    payload = payload if isinstance(payload, list) else [payload]
    if len(payload) != len(grids): raise ValueError('Número de celdas meteorológicas inesperado.')
    expected = pd.date_range(start, pd.Timestamp(end) + pd.Timedelta(days=1), freq='h', inclusive='left', tz=ZONE)
    frames = []
    for item, grid in zip(payload, grids.itertuples()):
        if item.get('timezone') != ZONE or item.get('utc_offset_seconds') != -18000:
            raise ValueError('La meteorología no usa la zona horaria de Bogotá.')
        if any(item.get('hourly_units', {}).get(key) != unit for key, unit in UNITS.items()):
            raise ValueError('Unidad meteorológica desconocida.')
        if abs(item['latitude'] - grid.grid_latitude) > .02 or abs(item['longitude'] - grid.grid_longitude) > .02:
            raise ValueError('La API devolvió otra celda ERA5.')
        hourly = item['hourly']
        dates = pd.DatetimeIndex(pd.to_datetime(hourly['time'])).tz_localize(ZONE)
        if not dates.equals(expected): raise ValueError('Horas ausentes, duplicadas o fuera del periodo solicitado.')
        frame = pd.DataFrame({'datetime': dates, 'grid_id': grid.grid_id})
        for channel, variable in CHANNELS.items():
            values = pd.to_numeric(pd.Series(hourly[channel]), errors='raise')
            if len(values) != len(expected) or not np.isfinite(values).all():
                raise ValueError(f'Reanálisis no finito: {channel}.')
            if variable == 'humidity' and not values.between(0, 100).all(): raise ValueError('HR ERA5 fuera de rango.')
            if variable in {'precipitation', 'wind_speed'} and values.lt(0).any(): raise ValueError('Lluvia/viento negativos.')
            frame[variable] = values.to_numpy()
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def collect_year(year, grids, cache, *, network=False):
    start, end = f'{year}-01-01', f'{year}-12-31' if year < 2025 else '2026-01-01'
    params = {'latitude': ','.join(grids.grid_latitude.astype(str)),
              'longitude': ','.join(grids.grid_longitude.astype(str)), 'start_date': start, 'end_date': end,
              'hourly': ','.join(CHANNELS), 'models': 'era5', 'timezone': ZONE, 'wind_speed_unit': 'ms',
              'elevation': ','.join(['nan'] * len(grids)), 'cell_selection': 'nearest'}
    url = ENDPOINT + '?' + urlencode(params)
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    content, manifest = cache / f'{year}_{key}.json.gz', cache / f'{year}_{key}.sources.json'
    if content.exists() and manifest.exists():
        raw, meta = gzip.decompress(content.read_bytes()), json.loads(manifest.read_text(encoding='utf-8'))
        if hashlib.sha256(raw).hexdigest() != meta['sha256']: raise ValueError('La caché ERA5 cambió.')
    else:
        if not network: raise FileNotFoundError(f'Falta ERA5 {year}; ejecutar con --network.')
        request = Request(url, headers={'User-Agent': 'AirQualityBogotaResearch/0.2 (cached sequential research)'})
        with urlopen(request, timeout=90) as response: raw = response.read(20_000_001)
        if len(raw) > 20_000_000: raise ValueError('Respuesta ERA5 demasiado grande.')
        parse_weather(raw, grids, start, end)
        meta = {'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'year': year,
                'downloaded_at_utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(raw)}
        content.write_bytes(gzip.compress(raw, mtime=0))
        manifest.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8', newline="\n")
        time.sleep(2)
    return parse_weather(raw, grids, start, end), meta


def build(root, *, network=False, progress=print):
    root = Path(root)
    reference = root / 'data/references/rmcab_station_locations.json'
    mapping, grids = grid_reference(json.loads(reference.read_text(encoding='utf-8'))['stations'])
    frames, sources = [], []
    for year in range(2015, 2026):
        data, source = collect_year(year, grids, root / '.local/research/era5', network=network)
        frames.append(data); sources.append(source)
        progress(f'ERA5 {year}: {len(data):,} horas/celda, {len(grids)} celdas', flush=True)
    data = pd.concat(frames, ignore_index=True)
    start, end = pd.Timestamp('2015-01-01', tz=ZONE), pd.Timestamp('2026-01-01', tz=ZONE)
    data = data.loc[data.datetime.gt(start) & data.datetime.le(end)].sort_values(['grid_id', 'datetime'])
    if data.duplicated(['grid_id', 'datetime']).any(): raise ValueError('Hora/celda ERA5 repetida.')
    target = root / 'data/weather'; target.mkdir(parents=True, exist_ok=True)
    blob = gzip.compress(data.to_csv(index=False, float_format='%.3f', lineterminator='\n').encode('utf-8'), mtime=0)
    (target / 'era5_hourly_2015_2025.csv.gz').write_bytes(blob)
    mapping[['station_id', 'grid_id', 'grid_latitude', 'grid_longitude']].to_csv(target / 'station_grids.csv', index=False, lineterminator="\n")
    meta = {'schema_version': 1, 'source': 'Open-Meteo / ECMWF ERA5', 'documentation': DOCS,
            'record_type': 'weather_reanalysis', 'timezone': ZONE, 'grid_resolution_degrees': .25,
            'elevation_downscaling': False, 'station_coordinates_scope': 'fixed_reference_positions',
            'report_start': '2015-01-01', 'report_end': '2025-12-31', 'rows': len(data),
            'grid_cells': grids.to_dict('records'), 'station_count': len(mapping),
            'hours_per_grid': int(data.datetime.nunique()), 'units': dict(zip(CHANNELS.values(), UNITS.values())),
            'output_sha256': {'era5_hourly_2015_2025.csv.gz': hashlib.sha256(blob).hexdigest(),
                              'station_grids.csv': hashlib.sha256((target / 'station_grids.csv').read_bytes()).hexdigest()},
            'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(), 'sources': sources,
            'limitations': ['Reanalysis on a coarse grid, not a measured neighborhood or station value.',
                            'Retrospective data with publication delay; not archived live weather forecasts.',
                            'No historical station relocation validation.'],
            'attribution': 'Weather data by Open-Meteo.com; ERA5 by ECMWF / Copernicus Climate Change Service.'}
    (target / 'era5_manifest.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8', newline="\n")
    return meta


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(build(args.root, network=args.network), ensure_ascii=False, indent=2))
