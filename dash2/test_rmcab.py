import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from dash2.rmcab_data import (DATA_PATH, export_records, filter_period, load_samples,
    month_options, overview, station_options, station_summary, time_series, year_options)
from dash2.rmcab_figures import figures


class RmcabDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = load_samples()

    def setUp(self):
        self.data = pd.DataFrame([
            ["2025-02-03 01:00-05:00", "2025-02-03", "A", "Estación A", 0, 10, 15, 70],
            ["2025-02-03 03:00-05:00", "2025-02-03", "A", "Estación A", 20, 30, 17, 80],
            ["2025-02-04 01:00-05:00", "2025-02-04", "A", "Estación A", 40, 50, 19, 90],
            ["2025-02-03 01:00-05:00", "2025-02-03", "B", "Estación B", 10, 20, 16, np.nan],
            ["2026-01-01 00:00-05:00", "2025-12-31", "A", "Estación A", 80, 90, 18, 60],
        ], columns=["datetime", "report_date", "station_id", "station_label", "pm_25", "pm_10", "temperature", "humidity"])
        self.data["datetime"] = pd.to_datetime(self.data.datetime, utc=True).dt.tz_convert("America/Bogota")
        self.data["report_date"] = pd.to_datetime(self.data.report_date)

    def test_pilot_loads_all_years_and_exposes_only_published_values(self):
        self.assertGreater(len(self.real), 0)
        self.assertTrue(set(range(2015, 2026)).issubset({o["value"] for o in year_options(self.real, "pm_25")}))
        for variable in ["pm_25", "pm_10", "temperature", "humidity"]:
            self.assertEqual(self.real[variable].notna().sum(), self.real[f"{variable}_origin"].eq("observed").sum())

    def test_report_date_controls_year_and_month_even_for_hour_24(self):
        december = filter_period(self.data, 2025, 12)
        self.assertEqual(len(december), 1)
        self.assertEqual(december.datetime.iloc[0].year, 2026)
        self.assertTrue(filter_period(self.data, 2026).empty)
        self.assertEqual([o["value"] for o in month_options(self.data, 2025, "pm_25")], ["all", 2, 12])

    def test_station_options_exclude_absent_variable_and_selection_is_shared(self):
        period = filter_period(self.data, 2025, 2)
        self.assertEqual([o["value"] for o in station_options(period, "humidity")], ["A"])
        selection = filter_period(self.data, 2025, 2, ["A"])
        self.assertEqual(len(selection), 3)
        self.assertTrue(filter_period(self.data, 2025, 2, []).empty)

    def test_presence_is_selected_report_availability_not_annual_coverage(self):
        period = filter_period(self.data, 2025, 2)
        result = overview(period, "humidity", 2025, 2)
        self.assertEqual(result["observations"], 3)
        self.assertEqual(result["slots"], 4)
        self.assertEqual(result["presence_pct"], 75)
        self.assertEqual(result["report_days"], 2)
        self.assertEqual(result["calendar_days"], 28)
        self.assertEqual(result["stations"], 1)

    def test_aggregation_preserves_zero_and_gaps_and_uses_correct_statistic(self):
        period = filter_period(self.data, 2025, 2, ["A"])
        hourly = time_series(period, "pm_25")
        self.assertEqual(hourly.value.iloc[0], 0)
        self.assertTrue(pd.isna(hourly.value.iloc[1]))
        self.assertEqual(hourly.observations.iloc[1], 0)
        daily = time_series(period, "pm_25", "day", "mean")
        self.assertEqual(daily.value.tolist(), [10, 40])
        self.assertEqual(daily.observations.tolist(), [2, 1])
        self.assertEqual(station_summary(period, "pm_25", "mean").value.iloc[0], 20)
        self.assertEqual(station_summary(period, "pm_25", "max").value.iloc[0], 40)

    def test_figures_have_one_unit_local_clock_and_do_not_connect_missing_hours(self):
        period = filter_period(self.data, 2025, 2, ["A"])
        line, bar = figures(period, "humidity")
        self.assertIn("(%)", line.layout.yaxis.title.text)
        self.assertIn("(%)", bar.layout.xaxis.title.text)
        self.assertEqual(line.data[0].x[0].hour, 1)
        self.assertFalse(line.data[0].connectgaps)
        self.assertEqual(bar.data[0].orientation, "h")
        self.assertEqual(len(line.data), 1)

    def test_empty_selection_shows_message_and_export_has_units(self):
        empty = filter_period(self.data, 2025, 2, [])
        line, bar = figures(empty, "pm_25")
        self.assertIn("Selecciona", line.layout.annotations[0].text)
        self.assertEqual(len(bar.data), 0)
        period = filter_period(self.real, 2025, 2, ["5"])
        exported = export_records(period)
        self.assertTrue(exported.humidity_unit.eq("%").all())
        self.assertTrue(exported.pm_25_unit.eq("µg/m³").all())
        self.assertIn("source_url", exported)
        self.assertIn("pm_25_origin", exported)
        self.assertEqual(len(exported), len(period))
        self.assertTrue(exported.station_id.eq("5").all())

    def test_loader_rejects_imputation_and_mismatched_provenance(self):
        source = pd.read_csv(DATA_PATH, dtype={"station_id": "string"}).head(1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.with_suffix(".sources.json").write_text(DATA_PATH.with_suffix(".sources.json").read_text(encoding="utf-8"), encoding="utf-8")
            imputed = source.copy()
            imputed.loc[0, "pm_25_origin"] = "imputed"
            imputed.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "imputados"):
                load_samples(path)
            changed = source.copy()
            changed.loc[0, "source_sha256"] = "unrecognized"
            changed.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "procedencia"):
                load_samples(path)


if __name__ == "__main__":
    unittest.main()
