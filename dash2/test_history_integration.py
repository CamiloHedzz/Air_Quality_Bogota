"""Integridad del histórico publicado, preservación y contexto ERA5."""
import gzip
import hashlib
import unittest

import numpy as np
import pandas as pd

from dash2.history_data import ROOT,load_observations,observation_metadata,LEGACY_INPUTS
from dash2.rmcab_data import load_samples,VARIABLES
from dash2.weather_data import load_weather,analysis_period


class ExpandedHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_observations()
        cls.meta=observation_metadata()

    def test_every_existing_valid_reading_and_its_source_are_preserved(self):
        old=pd.concat([load_samples(ROOT/p) for p in LEGACY_INPUTS],ignore_index=True).drop_duplicates(['station_id','datetime'])
        actual=self.data.set_index(['station_id','datetime'])
        for var in VARIABLES:
            source=old.loc[old[var].notna()].set_index(['station_id','datetime'])
            np.testing.assert_allclose(actual.loc[source.index,var],source[var],atol=1e-8,rtol=0)
            self.assertTrue(actual.loc[source.index,f'{var}_source_sha256'].astype(str).eq(source.source_sha256.astype(str)).all())

    def test_raw_targets_are_observed_and_source_exports_are_reproducible(self):
        self.assertGreater(self.meta['report_days'],3650)
        self.assertFalse(self.data.duplicated(['station_id','datetime']).any())
        exports=[s for s in self.meta['sources'] if s.get('kind')=='SISAIRE_hourly_export']
        self.assertEqual(len(exports),22)
        for source in exports:
            blob=gzip.decompress((ROOT/source['archive_path']).read_bytes())
            self.assertEqual(hashlib.sha256(blob).hexdigest(),source['sha256'])
        for var in ('pm_25','pm_10'):
            self.assertTrue(self.data[f'{var}_origin'].isin(['observed','missing','range_review']).all())

    def test_categorical_labels_do_not_create_false_station_combinations(self):
        from dash2.rmcab_data import filter_period,station_options,station_summary
        period=filter_period(self.data,2015)
        options=station_options(period,'pm_25')
        ids=[o['value'] for o in options]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(all(' · 0 mediciones' not in o['label'] for o in options))
        summary=station_summary(period,'pm_25')
        self.assertFalse(summary.station_id.duplicated().any())

    def test_weather_is_complete_reanalysis_and_does_not_modify_pm(self):
        weather,_,meta=load_weather()
        self.assertEqual(meta['record_type'],'weather_reanalysis')
        self.assertEqual(meta['hours_per_grid'],4018*24)
        self.assertEqual(weather.groupby('grid_id',observed=True).datetime.nunique().nunique(),1)
        start=pd.Timestamp('2025-04-15',tz='America/Bogota');end=start+pd.Timedelta(hours=48)
        treated=analysis_period(self.data,start,end,['5'])
        self.assertTrue(treated.humidity.notna().all())
        self.assertTrue(treated.humidity_origin.eq('weather_reanalysis').all())
        actual=self.data.loc[self.data.station_id.eq('5')&self.data.datetime.between(start,end)].set_index('datetime')
        for var in ['pm_25','pm_10']:
            joined=treated.set_index('datetime').loc[actual.index,var]
            np.testing.assert_allclose(joined,actual[var],equal_nan=True)
        self.assertFalse(treated.pm_25_origin.eq('weather_reanalysis').any())


if __name__=='__main__':unittest.main()
