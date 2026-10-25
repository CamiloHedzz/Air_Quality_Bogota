"""Bicycle alternatives and exploratory historical exposure, never live air quality."""
from functools import lru_cache
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache

ROOT = Path(__file__).resolve().parents[1]
BBOX = (-74.24, 4.48, -73.99, 4.84)
MAX_RADIUS_KM = 5
MIN_NEIGHBORS = 2
USER_AGENT = "AirQualityBogota/1.0 (experimental bicycle route planner)"


class ProviderUnavailable(Exception):
    pass


def point(value):
    try:
        lon, lat = [float(item) for item in value.split(",")]
    except (ValueError, AttributeError):
        raise ValueError("invalid_point") from None
    if not all(math.isfinite(v) for v in (lon, lat)) or not (BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]):
        raise ValueError("outside_bogota")
    return [round(lon, 6), round(lat, 6)]


def distance(a, b):
    """Haversine, km; points follow GeoJSON longitude, latitude."""
    lon1, lat1, lon2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    term = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(term)))


def remote_json(url, timeout=15):
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError("oversized_response")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("invalid_response")
        return payload
    except (OSError, ValueError) as error:
        raise ProviderUnavailable("provider_unavailable") from error


def search_places(query):
    query = " ".join(query.split())
    if not 3 <= len(query) <= 160:
        raise ValueError("invalid_search")
    key = "cycling:place:" + sha256(query.casefold().encode()).hexdigest()
    result = cache.get(key)
    if result is not None:
        return result
    # Explicit searches only, cached; a shared Django cache keeps this gate global.
    if not cache.add("cycling:place-rate", True, timeout=2):
        raise ProviderUnavailable("search_busy")
    params = {"q": query, "lat": 4.65, "lon": -74.08, "bbox": ",".join(map(str, BBOX)), "limit": 6}
    payload = remote_json(os.environ.get("AIRQUALITY_PHOTON_URL", "https://photon.komoot.io/api/") + "?" + urlencode(params))
    result = []
    for feature in payload.get("features", []):
        try:
            coords = point(",".join(map(str, feature["geometry"]["coordinates"][:2])))
            props = feature["properties"]
            name = props.get("name") or props.get("street") or "Bogotá"
            address = " · ".join(dict.fromkeys(str(v) for v in [props.get("street"), props.get("housenumber"), props.get("district"), props.get("city")] if v))
            result.append({"label": str(name)[:180], "detail": address[:240], "coordinates": coords})
        except (KeyError, TypeError, ValueError):
            continue
    cache.set(key, result, timeout=86400)
    return result


def normalize_route(payload, origin, destination):
    try:
        feature = next(f for f in payload["features"] if f.get("geometry", {}).get("type") == "LineString")
        props = feature["properties"]
        coordinates = [point(",".join(map(str, p[:2]))) for p in feature["geometry"]["coordinates"]]
        seconds, meters = float(props["total-time"]), float(props["track-length"])
        times = [float(t) for t in props.get("times", [])]
        if not 2 <= len(coordinates) <= 15000 or not (0 < seconds <= 14400 and 0 < meters <= 50000):
            raise ValueError("invalid_route")
        if distance(origin, coordinates[0]) > .35 or distance(destination, coordinates[-1]) > .35:
            raise ValueError("endpoint_too_far")
        if len(times) != len(coordinates) or not all(math.isfinite(t) for t in times) or any(b < a for a, b in zip(times, times[1:])) or not 0 < times[-1] <= seconds * 1.05:
            # The same bicycle duration, distributed along actual distance.
            lengths = [distance(a, b) for a, b in zip(coordinates, coordinates[1:])]
            total = sum(lengths)
            if total <= 0:
                raise ValueError("invalid_route")
            times, elapsed = [0], 0
            for length in lengths:
                elapsed += seconds * length / total
                times.append(elapsed)
        else:
            times = [max(0, t) * seconds / times[-1] for t in times]
            times[0] = 0
        return {"coordinates": coordinates, "times": times, "distance_m": meters, "duration_s": seconds,
                "access_m": round(1000 * (distance(origin, coordinates[0]) + distance(destination, coordinates[-1])))}
    except (KeyError, TypeError, ValueError, StopIteration) as error:
        raise ProviderUnavailable("invalid_route") from error


def bicycle_routes(origin, destination):
    span = distance(origin, destination)
    if span < .2:
        raise ValueError("points_too_close")
    if span > 25:
        raise ValueError("trip_too_long")
    key = "cycling:geometry:" + sha256(json.dumps([origin, destination]).encode()).hexdigest()
    saved = cache.get(key)
    if saved is not None:
        return saved
    if not cache.add("cycling:router-lock", True, timeout=65):
        raise ProviderUnavailable("router_busy")
    result, signatures = [], set()
    try:
        for index in range(3):
            params = {"lonlats": "|".join(",".join(map(str, p)) for p in [origin, destination]),
                      "profile": "trekking", "alternativeidx": index, "format": "geojson"}
            try:
                payload = remote_json(os.environ.get("AIRQUALITY_BROUTER_URL", "https://brouter.de/brouter") + "?" + urlencode(params))
                route = normalize_route(payload, origin, destination)
            except ProviderUnavailable:
                if not result:
                    raise
                break
            signature = json.dumps(route["coordinates"])
            if signature not in signatures:
                signatures.add(signature)
                result.append({**route, "id": f"route-{index + 1}"})
        cache.set(key, result, timeout=86400)
        return result
    finally:
        cache.delete("cycling:router-lock")


