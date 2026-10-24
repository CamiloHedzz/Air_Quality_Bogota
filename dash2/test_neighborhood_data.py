"""Integridad de la reconstrucción y coherencia entre mapa, promedios y series."""
import hashlib
import json
import unittest

import numpy as np
import pandas as pd

from dash2 import neighborhood_data as maps
from dash2.rmcab_data import VARIABLES, load_samples


class SpatialInterpolationTests(unittest.TestCase):
    def test_constant_field_and_exact_station_are_preserved(self):
        values=np.array([[12., 12., 12.], [10., 20., 30.]])
        distances=np.array([[0., 1., 2.], [1., 2., 3.]])
        result=maps.interpolate(values, distances)
        np.testing.assert_allclose(result[0], [12,12])
        self.assertEqual(result[1,0],10)
        self.assertTrue(10 <= result[1,1] <= 30)

    def test_missing_values_do_not_become_zero_and_neighbors_must_be_available(self):
        values=np.array([[np.nan,np.nan,40.], [np.nan,np.nan,np.nan]])
        result=maps.interpolate(values,np.array([[1.,2.,3.]]),neighbors=2)
        self.assertEqual(result[0,0],40)
        self.assertTrue(np.isnan(result[1,0]))


class MapHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame,cls.centroids,cls.manifest=maps.load_history()

    def test_complete_calendar_including_leap_years_and_distinct_origins(self):
        self.assertEqual(sorted(self.frame.report_date.dt.year.unique()),list(range(2015,2026)))
        for year,part in self.frame.groupby(self.frame.report_date.dt.year):
            expected=len(pd.date_range(f'{year}-01-01',f'{year}-12-31'))
            self.assertTrue(part.groupby('station_id').report_date.nunique().eq(expected).all())
        for var in VARIABLES:
            self.assertFalse(self.frame[var].isna().any())
            observed=self.frame[f'{var}_hours'].gt(0)
            self.assertTrue(self.frame.loc[observed,f'{var}_origin'].eq('observed_daily_aggregate').all())
            self.assertTrue(self.frame.loc[~observed,f'{var}_origin'].eq('knn_scenario_baseline').all())

    def test_every_published_daily_aggregate_is_preserved(self):
        raw=pd.concat([load_samples(maps.ROOT/path) for path in ['data/samples/rmcab_pilot_2015_2025.csv','data/samples/rmcab_2025_q1.csv']]).drop_duplicates(['station_id','datetime'])
        original=raw.groupby(['station_id','report_date'])[list(VARIABLES)].mean()
        actual=self.frame.set_index(['station_id','report_date'])
        for var in VARIABLES:
            expected=original[var].dropna()
            np.testing.assert_allclose(actual.loc[expected.index,var],expected,atol=1e-7,rtol=0)

    def test_all_original_polygons_and_identifiers_are_retained(self):
        geo=json.loads((maps.ROOT/'dash2/datasets/bogota_cadastral.json').read_text(encoding='utf-8'))
        self.assertEqual(set(self.centroids.neighborhood),{f['properties']['DISPLAY_NAME'] for f in geo['features']})
        data,info=maps.aggregates(2015,'all','estimated')
        self.assertEqual(len(data),1160)
        self.assertTrue(data.pm_25_mean.notna().all())
        self.assertEqual(info['pm_25']['source_days'],1)
        self.assertEqual(info['pm_25']['represented_days'],365)
        name=data.neighborhood.iloc[0]
        figure=maps.map_figure(data,'pm_25_mean',geo,[name],mode='estimated')
        self.assertEqual(len(figure.data[0].locations),1160)
        selected=list(figure.data[1].locations).index(name)
        self.assertEqual(figure.data[1].marker.line.width[selected],2.5)

    def test_observed_only_does_not_fill_missing_months_or_hide_boundaries(self):
        data,info=maps.aggregates(2015,12,'observed')
        self.assertTrue(data.pm_25_mean.isna().all())
        self.assertEqual(info['pm_25']['represented_days'],0)
        self.assertEqual(info['pm_25']['days_added'],0)
        geo=json.loads((maps.ROOT/'dash2/datasets/bogota_cadastral.json').read_text(encoding='utf-8'))
        figure=maps.map_figure(data,'pm_25_mean',geo,mode='observed')
        self.assertEqual(len(figure.data[0].locations),1160)
        self.assertTrue(figure.layout.annotations)

    def test_annual_map_equals_daily_series_and_weighted_monthly_means(self):
        annual,_=maps.aggregates(2024,'all','estimated')
        selected=annual.neighborhood.iloc[:2].tolist()
        daily=maps.series(2024,'all','estimated',selected)
        expected=daily.groupby('neighborhood').pm_25.mean()
        np.testing.assert_allclose(annual.set_index('neighborhood').loc[expected.index,'pm_25_mean'],expected)
        self.assertEqual(len(daily),366*len(selected))
        monthly=maps.series(2024,'all','estimated',selected,'Mensual')
        for name,group in monthly.groupby('neighborhood'):
            weighted=np.average(group.pm_25,weights=group.datetime.dt.days_in_month)
            self.assertAlmostEqual(weighted,expected[name])

    def test_export_has_units_scope_and_observed_coverage(self):
        exported=maps.export_aggregates(2016,7,'estimated')
        self.assertTrue(exported.dataset_mode.eq('estimated').all())
        self.assertTrue(exported.pm_25_source_days.eq(0).all())
        self.assertTrue(exported.pm_25_temporal_days_added.eq(31).all())
        self.assertTrue(exported.pm_25_unit.eq('µg/m³').all())
        self.assertTrue(exported.value_scope.str.contains('not_neighborhood_measurement').all())

    def test_generated_data_is_not_part_of_the_forecast_training_inputs(self):
        forecast=json.loads((maps.ROOT/'data/forecasts/hgb_historical.json').read_text(encoding='utf-8'))
        self.assertFalse(self.manifest['used_to_train_forecast_model'])
        for path,digest in forecast['input_sha256'].items():
            self.assertNotIn('/maps/',path)
            self.assertEqual(hashlib.sha256((maps.ROOT/path).read_bytes()).hexdigest(),digest)


if __name__=='__main__': unittest.main()
