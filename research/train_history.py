"""HGB multianual: desarrollo 2024, prueba final estacional 2025, PM observado.

ERA5 es un predictor retrospectivo identificado; no se afirma disponibilidad en
tiempo real. Ninguna etiqueta ni rezago de PM proviene del mapa o de una imputación.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from threadpoolctl import threadpool_limits

from dash2.history_data import load_observations,source_paths
from dash2.weather_data import enrich_predictors,FEATURES
from research.air_quality import VARIABLES
from research.forecast_experiment import MODEL_PARAMS,feature_columns,observed_forecast_table,summarize_predictions


def evaluation_days(year):
    return [pd.Timestamp(year,month,day) for month in (1,4,7,10) for day in range(15,22)]


def split_history(frame,year):
    cutoff=pd.Timestamp(year,1,1,tz='America/Bogota')
    train=frame.loc[frame.datetime.lt(cutoff)&frame.target_datetime.lt(cutoff)]
    report=(frame.target_datetime-pd.Timedelta(hours=1)).dt.tz_localize(None).dt.normalize()
    test=frame.loc[report.isin(evaluation_days(year))&frame.datetime.ge(cutoff)]
    test=test.loc[test.station_id.isin(train.station_id.unique())]
    if train.empty or test.empty:raise ValueError(f'No hay soporte observado para el corte {year}.')
    if not train.target_datetime.max()<test.datetime.min():raise AssertionError('Fuga temporal en el corte multianual.')
    return train,test


def history_model(target):
    columns=feature_columns(target)+FEATURES
    transform=ColumnTransformer([('station',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=np.nan),['station_id']),
                                 ('numeric','passthrough',columns[1:])])
    return Pipeline([('features',transform),('model',HistGradientBoostingRegressor(categorical_features=[0],**MODEL_PARAMS))])


def train(root):
    root=Path(root);report=root/'data/reports/hgb_2015_2025';report.mkdir(parents=True,exist_ok=True)
    processed=root/'data/processed';processed.mkdir(parents=True,exist_ok=True)
    source=load_observations(root)
    keep=['datetime','station_id','station_name',*VARIABLES,*[f'{v}_origin' for v in VARIABLES],
          'source_url','source_sha256',*[f'{v}_source_{kind}' for v in ('pm_25','pm_10') for kind in ('url','sha256')]]
    data=enrich_predictors(source[keep],root)
    outputs={phase:[] for phase in ('development','holdout')};folds={phase:[] for phase in outputs}
    for target in ('pm_25','pm_10'):
        columns=feature_columns(target)+FEATURES
        for horizon in (24,48,72):
            frame=observed_forecast_table(data,target,horizon)
            for phase,year in [('development',2024),('holdout',2025)]:
                fitting,testing=split_history(frame,year)
                print(f'{phase} {target} +{horizon}h: train={len(fitting):,}; test={len(testing):,}',flush=True)
                model=history_model(target)
                with threadpool_limits(limits=2):
                    model.fit(fitting[columns],fitting.target_value)
                    predicted=model.predict(testing[columns])
                if not np.isfinite(predicted).all():raise ValueError('Predicciones HGB no finitas.')
                fold=dict(target=target,horizon_hours=horizon,fold=1,status='evaluated',
                          train_rows=len(fitting),validation_rows=len(testing),train_target_max=fitting.target_datetime.max(),
                          validation_origin_start=testing.datetime.min(),validation_origin_end_exclusive=testing.datetime.max()+pd.Timedelta(hours=1),
                          train_year_min=int(fitting.datetime.dt.year.min()),train_year_max=int(fitting.datetime.dt.year.max()),
                          validation_target_year=year)
                folds[phase].append(fold)
                keys=['datetime','target_datetime','station_id','station_name','target_source_url','target_source_sha256']
                for method,values in [('hgb_native_missing',predicted),('persistence',testing[target].to_numpy())]:
                    evaluation=testing[keys].copy()
                    evaluation=evaluation.assign(y_true=testing.target_value.to_numpy(),y_pred=values,target=target,horizon_hours=horizon,fold=1,method=method,
                                                 record_type='historical_forecast_evaluation')
                    outputs[phase].append(evaluation)
            del frame
    for phase,parts in outputs.items():
        predictions=pd.concat(parts,ignore_index=True)
        predictions.to_csv(processed/f'hgb_2015_2025_{phase}_predictions.csv',index=False, lineterminator="\n")
        scores=summarize_predictions(predictions,['target','horizon_hours','method'])
        baseline=scores.loc[scores.method.eq('persistence'),['target','horizon_hours','MAE_ug_m3']].rename(columns={'MAE_ug_m3':'baseline_MAE'})
        scores=scores.merge(baseline,on=['target','horizon_hours'],validate='many_to_one')
        scores['MAE_skill_vs_persistence']=1-scores.MAE_ug_m3/scores.baseline_MAE
        scores.to_csv(report/f'{phase}_scores.csv',index=False, lineterminator="\n")
        summarize_predictions(predictions,['target','horizon_hours','station_id','station_name','method']).to_csv(report/f'{phase}_per_station.csv',index=False, lineterminator="\n")
        pd.DataFrame(folds[phase]).to_csv(report/f'{phase}_folds.csv',index=False, lineterminator="\n")
    inputs=source_paths(root)+['data/weather/era5_hourly_2015_2025.csv.gz','data/weather/station_grids.csv','data/weather/era5_manifest.json']
    metadata={'experiment':'hgb_2015_2024_era5_holdout_2025_v1','hgb_parameters':MODEL_PARAMS,
              'input_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in inputs},
              'training_years':list(range(2015,2025)), 'training_scope':'Mediciones publicadas de 2015–2024; prueba final en cuatro semanas de 2025',
              'development_scope':'Entrenamiento 2015–2023; cuatro semanas de desarrollo en 2024',
              'evaluation_label':'cuatro semanas de 2025 (enero, abril, julio y octubre)',
              'evaluation_periods':[{'start':f'2025-{m:02d}-15','end':f'2025-{m:02d}-21'} for m in (1,4,7,10)],
              'target_report_start':'2025-01-15','target_report_end':'2025-10-21',
              'full_history_collected':int(source.report_date.nunique())==4018,
              'holdout_predictions_path':'data/processed/hgb_2015_2025_holdout_predictions.csv',
              'weather_features':FEATURES,'predictor_scope':'ERA5 retrospectivo en el origen; disponibilidad operativa histórica no verificada',
              'future_weather_used':False,'synthetic_targets_used':False,'maps_used_for_training':False,
              'station_scope':'Known stations only; historical relocations not verified',
              'sklearn_version':sklearn.__version__,'live_forecast':False,'deployment_ready':False}
    (report/'experiment.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8', newline="\n")
    print('Experimento multianual completado.',flush=True)
    return metadata


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=parser.parse_args()
    train(args.root)
