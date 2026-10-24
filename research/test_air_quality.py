"""Controles del contrato, tiempos y procedencia, sin solicitudes de red."""

from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from research.air_quality import build_forecast_table, clean_measurements, fetch_report, parse_hourly_report, purged_time_splits


def report_fixture(day="03-02-2024"):
    header = "".join(f"<th>{value}</th>" for value in ["", "parámetros", "Unidades", "Máx", "Mín"] + [f"{h:02d}" for h in range(1, 25)])
    rows = ""
    for label, unit, value in [("PM2.5", "µg/m3", "10,5"), ("PM10", "µg/m3", "20"), ("Temperatura", "°C", "16"), ("HR", "%", "80"), ("Humedad Inter", "%", "12"), ("HR_2m", "%", "99")]:
        values = ["", label, unit, "", ""] + [value] * 24
        rows += "<tr>" + "".join(f"<td>{v}</td>" for v in values) + "</tr>"
    return f'<input id="pageDate" value="{day}"><div class="TableStation" id="S_5" data-station="estación prueba"><table class="DataTable"><tr>{header}</tr>{rows}</table></div>'.encode("cp1252")


class DataContractTests(unittest.TestCase):
    def test_decimal_comma_environmental_channel_and_end_of_day(self):
        data = parse_hourly_report(report_fixture(), "2024-02-03")
        self.assertEqual(len(data), 24)
        self.assertEqual(data.iloc[0].pm_25, 10.5)
        self.assertTrue(data.humidity.eq(80).all())
        self.assertTrue(data.humidity_channel.eq("HR").all())
        self.assertEqual(str(data.iloc[-1].datetime), "2024-02-04 00:00:00-05:00")
        self.assertEqual(str(data.iloc[0].datetime), "2024-02-03 01:00:00-05:00")

    def test_wrong_date_and_units_fail_closed(self):
        with self.assertRaises(ValueError):
            parse_hourly_report(report_fixture(), "2024-02-04")
        with self.assertRaises(ValueError):
            parse_hourly_report(report_fixture().replace(b"\xb5g/m3", b"ppm"), "2024-02-03")

    def test_missing_is_not_zero_and_cleaning_preserves_raw(self):
        data = parse_hourly_report(report_fixture(), "2024-02-03")
        data.loc[0, "humidity"] = -2
        data.loc[1, "pm_25"] = 0
        data.loc[2, "pm_25"] = np.nan
        clean = clean_measurements(data)
        self.assertTrue(pd.isna(clean.loc[0, "humidity"]))
        self.assertEqual(clean.loc[0, "humidity_raw"], -2)
        self.assertEqual(clean.loc[0, "humidity_origin"], "range_review")
        self.assertEqual(clean.loc[1, "pm_25"], 0)
        self.assertEqual(clean.loc[2, "pm_25_origin"], "missing")
        pd.testing.assert_frame_equal(clean, clean_measurements(clean))

    def test_cache_does_not_download_when_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                fetch_report("2024-02-03", Path(directory), allow_network=False)

    def test_appending_raw_rows_to_clean_data_preserves_measurements(self):
        first = clean_measurements(parse_hourly_report(report_fixture(), "2024-02-03"))
        new = parse_hourly_report(report_fixture("04-02-2024"), "2024-02-04")
        combined = clean_measurements(pd.concat([first, new], ignore_index=True))
        self.assertEqual(combined.pm_25.notna().sum(), 48)
        self.assertTrue(combined.humidity.eq(80).all())

    def test_forecast_join_requires_exact_hours_and_observed_target(self):
        first = parse_hourly_report(report_fixture(), "2024-02-03")
        last = parse_hourly_report(report_fixture("03-02-2025"), "2025-02-03")
        table = build_forecast_table(clean_measurements(pd.concat([first, last])), horizon_hours=1)
        self.assertEqual(len(table), 46)
        self.assertTrue((table.target_datetime - table.datetime).eq(pd.Timedelta(hours=1)).all())
        self.assertFalse(table.target_value.isna().any())
        self.assertEqual(len(build_forecast_table(clean_measurements(pd.concat([first, last])), horizon_hours=24)), 0)

    def test_temporal_split_purges_future_labels(self):
        times = pd.date_range("2024-01-01", periods=120, freq="h", tz="America/Bogota")
        frame = pd.DataFrame({"datetime": np.repeat(times, 2)})
        frame["target_datetime"] = frame.datetime + pd.Timedelta(hours=24)
        splits = list(purged_time_splits(frame))
        self.assertTrue(splits)
        for train, validation in splits:
            self.assertLess(frame.iloc[train].target_datetime.max(), frame.iloc[validation].datetime.min())
            self.assertFalse(set(frame.iloc[train].datetime) & set(frame.iloc[validation].datetime))


if __name__ == "__main__":
    unittest.main()
