import os
import requests
from dotenv import load_dotenv
import urllib3

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None
import json
from difflib import get_close_matches
from typing import Any, List, Optional

# 載入環境變數
load_dotenv()

# Streamlit 側邊欄顯示名 → F-A0012-001 官方 LocationName（見 data/氣象資料/F-A0012-001.json）。
# 若未對照，線上 API 可能查無；本機快取會用字串模糊比對，易誤配（例如「東港大鵬灣」曾被配到「臺東大武沿海」）。
F_A0012_LOCATION_ALIASES: dict[str, str] = {
    "東港大鵬灣": "高雄枋寮沿海",
    "雙獅海灘": "宜蘭蘇澳沿海",
    "烏石港": "宜蘭蘇澳沿海",
    "蜜月灣": "宜蘭蘇澳沿海",
    "佳樂水": "枋寮恆春沿海",
    "金樽": "成功臺東沿海",
}

# 浪點（UI）→ F-D0047-095「鄉鎮沿海」官方 locationName（與官網鄉鎮沿海地圖一致，逐 3 小時、空間較精細）。
FD047_COASTAL_BY_SPOT: dict[str, str] = {
    "東港大鵬灣": "東港鎮沿海",
    "雙獅海灘": "貢寮區沿海",
    "烏石港": "頭城鎮沿海",
    "蜜月灣": "頭城鎮沿海",
    "佳樂水": "滿州鄉沿海",
    "金樽": "東河鄉沿海",
}


