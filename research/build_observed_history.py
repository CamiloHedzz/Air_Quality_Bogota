"""Une exportaciones SISAIRE verificadas y las muestras RMCAB conservadas."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import unicodedata

import numpy as np
import pandas as pd

from dash2.rmcab_data import VARIABLES,load_samples
from research.air_quality import coverage_by_year
from research.collect_sisaire import validate_export

SISAIRE_TO_LOCAL={'8207':'1','8218':'3','8219':'4','8213':'5','8208':'6','8211':'8','8214':'9','8210':'11',
                  '8216':'13','8215':'17','28202':'24','31834':'26','28203':'27','8212':'30',
                  '31841':'32','31873':'34','31874':'37','31875':'38','31876':'39'}
LEGACY=['data/samples/rmcab_pilot_2015_2025.csv','data/samples/rmcab_2025_q1.csv']


def normalized(value):
    text=unicodedata.normalize('NFKD',str(value)).encode('ascii','ignore').decode().lower()
    return ' '.join(re.sub(r'[^a-z0-9 ]',' ',text).split())


def build(root):
    root=Path(root);cache=root/'.local/research/sisaire'
    if not any(cache.glob('*.sources.json')):cache=root/'data/history/source_exports'
    archives=root/'data/history/source_exports';archives.mkdir(parents=True,exist_ok=True)
    sources=[];pieces={var:[] for var in VARIABLES};excluded={};input_hashes={}
    def source(meta,**extra):
        entry={**meta,**extra,'source_id':len(sources)+1};sources.append(entry);return entry['source_id']
    for manifest in sorted(cache.glob('*.sources.json')):
        meta=json.loads(manifest.read_text(encoding='utf-8'))
        raw=gzip.decompress(manifest.with_name(manifest.name.replace('.sources.json','.csv.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=meta['sha256']: raise ValueError('Exportación SISAIRE alterada.')
        csv_path=manifest.with_name(manifest.name.replace('.sources.json','.csv.gz'))
        for original in [manifest,csv_path]:
            if original.resolve()!=(archives/original.name).resolve():shutil.copy2(original,archives/original.name)
        frame=validate_export(raw,meta['start'],meta['end'],meta['variable'])
        names={normalized(name):SISAIRE_TO_LOCAL[identifier] for identifier,name in meta['station_ids'].items() if identifier in SISAIRE_TO_LOCAL}
        # El antiguo USME (8220) no se confunde con la estación moderna "USME" (31841).
        known=frame.Estacion.map(normalized).isin(names)&frame.Estacion.ne('USME')
        for name,count in frame.loc[~known,'Estacion'].value_counts().items():excluded[str(name)]=excluded.get(str(name),0)+int(count)
        frame=frame.loc[known].copy()
        frame['station_id']=frame.Estacion.map(normalized).map(names)
        frame['datetime']=(pd.to_datetime(frame['Fecha inicial'])+pd.Timedelta(hours=1)).dt.tz_localize('America/Bogota')
        var={'PM2.5':'pm_25','PM10':'pm_10'}[meta['variable']]
        frame[f'{var}_raw']=pd.to_numeric(frame[meta['variable']].replace({'':'NaN'}),errors='raise')
        frame[f'{var}_source_id']=source(meta,kind='SISAIRE_hourly_export',archive_path=f'data/history/source_exports/{csv_path.name}')
        part=frame[['station_id','datetime',f'{var}_raw',f'{var}_source_id']]
        if part.duplicated(['station_id','datetime']).any():raise ValueError('Alias de estación ambiguo en SISAIRE.')
        pieces[var].append(part)
    old=pd.concat([load_samples(root/path) for path in LEGACY],ignore_index=True).drop_duplicates(['station_id','datetime'])
    source_ids={}
    for digest,part in old.groupby('source_sha256'):
        row=part.iloc[0]
        source_ids[str(digest)]=source({'url':row.source_url,'sha256':str(digest),'report_date':str(row.report_date.date()),
                                      'validation_status':'published_quality_not_verified'},kind='RMCAB_hourly_report')
    old_ids=old.source_sha256.map(source_ids)
    index=['station_id','datetime'];wide=None;overlap=[]
    for var in VARIABLES:
        current=pd.concat(pieces[var],ignore_index=True).set_index(index) if pieces[var] else pd.DataFrame(columns=[*index,f'{var}_raw',f'{var}_source_id']).set_index(index)
        if current.index.duplicated().any():raise ValueError('Exportaciones SISAIRE solapadas.')
        legacy=old[index].copy();legacy[f'{var}_raw']=old[f'{var}_raw'] if f'{var}_raw' in old else old[var]
        legacy[f'{var}_source_id']=old_ids
        legacy=legacy.set_index(index)
        joined=current.join(legacy,how='outer',rsuffix='_legacy')
        a,b=[pd.to_numeric(joined[column],errors='raise').astype(float) for column in [f'{var}_raw',f'{var}_raw_legacy']]
        both=a.notna()&b.notna()
        overlap.append({'variable':var,'overlap_rows':int(both.sum()),'different_rows':int((both&~np.isclose(a,b,equal_nan=True)).sum()),
                        'priority':'RMCAB existing valid readings preserved; otherwise SISAIRE'})
        valid=b.between(0,100) if var=='humidity' else b.between(-50,60) if var=='temperature' else b.ge(0)&np.isfinite(b)
        use_legacy=valid|a.isna()
        part=pd.DataFrame({f'{var}_raw':a.where(~use_legacy,b),f'{var}_source_id':joined[f'{var}_source_id'].where(~use_legacy,joined[f'{var}_source_id_legacy'])})
        wide=part if wide is None else wide.join(part,how='outer')
    wide=wide.reset_index()
    for var in VARIABLES:wide[f'{var}_source_id']=pd.to_numeric(wide[f'{var}_source_id'],errors='raise').fillna(0).astype('uint16')
    wide=wide.sort_values(['datetime','station_id'])
    locations=json.loads((root/'data/references/rmcab_station_locations.json').read_text(encoding='utf-8'))
    target=root/'data/history';target.mkdir(parents=True,exist_ok=True)
    blob=gzip.compress(wide.to_csv(index=False,float_format='%.12g',lineterminator='\n').encode('utf-8'),mtime=0)
    (target/'observations.csv.gz').write_bytes(blob)
    for path in LEGACY:input_hashes[path]=hashlib.sha256((root/path).read_bytes()).hexdigest()
    meta={'schema_version':1,'observed_only':True,'rows':len(wide),'observations_sha256':hashlib.sha256(blob).hexdigest(),
          'timezone':'America/Bogota','timestamp_convention':'end_of_hour; report_date=(datetime-1h).date',
          'stations':locations['stations'],'sources':sources,'legacy_input_sha256':input_hashes,'overlap':overlap,
          'station_crosswalk':SISAIRE_TO_LOCAL,'excluded_unmapped_station_rows':excluded,
          'limitations':['Published measurements; final source quality status not independently certified.',
                         'Station mapping by official names; historical relocations not verified.',
                         'Unmapped/ambiguous stations excluded rather than assigned invented coordinates.',
                         'Source files can contain missing hours; complete calendar does not mean complete sensors.']}
    (target/'observations_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8', newline="\n")
    from dash2.history_data import load_observations
    load_observations.cache_clear();data=load_observations(root)
    coverage=coverage_by_year(data);coverage.to_csv(target/'coverage_by_year.csv',index=False, lineterminator="\n")
    meta['coverage']=coverage.to_dict('records');meta['report_days']=int(data.report_date.nunique())
    meta['report_start']=str(data.report_date.min().date());meta['report_end']=str(data.report_date.max().date())
    meta['source_calendar_complete']=meta['report_days']==4018
    (target/'observations_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8', newline="\n")
    return meta


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=parser.parse_args()
    result=build(args.root);print(json.dumps({key:result[key] for key in ['rows','report_days','coverage','overlap']},ensure_ascii=False,indent=2))
