"""Deterministic tests: no live provider calls and no database needed."""
import json
import unittest
from unittest.mock import patch

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase

from . import planner
from .planner_views import compare, places


def station(identifier, value, coordinates):
    return {"id": identifier, "value": value, "coordinates": coordinates}


def route(seconds=600, identifier="route-1"):
    return {"id": identifier, "coordinates": [[-74.09, 4.65], [-74.08, 4.65]], "times": [0, seconds],
            "duration_s": seconds, "distance_m": 1110, "access_m": 0}


class ExposureTests(unittest.TestCase):
    def setUp(self):
        self.stations = [station("1", 10, [-74.09, 4.65]), station("2", 10, [-74.08, 4.65])]

    def test_constant_concentration_integrates_minutes(self):
        result = planner.estimate_route(route(), "pm_25", 7 * 60, 0, {("pm_25", False, 7): self.stations})
        self.assertAlmostEqual(result["exposure"], 100)
        self.assertEqual(result["mean_concentration"], 10)
        self.assertTrue(result["air_complete"])
        self.assertEqual(result["station_ids"], ["1", "2"])

    def test_crossing_hour_uses_arrival_hour(self):
        later = [{**s, "value": 30} for s in self.stations]
        result = planner.estimate_route(route(1200), "pm_25", 7 * 60 + 50, 0,
            {("pm_25", False, 7): self.stations, ("pm_25", False, 8): later})
        self.assertAlmostEqual(result["exposure"], 400)

    def test_friday_midnight_rolls_into_weekend(self):
        later = [{**s, "value": 30} for s in self.stations]
        result = planner.estimate_route(route(1200), "pm_25", 23 * 60 + 50, 4,
            {("pm_25", False, 23): self.stations, ("pm_25", True, 0): later})
        self.assertAlmostEqual(result["exposure"], 400)

    def test_missing_support_is_not_treated_as_clean_air(self):
        result = planner.estimate_route(route(1200), "pm_25", 7 * 60 + 50, 0, {("pm_25", False, 7): self.stations})
        self.assertEqual(result["air_coverage_pct"], 50)
        self.assertIsNone(result["exposure"])
        self.assertFalse(result["air_complete"])
        self.assertTrue(any(sample["value"] is None for sample in result["samples"]))

    def test_requires_two_nearby_stations(self):
        self.assertIsNone(planner.concentration([-74.09, 4.65], self.stations[:1])[0])
        self.assertIsNone(planner.concentration([-74.23, 4.49], self.stations)[0])

    def test_air_recommendation_requires_comparable_coverage(self):
        full = {"id": "a", "duration_s": 600, "air_complete": True, "exposure": 100}
        partial = {"id": "b", "duration_s": 500, "air_complete": False, "exposure": None}
        self.assertEqual(planner.rank_routes([full, partial]), {"fastest": "b", "exposure": None, "balanced": None})

    def test_longer_cleaner_route_can_accumulate_more_exposure(self):
        a = {"id": "short", "duration_s": 600, "air_complete": True, "exposure": 100}
        b = {"id": "long", "duration_s": 1200, "air_complete": True, "exposure": 120}
        self.assertEqual(planner.rank_routes([a, b])["exposure"], "short")


class ProviderTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_bounds_and_finite_coordinates(self):
        for value in ("NaN,4.6", "-74.1,Infinity", "-80,4.6", "4.6,-74.1", "bad"):
            with self.assertRaises(ValueError):
                planner.point(value)

    def test_provider_failure_is_503(self):
        with patch.object(planner, "bicycle_routes", side_effect=planner.ProviderUnavailable("provider_unavailable")):
            response = compare(RequestFactory().get("/api/routes/compare/", {"origin": "-74.09,4.65", "destination": "-74.06,4.62"}))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.content)["error"], "provider_unavailable")

    def test_bad_query_does_not_call_routing_provider(self):
        with patch.object(planner, "remote_json") as remote:
            response = compare(RequestFactory().get("/api/routes/compare/", {"origin": "bad", "destination": "-74.06,4.62"}))
        self.assertEqual(response.status_code, 400)
        remote.assert_not_called()

    def test_geocoding_is_cached_and_outside_results_filtered(self):
        payload = {"features": [{"properties": {"name": "Parque"}, "geometry": {"coordinates": [-74.09, 4.65]}},
                                 {"properties": {"name": "Other city"}, "geometry": {"coordinates": [-75, 6]}}]}
        with patch.object(planner, "remote_json", return_value=payload) as remote:
            first = planner.search_places("Parque Bogotá")
            second = planner.search_places("Parque Bogotá")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 1)
        remote.assert_called_once()

    def test_search_requires_explicit_valid_text(self):
        response = places(RequestFactory().get("/api/routes/places/", {"q": "a"}))
        self.assertEqual(response.status_code, 400)

    def test_duplicate_geometries_are_not_invented_as_alternatives(self):
        payload = {"features": [{"geometry": {"type": "LineString", "coordinates": route()["coordinates"]},
                                "properties": {"total-time": "600", "track-length": "1110", "times": [0, 600]}}]}
        with patch.object(planner, "remote_json", return_value=payload):
            result = planner.bicycle_routes([-74.09, 4.65], [-74.08, 4.65])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["duration_s"], 600)

    def test_invalid_provider_times_use_distance_proportions(self):
        payload = {"features": [{"geometry": {"type": "LineString", "coordinates": route()["coordinates"]},
                                "properties": {"total-time": "600", "track-length": "1110", "times": [500, 100]}}]}
        result = planner.normalize_route(payload, [-74.09, 4.65], [-74.08, 4.65])
        self.assertEqual(result["times"], [0, 600])


if __name__ == "__main__":
    unittest.main()
