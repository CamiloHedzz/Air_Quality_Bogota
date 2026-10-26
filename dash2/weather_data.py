"""Reanálisis local verificado; independiente de las observaciones de PM."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
FEATURES=['weather_temperature','weather_humidity','weather_precipitation','weather_wind_speed','weather_wind_sin','weather_wind_cos']


@lru_cache(maxsize=1)
def load_weather(root=ROOT):
    folder=Path(root)/'data/weather'
    meta=json.loads((folder/'era5_manifest.json').read_text(encoding='utf-8'))
    if meta.get('record_type')!='weather_reanalysis' or meta.get('schema_version')!=1: raise ValueError('Contrato ERA5 desconocido.')
    for name,digest in meta['output_sha256'].items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=digest: raise ValueError('El reanálisis cambió desde su preparación.')
    data=pd.read_csv(folder/'era5_hourly_2015_2025.csv.gz',dtype={'grid_id':'category'})
    data['datetime']=pd.to_datetime(data.datetime,utc=True).dt.tz_convert('America/Bogota')
    if data.duplicated(['grid_id','datetime']).any() or not np.isfinite(data[['temperature','humidity','precipitation','wind_speed','wind_direction']]).all().all():
        raise ValueError('Horas/celdas duplicadas o valores no finitos en ERA5.')
    mapping=pd.read_csv(folder/'station_grids.csv',dtype={'station_id':'string'})
    return data,mapping,meta


def enrich_predictors(observations,root=ROOT):
    weather,mapping,_=load_weather(root)
    weather=weather.rename(columns={v:'weather_'+v for v in ['temperature','humidity','precipitation','wind_speed','wind_direction']})
    joined=observations.merge(mapping[['station_id','grid_id']],on='station_id',how='left',validate='many_to_one')
    joined=joined.merge(weather,on=['grid_id','datetime'],how='left',validate='many_to_one').drop(columns='grid_id')
    angle=np.deg2rad(joined.pop('weather_wind_direction'))
    joined['weather_wind_sin'],joined['weather_wind_cos']=np.sin(angle),np.cos(angle)
    return joined


def daily_station_weather(root=ROOT):
    weather,mapping,_=load_weather(root)
    data=weather[['datetime','grid_id','temperature','humidity']].copy()
    data['report_date']=(data.datetime-pd.Timedelta(hours=1)).dt.tz_localize(None).dt.normalize()
    daily=data.groupby(['grid_id','report_date'],observed=True,as_index=False)[['temperature','humidity']].mean()
    return mapping[['station_id','grid_id']].merge(daily,on='grid_id',validate='many_to_many').drop(columns='grid_id')


def analysis_period(observations,start,end,stations,root=ROOT):
    """Completa solo clima del periodo consultado; PM y lecturas válidas intactos."""
    weather,mapping,meta=load_weather(root)
    times=pd.date_range(start,end,freq='h')
    keys=pd.MultiIndex.from_product([stations,times],names=['station_id','datetime']).to_frame(index=False)
    actual=observations.loc[observations.station_id.isin(stations)&observations.datetime.between(start,end)]
    result=keys.merge(actual,on=['station_id','datetime'],how='left',validate='one_to_one')
    context=keys.merge(mapping[['station_id','grid_id']],on='station_id',how='left',validate='many_to_one')
    context=context.merge(weather[['grid_id','datetime','temperature','humidity']],on=['grid_id','datetime'],how='left',validate='many_to_one')
    for var in ['temperature','humidity']:
        use=result[var].isna()&context[var].notna()
        result.loc[use,var]=context.loc[use,var].to_numpy()
        for field,value in [(f'{var}_origin','weather_reanalysis'),(f'{var}_source_url',meta['documentation']),
                            (f'{var}_source_sha256',meta['output_sha256']['era5_hourly_2015_2025.csv.gz'])]:
            result[field]=result[field].astype(object)
            result.loc[use,field]=value
    labels=observations.drop_duplicates('station_id').set_index('station_id')
    for field in ['station_name','station_label']:
        result[field]=result[field].astype(object).fillna(result.station_id.map(labels[field].astype(object)))
    result['report_date']=(result.datetime-pd.Timedelta(hours=1)).dt.tz_localize(None).dt.normalize()
    for var in ['pm_25','pm_10','temperature','humidity']:
        field=f'{var}_origin';result[field]=result[field].astype(object).fillna('missing')
        for kind in ['url','sha256']:
            field=f'{var}_source_{kind}';result[field]=result[field].astype(object).fillna('')
    for field,value in [('source_url',meta['documentation']),('source_sha256',meta['output_sha256']['era5_hourly_2015_2025.csv.gz']),
                        ('record_type','weather_context'),('validation_status','weather_reanalysis')]:
        result[field]=result[field].astype(object).fillna(value)
    return result
