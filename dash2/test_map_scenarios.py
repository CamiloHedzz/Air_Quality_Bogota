"""La variación es reproducible y no suplanta días respaldados por fuentes."""
import unittest
import numpy as np
import pandas as pd

from dash2 import neighborhood_data as maps
from dash2.map_scenarios import fill_short_gaps, scenario_noise, variation_rate
from dash2.rmcab_data import VARIABLES


class ShortGapTests(unittest.TestCase):
    def test_whole_short_runs_only_without_extrapolating_edges(self):
        x = pd.Series([np.nan, 10, np.nan, np.nan, np.nan, 18, np.nan, np.nan, np.nan, np.nan, 30, np.nan])
        y = fill_short_gaps(x)
        np.testing.assert_allclose(y.iloc[2:5], [12, 14, 16])
        self.assertTrue(y.iloc[6:10].isna().all())
        self.assertTrue(y.iloc[[0, 11]].isna().all())
        np.testing.assert_array_equal(x.dropna(), y.loc[x.notna()])

    def test_scenario_rate_is_bounded_and_finite(self):
        for bad in [-1, 31, np.nan, np.inf]:
            with self.assertRaises(ValueError): variation_rate(bad)


class ScenarioIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame, cls.centroids, cls.manifest = maps.load_history()
        cls.names = cls.centroids.loc[cls.centroids.neighborhood.str.contains('SAGRADO CORAZON|PROVIVIENDA', regex=True), 'neighborhood'].tolist()[:3]

    def test_two_options_with_complete_treatment_and_original_gaps(self):
        self.assertEqual(maps.MODES, {'observed': 'Datos originales', 'estimated': 'Datos con tratamiento'})
        data, info = maps.aggregates(2015)
        self.assertEqual(info['temperature']['source_days'], 1)
        self.assertEqual(info['temperature']['represented_days'], 365)
        self.assertEqual(info['temperature']['days_added'], 364)
        self.assertTrue(data.temperature_mean.notna().all())
        original, original_info = maps.aggregates(2015, 12, 'observed')
        self.assertTrue(original.temperature_mean.isna().all())
        self.assertEqual(len(original), 1160)
        self.assertEqual(original_info['temperature']['days_added'], 0)
        self.assertFalse(any('weekday' in feature for feature in self.manifest['features']))

    def test_source_and_short_gap_values_are_invariant_under_random_variation(self):
        observed = maps.series(2025, 'all', 'observed', self.names)
        low = maps.series(2025, 'all', 'estimated', self.names, variation=0)
        high = maps.series(2025, 'all', 'estimated', self.names, variation=30)
        for var in VARIABLES:
            measured = observed[var].notna()
            np.testing.assert_allclose(observed.loc[measured, var], low.loc[measured, var])
            np.testing.assert_allclose(observed.loc[measured, var], high.loc[measured, var])
            supported = low[f'{var}_origin'].ne('simulated')
            np.testing.assert_allclose(low.loc[supported, var], high.loc[supported, var])
            simulated = high[f'{var}_origin'].eq('simulated')
            if simulated.any():
                self.assertFalse(np.allclose(low.loc[simulated, var], high.loc[simulated, var]))
            if var in {'temperature','humidity'}:
                self.assertFalse(simulated.any())
                self.assertTrue(high[f'{var}_origin'].eq('weather_reanalysis').any())
        self.assertTrue(high.humidity.between(0, 100).all())
        self.assertTrue(high[['pm_25', 'pm_10']].ge(0).all().all())

    def test_seed_and_absolute_dates_keep_month_selection_and_order_consistent(self):
        annual = maps.series(2025, 'all', 'estimated', self.names, variation=15)
        april = maps.series(2025, 4, 'estimated', list(reversed(self.names)), variation=15)
        expected = annual.loc[annual.datetime.dt.month.eq(4)].reset_index(drop=True)
        pd.testing.assert_frame_equal(expected, april)
        single = maps.series(2025, 4, 'estimated', self.names[:1], variation=15)
        pd.testing.assert_frame_equal(single, april.loc[april.neighborhood.eq(self.names[0])].reset_index(drop=True))
        again = maps.series(2025, 4, 'estimated', self.names, variation=15)
        pd.testing.assert_frame_equal(again, april)

    def test_local_innovations_are_distinct_and_zero_rate_is_exact(self):
        dates = pd.date_range('2025-04-01', '2025-12-31')
        noise = scenario_noise(self.names, dates, 'temperature', 10, 4)
        self.assertFalse(np.allclose(noise[:, 0], noise[:, 1]))
        # A weekly sawtooth would be nearly unchanged after seven days.
        self.assertLess(abs(pd.Series(noise[:, 0]).autocorr(7)), .8)
        np.testing.assert_array_equal(scenario_noise(self.names, dates, 'temperature', 0, 4), np.zeros_like(noise))

    def test_map_series_monthly_aggregation_and_export_share_the_same_scenario(self):
        daily = maps.series(2025, 'all', 'estimated', self.names, variation=20)
        annual, info = maps.aggregates(2025, 'all', 'estimated', 20)
        exported = maps.export_aggregates(2025, 'all', 'estimated', 20).set_index('neighborhood')
        for mean, var in maps.METRICS.items():
            expected = daily.groupby('neighborhood')[var].mean()
            np.testing.assert_allclose(annual.set_index('neighborhood').loc[expected.index, mean], expected)
            np.testing.assert_allclose(exported.loc[expected.index, mean], expected)
            monthly = maps.series(2025, 'all', 'estimated', self.names, 'Mensual', variation=20)
            for name, group in monthly.groupby('neighborhood'):
                self.assertAlmostEqual(np.average(group[var], weights=group.datetime.dt.days_in_month), expected[name])
            counts = info[var]
            self.assertEqual(counts['represented_days'], counts['source_days']+counts['short_gap_days']+counts['simulated_days']+counts['reanalysis_days'])
            self.assertTrue(exported[f'{var}_simulated_days'].eq(counts['simulated_days']).all())
        self.assertTrue(exported.variation_percent.eq(20).all())
        self.assertTrue(exported.simulation_seed.eq(maps.SIMULATION_SEED).all())
        self.assertTrue(exported.value_scope.str.startswith('treated_with_estimated_and_synthetic_gaps').all())

    def test_one_curve_per_sector_and_variable_with_origin_in_hover(self):
        original, _ = maps.charts(2015, 'all', 'observed', self.names[:1], 'temperature_mean', [], 'Diaria')
        self.assertEqual(original.layout.title.text, 'Datos originales')
        self.assertTrue(all('markers' in t.mode for t in original.data))
        treated, _ = maps.charts(2025, 'all', 'estimated', self.names, 'temperature_mean', ['humidity'], 'Mensual')
        self.assertEqual(treated.layout.title.text, 'Datos con tratamiento')
        self.assertEqual(len(treated.data), len(self.names)*2)
        self.assertTrue(all(np.isfinite(t.y).all() and len(t.y) == 12 for t in treated.data))
        self.assertEqual(sum(bool(t.showlegend) for t in treated.data), len(self.names))
        self.assertTrue(all('customdata[3]' in t.hovertemplate for t in treated.data))
        self.assertTrue(any('ERA5' in row[4] for t in treated.data for row in t.customdata))


if __name__ == '__main__': unittest.main()
