"""Contrato compacto de observaciones publicadas; ningún relleno es una etiqueta."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .rmcab_data import VARIABLES, load_samples

ROOT = Path(__file__).resolve().parents[1]
LEGACY_INPUTS = ['data/samples/rmcab_pilot_2015_2025.csv', 'data/samples/rmcab_2025_q1.csv']


def source_paths(root=ROOT):
    root=Path(root)
    return ['data/history/observations.csv.gz','data/history/observations_manifest.json'] if (root/'data/history/observations_manifest.json').exists() else LEGACY_INPUTS


@lru_cache(maxsize=1)
def load_observations(root=ROOT):
    root=Path(root)
    path=root/'data/history/observations_manifest.json'
    if not path.exists():
        data=pd.concat([load_samples(root/p) for p in LEGACY_INPUTS],ignore_index=True)
        duplicates=data.loc[data.duplicated(['station_id','datetime'],keep=False)]
        if len(duplicates) and duplicates.groupby(['station_id','datetime'])[[*VARIABLES,'source_sha256']].nunique(dropna=False).gt(1).any().any():
            raise ValueError('Las muestras solapadas no coinciden.')
        return data.drop_duplicates(['station_id','datetime']).sort_values('datetime').reset_index(drop=True)
    meta=json.loads(path.read_text(encoding='utf-8'))
    if meta.get('schema_version')!=1 or meta.get('observed_only') is not True: raise ValueError('Contrato histórico desconocido.')
    data_path=root/'data/history/observations.csv.gz'
    if hashlib.sha256(data_path.read_bytes()).hexdigest()!=meta['observations_sha256']: raise ValueError('El histórico no coincide con su manifiesto.')
    data=pd.read_csv(data_path,dtype={'station_id':'string',**{f'{v}_source_id':'uint16' for v in VARIABLES}})
    data['datetime']=pd.to_datetime(data.datetime,utc=True).dt.tz_convert('America/Bogota')
    data['report_date']=(data.datetime-pd.Timedelta(hours=1)).dt.tz_localize(None).dt.normalize()
    if data.duplicated(['station_id','datetime']).any(): raise ValueError('Observaciones de estación/hora duplicadas.')
    stations={str(s['station_id']):s['station_name'] for s in meta['stations']}
    data['station_name']=data.station_id.map(stations).astype('category')
    if data.station_name.isna().any(): raise ValueError('Estación histórica sin referencia.')
    data['station_label']=data.station_name.astype('string').str.title().astype('category')
    sources={int(s['source_id']):s for s in meta['sources']}
    ids=set(sources)|{0}
    for var in VARIABLES:
        values=pd.to_numeric(data[f'{var}_raw'],errors='raise')
        source=data[f'{var}_source_id']
        if not set(source.unique()).issubset(ids): raise ValueError('Procedencia histórica desconocida.')
        if (values.notna() & source.eq(0)).any(): raise ValueError('Valor histórico sin fuente.')
        valid=values.between(0,100) if var=='humidity' else values.between(-50,60) if var=='temperature' else values.ge(0)&np.isfinite(values)
        data[var]=values.where(valid)
        data[f'{var}_origin']=pd.Categorical(np.select([values.isna(),valid],['missing','observed'],default='range_review'))
        data[f'{var}_source_sha256']=source.map({i:s['sha256'] for i,s in sources.items()}).fillna('').astype('category')
        data[f'{var}_source_url']=source.map({i:s['url'] for i,s in sources.items()}).fillna('').astype('category')
    first_source=pd.Series(0,index=data.index,dtype='uint16')
    for var in VARIABLES: first_source=first_source.where(first_source.ne(0),data[f'{var}_source_id'])
    data['source_url']=first_source.map({i:s['url'] for i,s in sources.items()}).astype('category')
    data['source_sha256']=first_source.map({i:s['sha256'] for i,s in sources.items()}).astype('category')
    data['record_type']=pd.Categorical(['station_observation']*len(data))
    data['validation_status']=pd.Categorical(['published_quality_not_verified']*len(data))
    data['pm25_above_pm10_review']=data.pm_25.gt(data.pm_10)
    return data.sort_values(['datetime','station_id']).reset_index(drop=True)


def observation_metadata(root=ROOT):
    path=Path(root)/'data/history/observations_manifest.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
