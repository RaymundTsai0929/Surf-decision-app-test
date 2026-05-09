"""
Swelleye（swelleye.com）「浪況直播」頁面列出的浪點，與官網衝浪預報／直播連動。
座標為浪點沙灘／港口附近概略位置，供 Windy 地圖置中；精確位置以 Swelleye 地圖為準。

來源（2026）：https://swelleye.com/surfcams
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class SwelleyeSpot:
    """單一浪點：顯示名稱、官網 slug、概略經緯度、區域標籤（方便選單分群）。"""

    name: str
    slug: str
    lat: float
    lon: float
    region: str

    @property
    def swelleye_cam_url(self) -> str:
        return f"https://swelleye.com/surf-spots/{self.slug}#cam-report"

    @property
    def label(self) -> str:
        return f"{self.name}（{self.region}）"


# 順序與官網「浪況直播」縮圖列相同；經緯度為概略值。
SWELLEYE_LIVE_CAM_SPOTS: Final[tuple[SwelleyeSpot, ...]] = (
    SwelleyeSpot("金山", "jinshan", 25.2210, 121.6360, "北海岸"),
    SwelleyeSpot("翡翠灣", "greenbay", 25.1310, 121.6920, "北海岸"),
    SwelleyeSpot("福隆", "fulong", 25.0160, 121.9440, "東北角"),
    SwelleyeSpot("大溪", "daxi", 24.9680, 121.8880, "東北角"),
    SwelleyeSpot("雙獅", "double-lions", 24.8320, 121.7920, "宜蘭"),
    SwelleyeSpot("烏石港", "wushi-north", 24.8712, 121.8356, "宜蘭"),
    SwelleyeSpot("北濱", "beibin", 23.9830, 121.6010, "花蓮"),
    SwelleyeSpot("東河", "donghe", 22.9730, 121.3040, "台東"),
    SwelleyeSpot("金樽", "jinzun", 23.1180, 121.2850, "台東"),
    SwelleyeSpot("佳樂水", "jialeshui", 22.0570, 120.8540, "恆春半島"),
    SwelleyeSpot("南灣", "nanwan", 21.9590, 120.7460, "恆春半島"),
    SwelleyeSpot("旗津", "qijin", 22.6080, 120.2650, "高雄"),
    SwelleyeSpot("松柏港", "songbai", 24.4318, 120.6179, "台中／中西部"),
)


def spots_by_region() -> tuple[SwelleyeSpot, ...]:
    """依區域名稱排序後回傳（同區內維持列表順序）。"""
    order = (
        "北海岸",
        "東北角",
        "宜蘭",
        "花蓮",
        "台東",
        "恆春半島",
        "高雄",
        "台中／中西部",
    )
    rank = {r: i for i, r in enumerate(order)}
    return tuple(sorted(SWELLEYE_LIVE_CAM_SPOTS, key=lambda s: (rank.get(s.region, 99), s.name)))
