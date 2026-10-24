"""Dos vistas del mapa: fuentes originales y calendario con tratamiento."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .dash_logic import METRICS
from .dash_figures import get_figure, properties_figures, empty_figure
from .rmcab_data import VARIABLES
from .map_scenarios import scenario_noise, variation_rate, SIMULATION_SEED, DEFAULT_VARIATION

ROOT = Path(__file__).resolve().parents[1]
MODES = {'observed': 'Datos originales', 'estimated': 'Datos con tratamiento'}
# Aceptar peticiones de pestañas anteriores hasta que se recarguen; no son
# opciones adicionales del selector.
HISTORICAL_MODES = {*MODES, 'simulated'}
ORIGINS = {1: 'observed_spatial', 2: 'short_gap', 3: 'simulated'}
ORIGIN_LABELS = {'observed_spatial': 'Con mediciones de origen',
                 'short_gap': 'Relleno de hueco corto',
                 'simulated': 'Relleno estimado con variación sintética',
                 'mixed': 'Mediciones y/o rellenos agregados', 'missing': 'Sin datos'}
COLORS = ['#526cc5', '#b74b74', '#648f39', '#a27621', '#7b55a3', '#258c91']


@lru_cache(maxsize=1)
def load_history():
    path = ROOT/'data/maps'
    manifest = json.loads((path/'history_manifest.json').read_text(encoding='utf-8'))
    if manifest['schema_version'] != 2:
        raise ValueError('Reconstruye el paquete del mapa con el procedimiento actualizado.')
    for relative, expected in manifest['input_sha256'].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() != expected:
            raise ValueError('La fuente del mapa cambió; reconstruye el paquete histórico.')
    for name, expected in manifest['output_sha256'].items():
        if hashlib.sha256((path/name).read_bytes()).hexdigest() != expected:
            raise ValueError('El dataset del mapa no coincide con su manifiesto.')
    frame = pd.read_csv(path/'station_daily_2015_2025.csv.gz', dtype={'station_id': 'str'})
    frame['report_date'] = pd.to_datetime(frame.report_date)
    centroids = pd.read_csv(path/'neighborhood_centroids.csv', dtype={'sector_code': 'str'})
    if frame.duplicated(['station_id', 'report_date']).any() or centroids.neighborhood.duplicated().any():
        raise ValueError('Hay claves duplicadas en el mapa.')
    for var in VARIABLES:
        if not np.isfinite(frame[var]).all(): raise ValueError('Base de simulación no finita.')
        if not frame[f'{var}_origin'].isin(['observed_daily_aggregate', 'knn_scenario_baseline']).all():
            raise ValueError('Procedencia desconocida en el calendario.')
        observed = frame[f'{var}_hours'].gt(0)
        if not observed.eq(frame[f'{var}_origin'].eq('observed_daily_aggregate')).all():
            raise ValueError('Las marcas de observación no coinciden con las horas de origen.')
        if not np.allclose(frame.loc[observed, var], frame.loc[observed, f'{var}_short_gap']):
            raise ValueError('El relleno corto modificó una observación.')
    return frame, centroids, manifest


def distances_km(points, stations):
    a = np.radians(points[['latitude', 'longitude']].to_numpy(dtype=float))
    b = np.radians(stations[['latitude', 'longitude']].to_numpy(dtype=float))
    dlat, dlon = a[:, None, 0]-b[None, :, 0], a[:, None, 1]-b[None, :, 1]
    value = np.sin(dlat/2)**2 + np.cos(a[:, None, 0])*np.cos(b[None, :, 0])*np.sin(dlon/2)**2
    return 6371.0088*2*np.arcsin(np.sqrt(np.clip(value, 0, 1)))


def interpolate(values, distances, neighbors=4):
    """Cuatro estaciones disponibles por día; nunca tratar NaN como cero."""
    output = np.full((len(values), len(distances)), np.nan)
    patterns, inverse = np.unique(np.isfinite(values), axis=0, return_inverse=True)
    for pattern_id, available in enumerate(patterns):
        if not available.any(): continue
        dates = np.flatnonzero(inverse == pattern_id)
        current = distances[:, available]
        nearest = np.argsort(current, axis=1)[:, :min(neighbors, available.sum())]
        weights = np.zeros_like(current)
        row = np.arange(len(current))[:, None]
        weights[row, nearest] = 1/np.maximum(current[row, nearest], 0.1)**2
        exact = current.min(axis=1) < 1e-8
        if exact.any(): weights[exact] = (current[exact] < 1e-8).astype(float)
        weights /= weights.sum(axis=1, keepdims=True)
        output[dates] = values[dates][:, available] @ weights.T
    return output


def period(year, month='all'):
    if int(year) not in range(2015, 2026): raise ValueError('Año fuera de 2015–2025.')
    if month in (None, 'all'):
        start, end = pd.Timestamp(int(year), 1, 1), pd.Timestamp(int(year), 12, 31)
    else:
        if int(month) not in range(1, 13): raise ValueError('Mes inválido.')
        start = pd.Timestamp(int(year), int(month), 1)
        end = start+pd.offsets.MonthEnd(0)
    frame, centroids, _ = load_history()
    part = frame.loc[frame.report_date.between(start, end)].copy()
    stations = part.drop_duplicates('station_id').set_index('station_id').sort_index()
    return part, stations, pd.date_range(start, end), centroids


def variable_daily(part, stations, dates, variable, mode):
    if mode not in HISTORICAL_MODES: raise ValueError('Modo histórico no válido.')
    values = part.pivot(index='report_date', columns='station_id', values=variable).reindex(index=dates, columns=stations.index)
    if mode == 'observed':
        counts = part.pivot(index='report_date', columns='station_id', values=f'{variable}_hours').reindex(index=dates, columns=stations.index)
        values = values.where(counts.gt(0))
    return values.to_numpy(dtype=float)


def sector_values(part, stations, dates, points, variable, mode, variation=DEFAULT_VARIATION):
    """Conservar fuentes; el tratamiento completa el resto del calendario."""
    if mode not in HISTORICAL_MODES: raise ValueError('Modo histórico no válido.')
    distances = distances_km(points, stations)
    actual = interpolate(variable_daily(part, stations, dates, variable, 'observed'), distances)
    values = actual.copy()
    kinds = np.where(np.isfinite(actual).any(axis=1), 1, 0)
    if mode in {'estimated', 'simulated'}:
        short_stations = part.pivot(index='report_date', columns='station_id', values=f'{variable}_short_gap').reindex(index=dates, columns=stations.index).to_numpy(dtype=float)
        short = interpolate(short_stations, distances)
        added = (kinds == 0) & np.isfinite(short).any(axis=1)
        values[added], kinds[added] = short[added], 2
    if mode in {'estimated', 'simulated'}:
        rate = variation_rate(variation)
        baseline = interpolate(variable_daily(part, stations, dates, variable, 'simulated'), distances)
        simulated = kinds == 0
        if simulated.any():
            scale = load_history()[2]['simulation']['scale_by_variable'][variable]
            noise = scenario_noise(points.neighborhood.tolist(), dates, variable, rate, scale)
            scenario = baseline + noise
            if variable in {'pm_25', 'pm_10'}: scenario = np.maximum(scenario, 0)
            if variable == 'humidity': scenario = np.clip(scenario, 0, 100)
            values[simulated], kinds[simulated] = scenario[simulated], 3
    return values, kinds


@lru_cache(maxsize=24)
def aggregates(year, month='all', mode='estimated', variation=DEFAULT_VARIATION):
    part, stations, dates, centroids = period(year, month)
    distances = distances_km(centroids, stations)
    result = centroids.copy()
    result['nearest_station_km'] = distances.min(axis=1)
    result['far_reference_station'] = result.nearest_station_km.gt(10)
    result['spatial_origin'] = 'centroid_idw_estimate' if mode == 'observed' else 'idw_with_estimated_and_synthetic_gap_values'
    info = {'calendar_days': len(dates), 'stations': len(stations), 'start': str(dates[0].date()), 'end': str(dates[-1].date()), 'mode': mode}
    for mean, var in METRICS.items():
        values, kinds = sector_values(part, stations, dates, centroids, var, mode, variation)
        counts = np.isfinite(values).sum(axis=0)
        result[mean] = np.divide(np.nansum(values, axis=0), counts, out=np.full(len(centroids), np.nan), where=counts>0)
        result[f'{var}_days'] = counts
        actual = part.loc[part[f'{var}_hours'].gt(0)]
        source_days = int((kinds == 1).sum())
        short_days, sim_days = int((kinds == 2).sum()), int((kinds == 3).sum())
        info[var] = {'source_days': source_days, 'observed_hours': int(actual[f'{var}_hours'].sum()),
                     'represented_days': int((kinds > 0).sum()), 'days_added': short_days + sim_days,
                     'short_gap_days': short_days, 'simulated_days': sim_days,
                     'source_start': str(actual.report_date.min().date()) if len(actual) else None,
                     'source_end': str(actual.report_date.max().date()) if len(actual) else None}
    return result, info


def series(year, month, mode, selected, frequency='Diaria', variation=DEFAULT_VARIATION):
    part, stations, dates, centroids = period(year, month)
    points = centroids.loc[centroids.neighborhood.isin(selected or [])]
    if points.empty: return pd.DataFrame()
    columns = {'datetime': np.tile(dates, len(points)), 'neighborhood': np.repeat(points.neighborhood.to_numpy(), len(dates))}
    for var in VARIABLES:
        values, kinds = sector_values(part, stations, dates, points, var, mode, variation)
        columns[var] = values.T.reshape(-1)
        for code, origin in ORIGINS.items():
            columns[f'{var}_{origin}_days'] = np.tile((kinds == code).astype(int), len(points))
    daily = pd.DataFrame(columns)
    rule = {'Diaria': 'D', 'Semanal': 'W-MON', 'Mensual': 'MS'}[frequency]
    aggregation = {column: ('mean' if column in VARIABLES else 'sum') for column in columns if column not in {'datetime', 'neighborhood'}}
    result = daily.groupby(['neighborhood', pd.Grouper(key='datetime', freq=rule)]).agg(aggregation).reset_index()
    for var in VARIABLES:
        result[f'{var}_origin'] = 'missing'
        counters = [f'{var}_{origin}_days' for origin in ORIGINS.values()]
        for origin in ORIGINS.values():
            result.loc[result[f'{var}_{origin}_days'].gt(0), f'{var}_origin'] = origin
        result.loc[result[counters].gt(0).sum(axis=1).gt(1), f'{var}_origin'] = 'mixed'
    return result


def map_figure(data, variable, counties, selected=None, basemap='color', mode='estimated', variation=DEFAULT_VARIATION):
    if mode == 'legacy':
        data = load_history()[1][['neighborhood']].merge(data, on='neighborhood', how='left', sort=False, validate='one_to_one')
    figure = get_figure(data, variable, counties, selected, basemap)
    names = [feature['properties']['DISPLAY_NAME'] for feature in counties['features']]
    background = go.Choroplethmapbox(geojson=counties, locations=names, featureidkey='properties.DISPLAY_NAME',
        z=[0]*len(names), colorscale=[[0, '#e7e8e1'], [1, '#e7e8e1']], showscale=False,
        marker_opacity=0.7, marker_line_color='#777b75', marker_line_width=0.5,
        hovertemplate='%{location}<br>Sin datos para este periodo<extra></extra>')
    selected_set = set(selected or [])
    background.marker.line.width = [2.5 if name in selected_set else 0.5 for name in names]
    background.marker.line.color = ['#bc3838' if name in selected_set else '#777b75' for name in names]
    figure.add_trace(background)
    figure.data = (figure.data[1], figure.data[0])
    version = load_history()[2]['input_sha256']['dash2/datasets/bogota_cadastral.json'][:16]
    figure.update_traces(geojson=f'/api/maps/geometry/?v={version}')
    metric = METRICS[variable]
    figure.data[1].meta = {'dataset_mode': mode, 'variation_percent': variation_rate(variation) if mode in {'estimated', 'simulated'} else 0,
                         'simulation_seed': SIMULATION_SEED if mode in {'estimated', 'simulated'} else None}
    if mode == 'legacy':
        figure.data[1].update(zauto=True, zmin=None, zmax=None)
        figure.data[1].customdata = [[name.split(',')[0]] for name in data.neighborhood]
        figure.data[1].hovertemplate = '%{customdata[0]}<br>Promedio original: %{z:.2f}<br>Recorridos 2024 · unidades en revisión<extra></extra>'
    else:
        limits = load_history()[2]['color_ranges'][metric]
        figure.data[1].update(zmin=limits[0], zmax=limits[1], zauto=False)
        figure.data[1].customdata = [[row.neighborhood.split(',')[0], round(row.nearest_station_km, 1), int(getattr(row, f'{metric}_days'))] for row in data.itertuples()]
        scope = 'Datos con tratamiento · incluye rellenos estimados y variación sintética' if mode in {'estimated', 'simulated'} else 'Datos originales · estimación espacial IDW con fuentes disponibles'
        figure.data[1].hovertemplate = ('%{customdata[0]}<br>Promedio: %{z:.2f} '+properties_figures[variable][0]
            +'<br>'+scope+'<br>%{customdata[2]} días representados<br>Estación registrada más cercana: %{customdata[1]} km<extra></extra>')
    if not data[variable].notna().any():
        figure.add_annotation(text='Sin datos disponibles · los huecos largos se conservan', x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False, bgcolor='white')
    return figure


def charts(year, month, mode, selected, variable, extras, frequency, variation=DEFAULT_VARIATION):
    if not selected: return empty_figure('Selecciona un sector del mapa'), empty_figure('Selecciona un sector del mapa')
    data = series(year, month, mode, selected, frequency, variation)
    if data.empty: return empty_figure('Selecciona un sector del mapa'), empty_figure('Selecciona un sector del mapa')
    current = METRICS[variable]
    requested = [extras] if isinstance(extras, str) else (extras or [])
    variables = list(dict.fromkeys([current, *[v for v in requested if v in VARIABLES]]))
    figure = make_subplots(rows=len(variables), cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           subplot_titles=[f'{VARIABLES[var][0]} · {VARIABLES[var][1]}' for var in variables])
    names = sorted(data.neighborhood.unique())
    for row, var in enumerate(variables, 1):
        for index, name in enumerate(names):
            group = data.loc[data.neighborhood.eq(name)]
            counters = group[[f'{var}_{kind}_days' for kind in ORIGINS.values()]].to_numpy()
            labels = group[f'{var}_origin'].map(ORIGIN_LABELS)
            details = [list(counts) + [label] for counts, label in zip(counters, labels)]
            color = COLORS[index % len(COLORS)]
            figure.add_trace(go.Scatter(x=group.datetime, y=group[var],
                mode='lines+markers' if mode == 'observed' or frequency != 'Diaria' else 'lines', connectgaps=False,
                line={'color': color}, marker={'color': color, 'size': 4},
                name=name.split(',')[0], legendgroup=name, showlegend=row==1,
                customdata=details, hovertemplate='%{x|%d/%m/%Y}<br>%{y:.2f} '+VARIABLES[var][1]
                +'<br>%{customdata[3]}<br>Días de origen: %{customdata[0]}<br>Relleno corto: %{customdata[1]}<br>Relleno con variación sintética: %{customdata[2]}<extra>%{fullData.name}</extra>'), row=row, col=1)
        figure.update_yaxes(title_text=VARIABLES[var][1], row=row, col=1)
    figure.update_xaxes(tickformat='%d/%m', title_text='Día del reporte', row=len(variables), col=1)
    aggregate, _ = aggregates(year, month, mode, variation)
    chosen = aggregate.loc[aggregate.neighborhood.isin(selected)]
    bars = go.Figure(go.Bar(x=chosen.neighborhood.str.split(',').str[0], y=chosen[variable], marker_color='#827b10',
        hovertemplate='%{x}<br>%{y:.2f} '+VARIABLES[current][1]+'<extra></extra>'))
    for fig in (figure, bars):
        fig.update_layout(autosize=True, template='plotly_white', paper_bgcolor='#f2f2f2', plot_bgcolor='#f2f2f2',
                          font=dict(family='OSWALD-LIGHT, sans-serif', color='#444a3e'), margin=dict(l=55, r=20, t=65, b=70))
    title = 'Datos originales' if mode == 'observed' else 'Datos con tratamiento'
    figure.update_layout(height=max(400, 290*len(variables)), title=title, legend_title='Sectores', legend={'orientation': 'h', 'y': -0.22})
    bars.update_layout(title=f'Promedio por sector · {VARIABLES[current][0]}', yaxis_title=VARIABLES[current][1], xaxis_title='Sector catastral')
    if not data[variables].notna().any().any():
        figure.add_annotation(text='Sin datos para el periodo · huecos largos sin rellenar', x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
    return figure, bars


def export_aggregates(year, month, mode, variation=DEFAULT_VARIATION):
    frame, info = aggregates(year, month, mode, variation)
    result = frame.copy()
    result['year'], result['month'], result['dataset_mode'] = int(year), month, mode
    result['variation_percent'] = variation_rate(variation) if mode in {'estimated', 'simulated'} else 0
    result['simulation_seed'] = SIMULATION_SEED if mode in {'estimated', 'simulated'} else ''
    result['variation_basis'] = 'P95_minus_P5_observed_station_daily_means' if mode in {'estimated', 'simulated'} else ''
    result['calibrated_uncertainty'] = False
    for var in VARIABLES:
        result[f'{var}_unit'] = VARIABLES[var][1]
        result[f'{var}_source_days'] = info[var]['source_days']
        result[f'{var}_calendar_days'] = info['calendar_days']
        result[f'{var}_temporal_days_added'] = info[var]['days_added']
        result[f'{var}_short_gap_days'] = info[var]['short_gap_days']
        result[f'{var}_simulated_days'] = info[var]['simulated_days']
        result[f'{var}_simulation_scale'] = load_history()[2]['simulation']['scale_by_variable'][var] if mode in {'estimated', 'simulated'} else 0
    result['value_scope'] = ('treated_with_estimated_and_synthetic_gaps_not_neighborhood_measurement' if mode in {'estimated', 'simulated'}
                             else 'exploratory_centroid_estimate_not_neighborhood_measurement')
    result['dataset_label'] = 'Datos originales' if mode == 'observed' else 'Datos con tratamiento'
    return result


def figure_update(figure):
    """Enviar valores y estilos; la geometría ya cargada permanece en el cliente."""
    from dash import Patch
    patch = Patch()
    payload = figure.to_plotly_json()
    patch['data'][0]['marker'] = payload['data'][0]['marker']
    for key in ['z', 'colorscale', 'colorbar', 'marker', 'customdata', 'hovertemplate', 'meta', 'zmin', 'zmax', 'zauto']:
        patch['data'][1][key] = payload['data'][1].get(key)
    patch['layout']['annotations'] = payload['layout'].get('annotations', [])
    patch['layout']['mapbox']['style'] = payload['layout']['mapbox']['style']
    return patch
