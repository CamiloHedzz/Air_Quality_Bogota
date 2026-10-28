"""Offline regression checks for the byte contracts of published datasets.

Run with ``python -m unittest research.test_data_portability``.  These checks use
only the standard library and the files shipped in the repository; they neither
download observations nor train a model.
"""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (
    "data/history/observations_manifest.json",
    "data/weather/era5_manifest.json",
    "data/reports/hgb_2015_2025/experiment.json",
    "data/forecasts/hgb_historical.json",
    "data/maps/history_manifest.json",
    "data/reports/run_manifest.json",
    "data/reports/legacy_audit.json",
    "data/reports/hgb_pilot/experiment.json",
    "data/reports/hgb_2025_q1/experiment.json",
)


class DataPortabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.metadata = {
            relative: json.loads((ROOT / relative).read_text(encoding="utf-8"))
            for relative in MANIFESTS
        }
        cls.digests = {}

    def assert_digest(self, relative, expected):
        """Keep exact-byte integrity checks, including for compressed datasets."""
        if relative not in self.digests:
            self.digests[relative] = hashlib.sha256(
                (ROOT / relative).read_bytes()
            ).hexdigest()
        self.assertEqual(self.digests[relative], expected, relative)

    def assert_digests(self, mapping, folder=""):
        self.assertTrue(mapping, "The manifest must declare its dataset hashes.")
        for relative, expected in mapping.items():
            path = (Path(folder) / relative).as_posix()
            with self.subTest(path=path):
                self.assert_digest(path, expected)

    def test_hashed_text_and_manifests_use_lf(self):
        """LF check catches a Windows checkout even when its hashes agree locally."""
        paths = set(MANIFESTS)
        for relative, metadata in self.metadata.items():
            for field in ("input_sha256", "legacy_input_sha256"):
                paths.update(metadata.get(field, {}))
            paths.update(
                (Path(relative).parent / name).as_posix()
                for name in metadata.get("output_sha256", {})
            )
        paths.update((
            "data/references/rmcab_station_locations.json",
            "data/samples/rmcab_pilot_2015_2025.sources.json",
            "data/samples/rmcab_2025_q1.sources.json",
            "dash2/datasets/final_rutes.csv",
        ))
        for relative in sorted(paths):
            if Path(relative).suffix not in (".csv", ".json"):
                continue
            with self.subTest(path=relative):
                content = (ROOT / relative).read_bytes()
                self.assertTrue(
                    b"\r" not in content,
                    f"{relative} must use LF so its hash survives checkout on another OS.",
                )

    def test_forecast_inputs_match_the_training_experiment(self):
        metadata = self.metadata["data/forecasts/hgb_historical.json"]
        experiment = self.metadata["data/reports/hgb_2015_2025/experiment.json"]
        self.assertEqual(metadata["input_sha256"], experiment["input_sha256"])
        self.assert_digests(metadata["input_sha256"])
        self.assert_digest(
            "data/forecasts/hgb_historical.csv.gz", metadata["forecast_sha256"]
        )

    def test_observed_history_and_legacy_inputs_match_their_manifest(self):
        metadata = self.metadata["data/history/observations_manifest.json"]
        self.assert_digest(
            "data/history/observations.csv.gz", metadata["observations_sha256"]
        )
        self.assert_digests(metadata["legacy_input_sha256"])

    def test_weather_outputs_and_reference_match_their_manifest(self):
        metadata = self.metadata["data/weather/era5_manifest.json"]
        self.assert_digests(metadata["output_sha256"], "data/weather")
        self.assert_digest(
            "data/references/rmcab_station_locations.json",
            metadata["reference_sha256"],
        )

    def test_neighborhood_map_inputs_and_outputs_match_their_manifest(self):
        metadata = self.metadata["data/maps/history_manifest.json"]
        self.assert_digests(metadata["input_sha256"])
        self.assert_digests(metadata["output_sha256"], "data/maps")

    def test_legacy_report_references_remain_verifiable(self):
        references = (
            ("data/reports/run_manifest.json", "legacy_sha256", "dash2/datasets/final_rutes.csv"),
            ("data/reports/run_manifest.json", "pilot_sha256", "data/samples/rmcab_pilot_2015_2025.csv"),
            ("data/reports/legacy_audit.json", "source_sha256", "dash2/datasets/final_rutes.csv"),
            ("data/reports/hgb_pilot/experiment.json", "dataset_sha256", "data/samples/rmcab_pilot_2015_2025.csv"),
            ("data/reports/hgb_pilot/experiment.json", "source_manifest_sha256", "data/samples/rmcab_pilot_2015_2025.sources.json"),
            ("data/reports/hgb_2025_q1/experiment.json", "source_manifest_sha256", "data/samples/rmcab_2025_q1.sources.json"),
        )
        for manifest, field, relative in references:
            with self.subTest(manifest=manifest, field=field):
                self.assert_digest(relative, self.metadata[manifest][field])
        self.assert_digests(
            self.metadata["data/reports/hgb_2025_q1/experiment.json"]["input_sha256"]
        )


if __name__ == "__main__":
    unittest.main()
