"""Pruebas de fuga temporal, procedencia y evaluación común del piloto."""

import unittest

import numpy as np
import pandas as pd

from research.air_quality import VARIABLES
from research.forecast_experiment import feature_columns, make_model, observed_forecast_table, run_pilot_benchmark, temporal_windows


def observations(periods=168):
    times = pd.date_range("2025-02-03 01:00", periods=periods, freq="h", tz="America/Bogota")
    rows = []
    for t in times:
        for station in ("A", "B"):
            values = {"pm_25": float(t.hour + 2), "pm_10": float(t.hour + 12), "temperature": 15.0, "humidity": 70.0}
            rows.append(dict(datetime=t, station_id=station, station_name=station, source_url="fixture", source_sha256="fixture",
                             **values, **{f"{v}_origin": "observed" for v in VARIABLES}))
    return pd.DataFrame(rows)


class ForecastExperimentTests(unittest.TestCase):
    def test_synthetic_target_and_unmarked_fill_rejected(self):
        data = observations()
        data.loc[0, "pm_25_origin"] = "synthetic"
        with self.assertRaises(ValueError):
            observed_forecast_table(data, "pm_25", 1)
        data.loc[0, "pm_25_origin"] = "missing"
        with self.assertRaises(ValueError):
            observed_forecast_table(data, "pm_25", 1)

    def test_gap_does_not_become_a_lag_and_future_never_enters_features(self):
        data = observations(50)
        missing_time = data.datetime.min() + pd.Timedelta(hours=3)
        data = data.loc[data.datetime.ne(missing_time)].copy()
        frame = observed_forecast_table(data, "pm_25", 1)
        after_gap = frame.loc[frame.datetime.eq(missing_time + pd.Timedelta(hours=1))]
        self.assertTrue(after_gap.pm_25_lag_1h.isna().all())
        cut = data.datetime.min() + pd.Timedelta(hours=30)
        changed = data.copy()
        changed.loc[changed.datetime.gt(cut), VARIABLES] = 9999.0
        later = observed_forecast_table(changed, "pm_25", 1)
        keys = ["station_id", "datetime"]
        original = frame.loc[frame.datetime.le(cut)].sort_values(keys)
        modified = later.loc[later.datetime.le(cut)].sort_values(keys)
        pd.testing.assert_frame_equal(original[feature_columns("pm_25")].reset_index(drop=True), modified[feature_columns("pm_25")].reset_index(drop=True))

    def test_windows_purge_labels_and_keep_station_times_together(self):
        data = observations()
        frame = observed_forecast_table(data, "pm_25", 24)
        held_out = set()
        for _, start, _, train, validation, _ in temporal_windows(frame, last_time=data.datetime.max(), horizon=24):
            if len(train):
                self.assertLess(train.target_datetime.max(), start)
            self.assertFalse(set(train.datetime) & set(validation.datetime))
            keys = set(zip(validation.station_id, validation.datetime))
            self.assertFalse(keys & held_out)
            held_out.update(keys)

    def test_median_is_fit_only_on_train_and_native_accepts_missing(self):
        frame = observed_forecast_table(observations(80), "pm_25", 1)
        columns = feature_columns("pm_25")
        training = frame.iloc[:80].copy()
        validation = frame.iloc[80:].copy()
        validation["humidity"] = np.nan
        for impute in (False, True):
            model = make_model("pm_25", impute=impute)
            model.fit(training[columns], training.target_value)
            self.assertTrue(np.isfinite(model.predict(validation[columns])).all())
            if impute:
                median = model.named_steps["features"].named_transformers_["measurements"]
                self.assertEqual(median.statistics_[VARIABLES.index("humidity")], 70.0)

    def test_holdout_methods_fixed_in_advance_and_unknown_method_rejected(self):
        result = run_pilot_benchmark(observations(), targets=("pm_25",), horizons=(1,),
                                     n_folds=1, min_train_rows=40,
                                     methods=("persistence", "hgb_native_missing"))
        self.assertEqual(set(result["predictions"].method), {"persistence", "hgb_native_missing"})
        with self.assertRaises(ValueError):
            run_pilot_benchmark(observations(), methods=("unknown",))

    def test_short_72h_is_skipped_and_scored_rows_identical(self):
        result = run_pilot_benchmark(observations(), targets=("pm_25",), horizons=(1, 72), min_train_rows=40)
        self.assertTrue(result["folds"].loc[result["folds"].horizon_hours.eq(72), "status"].eq("skipped").all())
        predictions = result["predictions"]
        counts = predictions.groupby(["fold", "method"]).size().unstack()
        self.assertTrue(counts.nunique(axis=1).eq(1).all())
        truth = predictions.pivot(index=["fold", "station_id", "datetime"], columns="method", values="y_true")
        self.assertTrue(truth.nunique(axis=1).eq(1).all())


if __name__ == "__main__":
    unittest.main()
