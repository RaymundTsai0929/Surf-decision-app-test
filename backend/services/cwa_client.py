import os
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

CWA_API_KEY = os.getenv("CWA_API_KEY", "")
CWA_BASE = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

SPOT_POINT_IDS: dict[str, str] = {
    "wushih-north": "6502600C01",
    "wushih-long": "6502600C01",
    "shuangshi": "6502600C01",
    "honeymoon": "6502600C02",
    "jialeshuei": "6500900C01",
    "wuwei": "6502600C03",
}


async def fetch_conditions(spot: str) -> dict:
    point_id = SPOT_POINT_IDS.get(spot)
    if not point_id:
        return {"error": f"Unknown spot: {spot}", "hourly": []}

    params = {
        "Authorization": CWA_API_KEY,
        "LocationId": point_id,
        "sort": "time",
    }

    async with httpx.AsyncClient(timeout=10, verify=False) as client:
        resp = await client.get(f"{CWA_BASE}/O-A0014-001", params=params)
        resp.raise_for_status()
        raw = resp.json()

    return _parse_coastal(raw, spot)


def _parse_coastal(raw: dict, spot: str) -> dict:
    try:
        records = raw["records"]["Station"]
        if not records:
            return {"spot": spot, "hourly": []}

        station = records[0]
        weather = station.get("WeatherElement", {})

        def val(key: str):
            v = weather.get(key, {}).get("Value")
            try:
                return float(v) if v not in (None, "", "-99", -99) else None
            except (TypeError, ValueError):
                return None

        snapshot = {
            "wave_height": val("WaveHeight"),
            "wave_period": val("WavePeriod"),
            "wave_direction": val("WaveDirection"),
            "wind_speed": val("WindSpeed"),
            "wind_direction": val("WindDirection"),
            "gust": val("GustSpeed"),
            "air_temp": val("AirTemperature"),
            "sea_temp": val("SeaTemperature"),
            "tide": val("TideHeight"),
        }

        return {"spot": spot, "snapshot": snapshot, "hourly": [snapshot]}
    except (KeyError, IndexError):
        return {"spot": spot, "hourly": []}
