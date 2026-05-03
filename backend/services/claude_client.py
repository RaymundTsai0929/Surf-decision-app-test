"""Gemini API client with per-spot-per-hour memory cache."""
import os
import time
import google.generativeai as genai

_model: genai.GenerativeModel | None = None

def _get_model() -> genai.GenerativeModel:
    global _model
    if _model is None:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        _model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=_SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                max_output_tokens=400,
                temperature=0.3,
            ),
        )
    return _model


_SYSTEM_PROMPT = """你是一位資深的在地衝浪嚮導，熟悉台灣各主要衝浪點的地形、潮流和天氣型態。

用戶會給你當前的海況數據和一個「有效等級」（代表用戶的衝浪經驗與當前條件的組合評估）。你的任務是根據這些資訊，以 2–3 段繁體中文說明當前海況的特點和注意事項。

原則：
- 不使用評分、等級、紅綠燈或任何「危不危險」的判斷語言
- 自然帶入具體數字，讓用戶自己產生判斷
- 語氣沉穩，像認識這個浪點多年的在地朋友
- 點出當前條件的特點、值得注意的地方，以及這種條件下的環境互動方式
- 根據有效等級調整敘述深度：cautious（較基礎）、understanding（中等）、proficient（細緻）
- 每段控制在 2–4 句，總長度約 120–200 字"""


# In-memory cache: key → (narrative, timestamp)
_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 3600.0


def _cache_key(data: dict) -> str:
    hour = int(time.time() // 3600)
    return f"{data['spot_name']}:{data['effective_level']}:{hour}"


async def generate_narrative(data: dict) -> str:
    key = _cache_key(data)
    if key in _cache:
        text, ts = _cache[key]
        if time.time() - ts < _CACHE_TTL:
            return text

    level_desc = {
        'cautious': '（初學 / 謹慎型）',
        'understanding': '（有基礎概念）',
        'proficient': '（思考成熟）',
    }.get(data.get('effective_level', ''), '')

    def fmt(v, unit='', decimals=1):
        if v is None:
            return '未知'
        return f"{round(v, decimals)}{unit}"

    prompt = f"""浪點：{data['spot_name']}
用戶有效等級：{data.get('effective_level', 'cautious')}{level_desc}

當前海況：
- 浪高：{fmt(data.get('wave_height'), 'm')}
- 波浪週期：{fmt(data.get('wave_period'), 's')}
- 風速：{fmt(data.get('wind_speed'), ' m/s')} / 陣風 {fmt(data.get('gust'), ' m/s')}
- 潮汐：{fmt(data.get('tide'), 'm')}
- 海溫：{fmt(data.get('sea_temp'), '°C', 0)}
- SAR 漂流速：{fmt(data.get('sar_speed_ms'), ' m/s', 2)}
- SAR 終點靠近危險區域：{'是' if data.get('endpoint_dangerous') else '否'}
- 不規則短週期浪況：{'是' if data.get('irregular_wave') else '否'}

請依照上述資料給出 2–3 段衝浪嚮導式的繁體中文說明。"""

    model = _get_model()
    response = await model.generate_content_async(prompt)
    text = response.text
    _cache[key] = (text, time.time())
    return text
