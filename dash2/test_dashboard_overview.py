import unittest

import pandas as pd

from dash2.dash_logic import period_overview


class DashboardOverviewTests(unittest.TestCase):
    def setUp(self):
        self.samples = pd.DataFrame([
            ["2024-02-14 08:00", "A"],
            ["2024-02-14 09:00", "A"],
            ["2024-02-29 10:00", "B"],
            ["2024-03-01 08:00", "B"],
            ["2023-02-01 08:00", "C"],
            ["2024-02-15 08:00", "Unknown Zone"],
        ], columns=["datetime", "neighborhood"])

    def test_many_records_on_one_date_count_as_one_available_day(self):
        overview = period_overview(self.samples, 2024, 2)
        self.assertEqual(overview["records"], 3)
        self.assertEqual(overview["days"], 2)
        self.assertEqual(overview["neighborhoods"], 2)
        self.assertEqual(overview["calendar_days"], 29)
        self.assertEqual(overview["start"].day, 14)
        self.assertEqual(overview["end"].day, 29)

    def test_annual_coverage_is_limited_to_the_selected_year(self):
        overview = period_overview(self.samples, 2024)
        self.assertEqual(overview["records"], 4)
        self.assertEqual(overview["days"], 3)
        self.assertEqual(overview["calendar_days"], 366)
        previous = period_overview(self.samples, 2023)
        self.assertEqual(previous["calendar_days"], 365)
        self.assertEqual(previous["neighborhoods"], 1)

    def test_missing_period_is_explicit_and_does_not_change_samples(self):
        original = self.samples.copy(deep=True)
        overview = period_overview(self.samples, 2024, 12)
        self.assertEqual(overview["records"], 0)
        self.assertEqual(overview["days"], 0)
        self.assertIsNone(overview["start"])
        self.assertIsNone(overview["end"])
        pd.testing.assert_frame_equal(self.samples, original)


if __name__ == "__main__":
    unittest.main()
