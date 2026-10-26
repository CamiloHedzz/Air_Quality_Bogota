"""Controles de tiempo, duplicados, unidades y etiquetas, sin red."""
import io
import json
import unittest

import numpy as np
import pandas as pd

from research.collect_sisaire import validate_export
from research.weather_history import parse_weather,UNITS
from research.train_history import split_history
from research.air_quality import build_forecast_table,clean_measurements
from research.test_air_quality import report_fixture
from research.air_quality import parse_hourly_report


class SisaireContractTests(unittest.TestCase):
    def blob(self,rows):
        return pd.DataFrame(rows,columns=['Estacion','Fecha inicial','Fecha final','PM2.5']).to_csv(index=False).encode()

    def test_two_hourly_conventions_and_zero_are_preserved(self):
        raw=self.blob([['LAS FERIAS','2015-01-01 00:00','2015-01-01 01:00',0],['LAS FERIAS','2015-01-01 01:00','2015-01-01 01:59',12]])
        data=validate_export(raw,'2015-01-01','2015-01-01','PM2.5')
        self.assertEqual(list(data['PM2.5']),[0,12])

    def test_identical_duplicates_removed_conflicts_and_unaligned_excluded(self):
        a=['LAS FERIAS','2015-01-01 00:00','2015-01-01 00:59',12]
        raw=self.blob([a,a,['LAS FERIAS','2015-01-01 01:00','2015-01-01 01:59',13],['LAS FERIAS','2015-01-01 01:00','2015-01-01 01:59',14],
                       ['LAS FERIAS','2015-01-01 02:59','2015-01-01 03:58',15]])
        data=validate_export(raw,'2015-01-01','2015-01-01','PM2.5')
        self.assertEqual(list(data['PM2.5']),[12])
        self.assertEqual(data.attrs['identical_duplicates_removed'],1)
        self.assertEqual(data.attrs['conflicting_duplicate_rows_excluded'],2)
        self.assertEqual(data.attrs['excluded_unaligned_intervals'],1)

    def test_wrong_dates_and_daily_aggregates_rejected(self):
        for start,end in [('2014-01-01 00:00','2014-01-01 00:59'),('2015-01-01 00:00','2015-01-01 23:59')]:
            with self.assertRaises(ValueError):validate_export(self.blob([['LAS FERIAS',start,end,12]]),'2015-01-01','2015-01-01','PM2.5')


class WeatherContractTests(unittest.TestCase):
    def fixture(self):
        hours=pd.date_range('2015-01-01',periods=24,freq='h')
        payload={'timezone':'America/Bogota','utc_offset_seconds':-18000,'latitude':4.75,'longitude':-74.,'hourly_units':UNITS,
                 'hourly':{'time':hours.strftime('%Y-%m-%dT%H:%M').tolist(),**{key:[15.]*24 for key in UNITS}}}
        return payload,pd.DataFrame([{'grid_id':'a','grid_latitude':4.75,'grid_longitude':-74.}])

    def test_units_hours_and_cell_checked(self):
        payload,grids=self.fixture()
        data=parse_weather(json.dumps(payload),grids,'2015-01-01','2015-01-01')
        self.assertEqual(len(data),24);self.assertEqual(str(data.datetime.dt.tz),'America/Bogota')
        for change in ['unit','hour','cell']:
            payload,_=self.fixture()
            if change=='unit':payload['hourly_units']={**UNITS,'wind_speed_10m':'km/h'}
            if change=='hour':payload['hourly']['time'][1]=payload['hourly']['time'][0]
            if change=='cell':payload['latitude']=5.5
            with self.assertRaises(ValueError):parse_weather(json.dumps(payload),grids,'2015-01-01','2015-01-01')


class HistoricalModelTests(unittest.TestCase):
    def test_target_uses_pollutant_specific_provenance(self):
        data=clean_measurements(parse_hourly_report(report_fixture(),'2024-02-03'))
        data['pm_10_source_url']='https://example.test/pm10'
        data['pm_10_source_sha256']='pm10-verified-hash'
        frame=build_forecast_table(data,target='pm_10',horizon_hours=1)
        self.assertTrue(frame.target_source_sha256.eq('pm10-verified-hash').all())
        self.assertTrue(frame.target_source_url.eq('https://example.test/pm10').all())

    def test_training_targets_do_not_reach_validation_year(self):
        zone='America/Bogota'
        data=pd.DataFrame({'station_id':['5']*3,'datetime':pd.to_datetime(['2023-12-28','2023-12-31','2024-01-14']).tz_localize(zone),
                           'target_datetime':pd.to_datetime(['2023-12-29','2024-01-01','2024-01-15']).tz_localize(zone)})
        # Hora 24 pertenece al día anterior: usar un objetivo interior del día 15.
        data.loc[2,'target_datetime']+=pd.Timedelta(hours=12)
        train,test=split_history(data,2024)
        self.assertEqual(len(train),1);self.assertEqual(len(test),1)
        self.assertLess(train.target_datetime.max(),test.datetime.min())


if __name__=='__main__':unittest.main()
