import unittest

import pandas as pd

from dash2.dash_logic import (
    aggregate_neighborhoods, available_years, create_bar_graph,
    create_time_series, filter_period, month_options,
)
from dash2.dash_figures import get_figure


class DashboardPeriodTests(unittest.TestCase):
    def setUp(self):
        self.samples = pd.DataFrame([
            ["2023-02-01 10:00", "A", 100, 110, 15, 60],
            ["2024-02-01 10:00", "B", 20, 30, 16, 65],
            ["2024-02-01 12:00", "B", 40, 50, 18, 75],
            ["2024-03-01 10:00", "A", 80, 90, 20, 80],
            ["2025-01-01 10:00", "Unknown Zone", 1, 1, 1, 1],
            ["invalid", "A", 1, 1, 1, 1],
        ], columns=["datetime", "neighborhood", "pm_25", "pm_10", "temperature", "humidity"])

    def test_years_and_months_come_from_available_records(self):
        self.assertEqual(available_years(self.samples), [2023, 2024])
        self.assertEqual([m["value"] for m in month_options(self.samples, 2024)], ["all", 2, 3])
        self.assertEqual([m["value"] for m in month_options(self.samples, 2023)], ["all", 2])

    def test_repeated_month_filter_is_year_specific_and_does_not_mutate_source(self):
        original = self.samples.copy(deep=True)
        for _ in range(2):
            data = filter_period(self.samples, 2024, 2)
            self.assertEqual(len(data), 2)
            self.assertEqual(data["neighborhood"].unique().tolist(), ["B"])
        pd.testing.assert_frame_equal(original, self.samples)

    def test_all_year_and_empty_period(self):
        self.assertEqual(len(filter_period(self.samples, 2024)), 3)
        self.assertTrue(filter_period(self.samples, 2024, 12).empty)
        self.assertTrue(filter_period(self.samples, None).empty)

    def test_map_locations_values_and_borders_stay_aligned_for_sparse_month(self):
        data = aggregate_neighborhoods(filter_period(self.samples, 2024, 2))
        fig = get_figure(data, "pm_25_mean", {"type": "FeatureCollection", "features": []}, ["B"])
        self.assertEqual(list(fig.data[0].locations), ["B"])
        self.assertEqual(list(fig.data[0].z), [30])
        self.assertEqual(list(fig.data[0].marker.line.width), [2.5])

    def test_map_and_charts_use_the_same_period_and_daily_averages(self):
        period = filter_period(self.samples, 2024, 2)
        series = create_time_series(period, ["B"], "Diaria")
        bars = create_bar_graph(aggregate_neighborhoods(period), ["B"])
        self.assertEqual(len(series), 1)
        self.assertEqual(series.iloc[0]["pm_25"], 30)
        self.assertEqual(bars.loc[bars["variable"].eq("pm_25_mean"), "value"].tolist(), [30])
        self.assertEqual(series["datetime"].dt.month.unique().tolist(), [2])

    def test_no_selection_and_no_data_are_supported(self):
        period = filter_period(self.samples, 2024, 12)
        self.assertTrue(create_time_series(period, []).empty)
        self.assertTrue(create_bar_graph(aggregate_neighborhoods(period), []).empty)
        fig = get_figure(aggregate_neighborhoods(period), "pm_25_mean", {"type": "FeatureCollection", "features": []})
        self.assertIn("No hay datos", fig.layout.annotations[0].text)

    def test_figures_do_not_share_theme_or_selection(self):
        data = aggregate_neighborhoods(filter_period(self.samples, 2024))
        first = get_figure(data, "pm_25_mean", {"type": "FeatureCollection", "features": []}, ["A"], "color")
        second = get_figure(data, "pm_25_mean", {"type": "FeatureCollection", "features": []}, ["B"], "light")
        self.assertTrue(first.layout.mapbox.style.endswith("liberty"))
        self.assertTrue(second.layout.mapbox.style.endswith("positron"))
        self.assertEqual(list(first.data[0].marker.line.width), [2.5, 0.5])
        self.assertEqual(list(second.data[0].marker.line.width), [0.5, 2.5])

    def test_same_month_in_new_year_is_added_without_hardcoded_options(self):
        expanded = pd.concat([self.samples, pd.DataFrame([
            ["2026-02-01", "B", 10, 20, 12, 70],
        ], columns=self.samples.columns)], ignore_index=True)
        self.assertEqual(available_years(expanded), [2023, 2024, 2026])
        self.assertEqual(filter_period(expanded, 2026, 2)["pm_25"].tolist(), [10])


if __name__ == "__main__":
    unittest.main()