@lru_cache(maxsize=1)
def air_profiles():
    from dash2.rmcab_data import load_samples
    data = load_samples(ROOT / "data/samples/rmcab_2025_q1.csv")
    positions = json.loads((ROOT / "data/references/rmcab_station_locations.json").read_text(encoding="utf-8"))
    locations = {s["station_id"]: s for s in positions["stations"]}
    data["hour"] = data.datetime.dt.hour
    data["weekend"] = data.datetime.dt.dayofweek.ge(5)
    profiles = {}
    for variable in ("pm_25", "pm_10"):
        groups = data.loc[data[variable].notna()].groupby(["station_id", "weekend", "hour"])[variable].agg(["median", "count"])
        for (station, weekend, hour), row in groups.iterrows():
            if station not in locations or row["count"] < 8:
                continue
            location = locations[station]
            profiles.setdefault((variable, bool(weekend), int(hour)), []).append({
                "id": station, "label": location["station_name"], "coordinates": [location["longitude"], location["latitude"]],
                "value": float(row["median"]), "n": int(row["count"])})
    return profiles, {"start": str(data.datetime.min().date()), "end": str(data.datetime.max().date()),
                      "report_days": int(data.report_date.nunique()), "station_source": positions["source_url"]}


def concentration(position, stations):
    nearby = sorted([(distance(position, station["coordinates"]), station) for station in stations], key=lambda item: item[0])
    nearby = [(d, s) for d, s in nearby if d <= MAX_RADIUS_KM][:3]
    if len(nearby) < MIN_NEIGHBORS:
        return None, []
    weights = [1 / max(d, .25) ** 2 for d, _ in nearby]
    estimate = sum(w * station["value"] for w, (_, station) in zip(weights, nearby)) / sum(weights)
    return estimate, [station["id"] for _, station in nearby]


def estimate_route(route, variable, departure, weekday, profiles):
    """Integrate C(t) dt; midpoint samples <= 200m and <= one minute apart."""
    exposure, covered_seconds, station_ids, samples, travelled = 0, 0, set(), [], 0
    for i, (a, b) in enumerate(zip(route["coordinates"], route["coordinates"][1:])):
        start, end = route["times"][i:i + 2]
        dt = end - start
        segment_km = distance(a, b)
        if dt <= 0:
            travelled += segment_km
            continue
        divisions = max(1, math.ceil(segment_km / .2), math.ceil(dt / 60))
        for j in range(divisions):
            fraction = (j + .5) / divisions
            pos = [a[k] + (b[k] - a[k]) * fraction for k in (0, 1)]
            minute = departure + (start + dt * fraction) / 60
            day = (weekday + int(minute // 1440)) % 7
            hour = int(minute // 60) % 24
            value, ids = concentration(pos, profiles.get((variable, day >= 5, hour), []))
            if value is not None:
                exposure += value * dt / divisions / 60
                covered_seconds += dt / divisions
                station_ids.update(ids)
            samples.append({"km": round(travelled + segment_km * fraction, 3),
                            "value": round(value, 2) if value is not None else None})
        travelled += segment_km
    coverage = covered_seconds / route["duration_s"] if route["duration_s"] else 0
    # Never rank partial air coverage as though the missing part were clean.
    complete = coverage >= 1 - 1e-6
    return {**route, "air_coverage_pct": round(coverage * 100, 1), "air_complete": complete,
            "mean_concentration": round(exposure / (covered_seconds / 60), 2) if covered_seconds else None,
            "exposure": round(exposure, 2) if complete else None, "station_ids": sorted(station_ids), "samples": samples}


def rank_routes(routes):
    fastest = min(routes, key=lambda r: r["duration_s"])
    # Comparable support is required for an exposure recommendation across alternatives.
    eligible = routes if all(r["air_complete"] for r in routes) else []
    least = min(eligible, key=lambda r: r["exposure"]) if eligible else None
    balanced = None
    if eligible:
        min_time = fastest["duration_s"]
        min_exposure = max(min(r["exposure"] for r in eligible), .01)
        balanced = min(eligible, key=lambda r: .5 * r["duration_s"] / min_time + .5 * r["exposure"] / min_exposure)
    return {"fastest": fastest["id"], "exposure": least["id"] if least else None, "balanced": balanced["id"] if balanced else None}


def plan(params):
    origin, destination = point(params.get("origin", "")), point(params.get("destination", ""))
    variable = params.get("variable", "pm_25")
    try:
        hour, minute = [int(v) for v in params.get("time", "07:00").split(":")]
        weekday = int(params.get("day", "0"))
    except (ValueError, AttributeError):
        raise ValueError("invalid_time") from None
    if variable not in ("pm_25", "pm_10") or not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= weekday <= 6):
        raise ValueError("invalid_time")
    geometry = bicycle_routes(origin, destination)
    try:
        profiles, source = air_profiles()
    except ValueError as error:
        raise ProviderUnavailable("data_unavailable") from error
    routes = [estimate_route(r, variable, hour * 60 + minute, weekday, profiles) for r in geometry]
    station_ids = {station for r in routes for station in r["station_ids"]}
    stations = {s["id"]: s for group in profiles.values() for s in group if s["id"] in station_ids}
    return {"routes": routes, "recommendations": rank_routes(routes), "source": source,
            "stations": [{k: s[k] for k in ("id", "label", "coordinates")} for s in stations.values()],
            "query": {"origin": origin, "destination": destination, "time": f"{hour:02}:{minute:02}", "day": weekday, "variable": variable},
            "method": {"type": "historical_hourly_idw", "max_radius_km": MAX_RADIUS_KM, "min_stations": MIN_NEIGHBORS,
                       "unit": "µg/m³", "exposure_unit": "µg·min/m³", "live": False, "routing": "BRouter · trekking"}}
