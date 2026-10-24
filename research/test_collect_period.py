import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from research.air_quality import parse_hourly_report
from research.collect_rmcab_period import collect_period
from research.test_air_quality import report_fixture


class PeriodCollectionTests(unittest.TestCase):
    def test_bounded_dates_and_no_network_by_default(self):
        with self.assertRaises(ValueError):
            collect_period("2025-03-02", "2025-03-01", cache="unused")
        with self.assertRaises(ValueError):
            collect_period("2025-01-01", "2025-12-31", cache="unused")
        with tempfile.TemporaryDirectory() as cache:
            with self.assertRaisesRegex(RuntimeError, "Fechas fallidas: 2025-01-01"):
                collect_period("2025-01-01", "2025-01-01", cache=cache, progress=lambda _: None)

    def test_full_period_combines_exact_report_hours(self):
        def fake_fetch(day, cache, allow_network=False):
            date = pd.Timestamp(day).strftime("%d-%m-%Y")
            return parse_hourly_report(report_fixture(date), day), {"report_date": day}
        with patch("research.collect_rmcab_period.fetch_report", side_effect=fake_fetch) as fetch:
            data, sources = collect_period("2025-01-01", "2025-01-02", cache="unused", progress=lambda _: None)
        self.assertEqual(len(data), 48)
        self.assertEqual(len(sources), 2)
        self.assertTrue(data.pm_25.eq(10.5).all())
        self.assertFalse(data.duplicated(["station_id", "datetime"]).any())
        self.assertEqual(str(data.datetime.max()), "2025-01-03 00:00:00-05:00")
        self.assertTrue(all(not call.kwargs["allow_network"] for call in fetch.call_args_list))

    def test_one_failed_day_does_not_publish_a_partial_period(self):
        def fake_fetch(day, cache, allow_network=False):
            if day.endswith("02"):
                raise ValueError("Reporte inválido")
            return parse_hourly_report(report_fixture("01-01-2025"), day), {"report_date": day}
        with patch("research.collect_rmcab_period.fetch_report", side_effect=fake_fetch):
            with self.assertRaisesRegex(RuntimeError, "2025-01-02"):
                collect_period("2025-01-01", "2025-01-02", cache="unused", progress=lambda _: None)

    def test_valid_report_without_pm_is_preserved_as_missing(self):
        frame = parse_hourly_report(report_fixture("01-01-2025"), "2025-01-01")
        frame[["pm_25", "pm_10"]] = float("nan")
        with patch("research.collect_rmcab_period.fetch_report", return_value=(frame, {"report_date": "2025-01-01"})):
            data, sources = collect_period("2025-01-01", "2025-01-01", cache="unused", progress=lambda _: None)
        self.assertEqual(len(data), 24)
        self.assertTrue(data.pm_25.isna().all())
        self.assertTrue(data.pm_25_origin.eq("missing").all())
        self.assertEqual(len(sources), 1)


if __name__ == "__main__":
    unittest.main()