class CWAService:
    def __init__(self) -> None:
        self.auth_code = os.getenv("CWA_AUTH_CODE")
        # 近海海象預報-未來2天預報 (F-A0012-001)
        self.near_sea_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-A0012-001"
        # 鄉鎮沿海逐三小時 (F-D0047-095)。資料集類型為 rawData 時，實務上以 fileapi 可取回；
        # rest/datastore 對部分授權會回 404，故以 fileapi 為主。
        self.coastal_fileapi_url = (
            "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-D0047-095"
        )
        self.coastal_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-095"
        self._verify = certifi.where() if certifi else True
        self._near_sea_cache_path = os.path.join(
            os.path.dirname(__file__),
            "data",
            "氣象資料",
            "F-A0012-001.json",
        )

    def _parse_cached_near_sea_report(
        self,
        data: dict,
        location_name: str,
        display_name: Optional[str] = None,
    ) -> str:
        """
        從本機已下載的快取檔（F-A0012-001.json）解析出簡要文字。
        注意：快取檔的結構是 cwaopendata.Dataset.Locations.Location[].WeatherElement[] ...
        """
        try:
            locations = (
                data.get("cwaopendata", {})
                .get("Dataset", {})
                .get("Locations", {})
                .get("Location", [])
            )
            if not locations:
                raise KeyError("cached locations missing")

            available_names = [loc.get("LocationName") for loc in locations if loc.get("LocationName")]
            chosen = None
            if location_name in available_names:
                chosen = location_name
            else:
                # 僅在無法精確對應時才模糊比對；門檻提高以降低「東港」誤配「臺東大武」這類錯誤。
                matches = get_close_matches(location_name, available_names, n=1, cutoff=0.55)
                chosen = matches[0] if matches else available_names[0]

            loc = next(loc for loc in locations if loc.get("LocationName") == chosen)
            weather_elements = loc.get("WeatherElement", [])

            def get_elem_value(element_name: str, idx: int = 0):
                elem = next((e for e in weather_elements if e.get("ElementName") == element_name), None)
                if not elem:
                    return None
                time_arr = elem.get("Time") or []
                if idx >= len(time_arr):
                    idx = 0
                ev = time_arr[idx].get("ElementValue") or {}
                return ev

            wx_ev = get_elem_value("天氣現象")
            wind_ev = get_elem_value("風向描述")
            beaufort_ev = get_elem_value("蒲福風級描述")
            wave_h_ev = get_elem_value("浪高描述")
            wave_t_ev = get_elem_value("浪型描述")

            wind_dir = wind_ev.get("WindDirectionDescription") if wind_ev else None
            wind_force = beaufort_ev.get("BeaufortScaleDescription") if beaufort_ev else None
            wave_height = wave_h_ev.get("WaveHeightDescription") if wave_h_ev else None
            wave_type = wave_t_ev.get("WaveTypeDescription") if wave_t_ev else None
            weather = wx_ev.get("Weather") if wx_ev else None

            label = display_name or chosen
            return (
                f"【近海海象預報（本機快取）- {label}】\n"
                f"（署方區域名：{chosen}）\n"
                + (f"天氣：{weather}\n" if weather else "")
                + (f"浪高：{wave_height}\n" if wave_height else "")
                + (f"浪況：{wave_type}\n" if wave_type else "")
                + (f"風向：{wind_dir}\n" if wind_dir else "")
                + (f"風力：{wind_force}\n" if wind_force else "")
            )
        except Exception:
            return "錯誤：本機快取檔解析失敗。"

    def _get_json(self, url: str, params: dict) -> dict:
        """
        取得 JSON；若遇到憑證驗證失敗，先用 certifi CA bundle 再重試。
        若仍失敗（原型情境），最後一次改為 verify=False 以確保功能可跑。
        """
        try:
            resp = requests.get(url, params=params, timeout=20, verify=self._verify)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.SSLError:
            # 原型暫時用：避免因環境缺 CA bundle/憑證鏈解析問題導致功能完全中斷。
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            resp = requests.get(url, params=params, timeout=20, verify=False)
            resp.raise_for_status()
            return resp.json()

    # --- 既有：近海海象簡要文字（保留給目前 Streamlit 側邊欄使用） ---
    def get_ocean_forecast(self, location_name: str = "宜蘭頭城近海") -> str:
        """
        F-A0012-001 近海海象預報（兩天，區域較大）。
        回傳簡要文字描述。
        """
        if not self.auth_code:
            return "錯誤：找不到 CWA_AUTH_CODE，請檢查 .env 檔案。"

        api_location = F_A0012_LOCATION_ALIASES.get(location_name, location_name)

        params = {
            "Authorization": self.auth_code,
            "format": "JSON",
            "locationName": api_location,
        }

        try:
            data = self._get_json(self.near_sea_url, params)

            if not data.get("success") == "true":
                return f"API 請求失敗：{data.get('message')}"

            raw_locs = data["records"]["locations"]["location"]
            locs = raw_locs if isinstance(raw_locs, list) else [raw_locs]
            location = next(
                (loc for loc in locs if loc.get("locationName") == api_location),
                locs[0],
            )
            forecasts = location["time"][0]["element"]

            wave_height = next(
                item for item in forecasts if item["elementName"] == "WaveHeight"
            )["elementValue"][0]["value"]
            wave_type = next(
                item for item in forecasts if item["elementName"] == "WaveType"
            )["elementValue"][0]["value"]
            wind_dir = next(
                item for item in forecasts if item["elementName"] == "WindDirection"
            )["elementValue"][0]["value"]
            wind_force = next(
                item for item in forecasts if item["elementName"] == "WindForce"
            )["elementValue"][0]["value"]

            zone = location.get("locationName", api_location)
            title = (
                f"【近海海象預報 - {location_name}】\n"
                f"（署方區域名：{zone}）\n"
            )
            report = (
                title
                + f"浪高：{wave_height} 公尺\n"
                f"浪況：{wave_type}\n"
                f"風向：{wind_dir}\n"
                f"風力：{wind_force} 級\n"
            )
            return report

        except Exception as e:
            # 線上取用失敗時，用本機快取檔兜底，避免聊天模型誤判「沒有即時資料」
            try:
                if os.path.exists(self._near_sea_cache_path):
                    with open(self._near_sea_cache_path, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    return self._parse_cached_near_sea_report(
                        cached, api_location, display_name=location_name
                    )
            except Exception:
                pass
            return f"抓取近海海象資料時發生錯誤: {str(e)}"

    @staticmethod
    def _fd047_extract_location(data: dict) -> dict:
        """自 F-D0047-095 JSON 取出第一筆 location（相容大小寫／巢狀差異）。"""
        rec = data.get("records") or {}
        # 常見：records.locations.location[]
        lr = rec.get("locations")
        if lr is not None:
            if isinstance(lr, dict):
                raw = lr.get("location") or lr.get("Location")
            elif isinstance(lr, list) and lr:
                block = lr[0]
                raw = block.get("location") or block.get("Location") if isinstance(block, dict) else None
            else:
                raw = None
            if isinstance(raw, list) and raw:
                return raw[0]
            if isinstance(raw, dict):
                return raw
        # 另式：records.Locations.Location[]
        loc2 = rec.get("Locations") or {}
        raw2 = loc2.get("Location") or loc2.get("location")
        if isinstance(raw2, list) and raw2:
            return raw2[0]
        if isinstance(raw2, dict):
            return raw2
        raise RuntimeError("CWA 鄉鎮沿海回傳格式異常（找不到 location）")

    @staticmethod
    def _fd047_elem_dict(time_slot: dict) -> dict:
        ev = time_slot.get("elementValue") or time_slot.get("ElementValue")
        if isinstance(ev, list) and ev and isinstance(ev[0], dict):
            return ev[0]
        if isinstance(ev, dict):
            return ev
        return {}

    @classmethod
    def _fd047_pick(cls, elems: dict[str, list], idx: int, *elem_names: str) -> Optional[str]:
        for name in elem_names:
            arr = elems.get(name)
            if not arr or idx >= len(arr):
                continue
            d = cls._fd047_elem_dict(arr[idx])
            v = d.get("value")
            if v is None:
                v = d.get("Value")
            if v is not None and str(v).strip() != "":
                return str(v).strip()
            if d:
                for x in d.values():
                    if x is not None and str(x).strip() != "":
                        return str(x).strip()
        return None

    @staticmethod
    def _fd047_scalar_from_ev(ev_dict: dict, *keys: str) -> Optional[str]:
        if not ev_dict:
            return None
        for k in keys:
            v = ev_dict.get(k)
            if v is not None and str(v).strip() not in ("", "None"):
                return str(v).strip()
        return None

    def _fd047_ev_dict_at(self, elems: dict[str, list], idx: int, *elem_names: str) -> dict:
        for n in elem_names:
            arr = elems.get(n)
            if arr and idx < len(arr):
                return self._fd047_elem_dict(arr[idx])
        return {}

    @staticmethod
    def _fd047_find_location_in_fileapi(data: dict, location_name: str) -> dict:
        try:
            raw = data["cwaopendata"]["Dataset"]["Locations"]["Location"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("F-D0047-095 fileapi 回傳缺少 cwaopendata.Dataset.Locations") from exc
        locs = raw if isinstance(raw, list) else [raw]
        for loc in locs:
            if loc.get("LocationName") == location_name:
                return loc
        names = [x.get("LocationName") for x in locs if x.get("LocationName")]
        matches = get_close_matches(location_name, names, n=1, cutoff=0.55)
        if matches:
            m = matches[0]
            return next(x for x in locs if x.get("LocationName") == m)
        raise RuntimeError(f"鄉鎮沿海 JSON 中找不到地點「{location_name}」")

    def _fd047_series_from_location_dict(self, location: dict) -> List[dict[str, Any]]:
        raw_we = location.get("WeatherElement") or location.get("weatherElement") or []
        elems: dict[str, list] = {}
        for elem in raw_we:
            en = elem.get("ElementName") or elem.get("elementName")
            if not en:
                continue
            times = elem.get("Time") or elem.get("time") or []
            elems[en] = times

        axis = (
            elems.get("風速")
            or elems.get("WindSpeed")
            or elems.get("浪高")
            or elems.get("WaveHeight")
        )
        if not axis and elems:
            axis = max(elems.values(), key=lambda a: len(a) if isinstance(a, list) else 0)
        if not axis:
            return []

        series: List[dict[str, Any]] = []
        for i, t in enumerate(axis):
            start = t.get("DataTime") or t.get("startTime") or t.get("start_time")
            end = t.get("endTime") or t.get("end_time") or ""

            ws = self._fd047_ev_dict_at(elems, i, "風速", "WindSpeed")
            wd = self._fd047_ev_dict_at(elems, i, "風向", "WindDirection")
            wh = self._fd047_ev_dict_at(elems, i, "浪高", "WaveHeight")
            wvd = self._fd047_ev_dict_at(elems, i, "浪向", "WaveDirection")
            wp = self._fd047_ev_dict_at(elems, i, "浪週期", "週期", "WavePeriod")
            cs = self._fd047_ev_dict_at(elems, i, "流速", "CurrentSpeed")
            cd = self._fd047_ev_dict_at(elems, i, "流向", "CurrentDirection")
            wx = self._fd047_ev_dict_at(elems, i, "天氣現象", "天氣", "Weather")

            series.append(
                {
                    "start_time": start,
                    "end_time": end,
                    "wind_speed": self._fd047_scalar_from_ev(ws, "WindSpeed", "value", "Value"),
                    "wind_beaufort": self._fd047_scalar_from_ev(
                        ws, "BeaufortScale", "value", "Value"
                    ),
                    "wind_dir": self._fd047_scalar_from_ev(wd, "WindDirection", "value", "Value"),
                    "wave_height": self._fd047_scalar_from_ev(wh, "WaveHeight", "value", "Value"),
                    "wave_dir": self._fd047_scalar_from_ev(wvd, "WaveDirection", "value", "Value"),
                    "wave_period": self._fd047_scalar_from_ev(wp, "WavePeriod", "value", "Value"),
                    "current_speed": self._fd047_scalar_from_ev(
                        cs, "OceanCurrentSpeed", "value", "Value"
                    ),
                    "current_dir": self._fd047_scalar_from_ev(
                        cd, "OceanCurrentDirection", "value", "Value"
                    ),
                    "weather": self._fd047_scalar_from_ev(wx, "Weather", "value", "Value"),
                }
            )
        return series

    def get_coastal_timeseries(self, location_name: str) -> List[dict[str, Any]]:
        """
        從 F-D0047-095 取得指定鄉鎮沿海代表點的逐三小時海象預報。

        優先使用 fileapi（rawData）；失敗再嘗試 rest/datastore。

        回傳 list[dict]：start_time, end_time, wind_speed, wind_beaufort, wind_dir,
        wave_height, wave_dir, wave_period, current_speed, current_dir, weather
        """
        if not self.auth_code:
            raise RuntimeError("找不到 CWA_AUTH_CODE，請檢查 .env 檔案。")

        base = {"Authorization": self.auth_code, "format": "JSON"}
        errs: list[str] = []

        try:
            data = self._get_json(self.coastal_fileapi_url, base)
            if isinstance(data, dict) and "cwaopendata" in data:
                loc = self._fd047_find_location_in_fileapi(data, location_name)
                return self._fd047_series_from_location_dict(loc)
            errs.append("fileapi：回傳非 cwaopendata 格式")
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            errs.append(f"fileapi HTTP {code}")
        except Exception as e:
            errs.append(f"fileapi：{e}")

        try:
            data = self._get_json(
                self.coastal_url, {**base, "locationName": location_name}
            )
            if not data.get("success") == "true":
                errs.append(f"datastore：{data.get('message')}")
            else:
                loc = self._fd047_extract_location(data)
                return self._fd047_series_from_location_dict(loc)
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            errs.append(f"datastore HTTP {code}")
        except Exception as e:
            errs.append(f"datastore：{e}")

        raise RuntimeError("；".join(errs) if errs else "鄉鎮沿海資料取得失敗")

    @staticmethod
    def _format_coastal_series(
        spot_label: str,
        cwa_location_name: str,
        series: List[dict[str, Any]],
        max_slots: int = 16,
    ) -> str:
        """組成給人讀／給 LLM 用的文字（預設約 48 小時內 16 個時段）。"""
        lines = [
            f"【鄉鎮沿海預報｜F-D0047-095｜{cwa_location_name}】",
            f"（對應浪點：{spot_label}；逐 3 小時；"
            f"來源：中央氣象署 fileapi／opendataapi，與資料頁 rawData JSON 相同管道）",
            "",
        ]
        for row in series[:max_slots]:
            lines.append(
                f"— {row.get('start_time', '')} ~ {row.get('end_time', '')} —"
            )
            if row.get("weather"):
                lines.append(f"  天氣：{row['weather']}")
            wparts = []
            if row.get("wind_speed") is not None:
                wparts.append(f"風速 {row['wind_speed']} m/s")
            if row.get("wind_beaufort"):
                wparts.append(f"風級 {row['wind_beaufort']}")
            if row.get("wind_dir"):
                wparts.append(f"風向 {row['wind_dir']}")
            if wparts:
                lines.append("  " + "，".join(wparts))
            hparts = []
            if row.get("wave_height") is not None:
                hparts.append(f"浪高 {row['wave_height']} m")
            if row.get("wave_dir"):
                hparts.append(f"浪向 {row['wave_dir']}")
            if row.get("wave_period") is not None:
                hparts.append(f"週期 {row['wave_period']} s")
            if hparts:
                lines.append("  " + "，".join(hparts))
            cparts = []
            if row.get("current_speed") is not None:
                cparts.append(f"流速 {row['current_speed']}")
            if row.get("current_dir"):
                cparts.append(f"流向 {row['current_dir']}")
            if cparts:
                lines.append("  " + "，".join(cparts))
            lines.append("")
        if len(series) > max_slots:
            lines.append(f"（僅列出前 {max_slots} 個時段，API 共 {len(series)} 筆）")
        return "\n".join(lines).strip()

    def get_surf_spot_forecast(self, ui_spot_name: str) -> str:
        """
        優先使用 F-D0047-095 鄉鎮沿海（最精細）；失敗時改為 F-A0012-001 近海大區＋本機快取。
        供 Streamlit 側邊欄與對話上下文使用。
        """
        if not self.auth_code:
            return "錯誤：找不到 CWA_AUTH_CODE，請檢查 .env 檔案。"

        coastal = FD047_COASTAL_BY_SPOT.get(ui_spot_name)
        if coastal:
            try:
                s = self.get_coastal_timeseries(coastal)
                if s:
                    return self._format_coastal_series(ui_spot_name, coastal, s)
            except Exception as e:
                note = (
                    f"【鄉鎮沿海預報暫不可用】{coastal}：{e}\n"
                    f"（F-D0047-095 已改走 fileapi；若仍失敗請確認授權碼與網路。）\n"
                    f"改以近海大區備援如下。\n\n"
                )
                return note + self.get_ocean_forecast(ui_spot_name)
        return self.get_ocean_forecast(ui_spot_name)


if __name__ == "__main__":
    service = CWAService()
    print(service.get_surf_spot_forecast("烏石港"))
