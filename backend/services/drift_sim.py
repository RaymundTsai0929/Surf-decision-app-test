"""SAR drift simulation using vector sum of Swell1, Swell2, and wind forces."""
import math
from typing import TypedDict
from services.cwa_client import fetch_conditions, SPOT_POINT_IDS


class TrajectoryPoint(TypedDict):
    lat: float
    lng: float


class DriftResult(TypedDict):
    speed_ms: float
    trajectory: list[TrajectoryPoint]
    endpoint_dangerous: bool


# Earth radius in metres
_R = 6_371_000
# Simulation step in seconds
_STEP_S = 60
# Simulation duration in seconds (1 hour)
_DURATION_S = 3600
# Danger proximity threshold in metres
_DANGER_RADIUS_M = 50

# Dangerous objects per spot — mirrors frontend/src/data/spots.ts
_DANGER_ZONES: dict[str, list[dict]] = {
    "wushih-north": [{"lat": 24.8690, "lng": 121.8570, "radius": 50}],
    "wushih-long":  [{"lat": 24.8630, "lng": 121.8580, "radius": 50}],
    "shuangshi":    [{"lat": 24.8210, "lng": 121.8340, "radius": 60}],
    "honeymoon":    [{"lat": 24.7920, "lng": 121.8190, "radius": 40},
                     {"lat": 24.7880, "lng": 121.8180, "radius": 40}],
    "jialeshuei":   [{"lat": 21.9060, "lng": 120.8640, "radius": 50}],
    "wuwei":        [{"lat": 24.5315, "lng": 121.8490, "radius": 50}],
}


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return 2 * _R * math.asin(math.sqrt(a))


def _deg_to_rad(d: float) -> float:
    return math.radians(d)


def _vector_sum(forces: list[tuple[float, float]]) -> tuple[float, float]:
    """Sum (speed, direction_deg_from_north) pairs into (vx, vy) then back."""
    vx = sum(s * math.sin(_deg_to_rad(d)) for s, d in forces)
    vy = sum(s * math.cos(_deg_to_rad(d)) for s, d in forces)
    speed = math.hypot(vx, vy)
    direction = math.degrees(math.atan2(vx, vy)) % 360
    return speed, direction


def _advance(lat: float, lng: float, speed_ms: float, direction_deg: float, dt_s: float) -> tuple[float, float]:
    dist = speed_ms * dt_s
    bearing = math.radians(direction_deg)
    lat_r = math.radians(lat)
    lng_r = math.radians(lng)
    new_lat_r = math.asin(math.sin(lat_r) * math.cos(dist / _R)
                          + math.cos(lat_r) * math.sin(dist / _R) * math.cos(bearing))
    new_lng_r = lng_r + math.atan2(
        math.sin(bearing) * math.sin(dist / _R) * math.cos(lat_r),
        math.cos(dist / _R) - math.sin(lat_r) * math.sin(new_lat_r),
    )
    return math.degrees(new_lat_r), math.degrees(new_lng_r)


def _is_dangerous(lat: float, lng: float, spot: str) -> bool:
    zones = _DANGER_ZONES.get(spot, [])
    for z in zones:
        if _haversine(lat, lng, z["lat"], z["lng"]) <= z["radius"]:
            return True
    return False


async def simulate_drift(lat: float, lng: float, spot: str) -> DriftResult:
    cwa = await fetch_conditions(spot)
    snap = cwa.get("snapshot", {})

    wind_speed = snap.get("wind_speed") or 0.0
    wind_dir = snap.get("wind_direction") or 0.0
    wave_height = snap.get("wave_height") or 0.0
    wave_dir = snap.get("wave_direction") or 0.0

    # Approximate swell speed from wave height (simplified deep-water relation)
    swell1_speed = wave_height * 0.8
    swell2_speed = wave_height * 0.3
    swell2_dir = (wave_dir + 30) % 360
    wind_drift = wind_speed * 0.03  # ~3% wind leeway

    forces = [
        (swell1_speed, wave_dir),
        (swell2_speed, swell2_dir),
        (wind_drift, wind_dir),
    ]
    result_speed, result_dir = _vector_sum(forces)

    trajectory: list[TrajectoryPoint] = [{"lat": lat, "lng": lng}]
    cur_lat, cur_lng = lat, lng
    steps = _DURATION_S // _STEP_S
    endpoint_dangerous = False

    for _ in range(steps):
        cur_lat, cur_lng = _advance(cur_lat, cur_lng, result_speed, result_dir, _STEP_S)
        trajectory.append({"lat": cur_lat, "lng": cur_lng})
        if _is_dangerous(cur_lat, cur_lng, spot):
            endpoint_dangerous = True
            break

    if not endpoint_dangerous:
        endpoint_dangerous = _is_dangerous(cur_lat, cur_lng, spot)

    return {
        "speed_ms": round(result_speed, 2),
        "trajectory": trajectory,
        "endpoint_dangerous": endpoint_dangerous,
    }
