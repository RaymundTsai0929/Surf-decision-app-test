"""
將鄉鎮沿海 F-D0047-095 之風向／浪向／流向中文描述轉成度數（自正北順時針 0–360）。

氣象上「風向」為風之來向；海流「流向」為流之去向（與本專案 drift 腳本約定一致）。
"""

from __future__ import annotations

import re
from typing import Optional

# 16 方位中心角（自北順時針）
_CARDINAL_DEG = {
    "北": 0.0,
    "北北東": 22.5,
    "東北": 45.0,
    "東北東": 67.5,
    "東": 90.0,
    "東南東": 112.5,
    "東南": 135.0,
    "南南東": 157.5,
    "南": 180.0,
    "南南西": 202.5,
    "西南": 225.0,
    "西南西": 247.5,
    "西": 270.0,
    "西北西": 292.5,
    "西北": 315.0,
    "西北北": 337.5,
}

# 「偏X」簡化為該象限代表角（與官網文字欄位相容）
_BIAS_DEG = {
    "偏北": 10.0,
    "偏東北": 40.0,
    "偏東": 80.0,
    "偏東南": 130.0,
    "偏南": 170.0,
    "偏西南": 220.0,
    "偏西": 260.0,
    "偏西北": 310.0,
}


def _norm(s: str) -> str:
    t = (s or "").strip()
    t = re.sub(r"\s+", "", t)
    return t


def cwa_text_to_meteorological_from_deg(text: Optional[str]) -> float:
    """
    風、浪之「來向」：例如「東南風」「偏東」→ 風／浪從該方位吹來之角度（度）。
    無法辨識時回傳 0.0。
    """
    t = _norm(text or "")
    if not t or t in ("靜風", "無風", "旋轉風"):
        return 0.0
    if t.endswith("風"):
        t = t[:-1]
    # 先比對較長鍵
    for table in (_BIAS_DEG, _CARDINAL_DEG):
        keys = sorted(table.keys(), key=len, reverse=True)
        for k in keys:
            if k in t or t == k:
                return float(table[k])
    return 0.0


def cwa_text_to_current_to_deg(text: Optional[str]) -> float:
    """
    海流「去向」：例如「偏北」表示大致往北流之方位角（度）。
    """
    t = _norm(text or "")
    if not t:
        return 0.0
    keys = sorted({**_BIAS_DEG, **_CARDINAL_DEG}.keys(), key=len, reverse=True)
    for k in keys:
        if k in t or t == k:
            v = _BIAS_DEG.get(k)
            if v is not None:
                return float(v)
            return float(_CARDINAL_DEG[k])
    return 0.0


def safe_float(x: Optional[str | float | int], default: float = 0.0) -> float:
    if x is None:
        return default
    try:
        return float(str(x).strip())
    except (TypeError, ValueError):
        return default


def build_drift_injection_from_coastal_row(row: dict) -> dict:
    """
    將 get_coastal_timeseries 單筆轉成注入 drift 疊圖的純 JSON（給前端 sarDriftMs 使用）。
    """
    ws = safe_float(row.get("wind_speed"))
    wh = safe_float(row.get("wave_height"))
    cs = safe_float(row.get("current_speed"))
    wf = cwa_text_to_meteorological_from_deg(row.get("wind_dir"))
    wav_f = cwa_text_to_meteorological_from_deg(row.get("wave_dir"))
    cto = cwa_text_to_current_to_deg(row.get("current_dir"))
    return {
        "windSpeed": ws,
        "windFromDeg": wf,
        "waveHeight": wh,
        "waveFromDeg": wav_f,
        "currentSpeedMps": cs,
        "currentToDeg": cto,
        "dataTime": row.get("start_time") or "",
        "source": "CWA-F-D0047-095",
    }
