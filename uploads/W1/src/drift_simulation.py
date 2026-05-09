"""
海上飄移視覺化（教育用，非 SAROPS／非搜救）。

速度場採 IAMSAR 常見簡化：合成漂移 ≈ 表層海流 U_current + 風偏流 L_leeway（Leeway ≈ 係數 × W₁₀，
預設「人體／救生衣」約 1.1%·W₁₀）＋可選簡化斯托克斯漂移（波高經驗式，實務常併入風偏不確定度）。

- 風：Open-Meteo Forecast API（current）
- 浪／流：Open-Meteo Marine API

畫面位移仍以 m/s 經 Web Mercator 公尺／像素換算，與地圖 zoom 幾何一致。
Windy 嵌入無法讀取格點資料，數值非 Windy 引擎。
"""

from __future__ import annotations

import json
import math
from typing import Optional


def _web_mercator_meters_per_pixel(lat: float, zoom: int) -> float:
    """與 Google Maps 等 Web Mercator 圖磚一致：中心緯度 lat、整數 zoom 下之公尺／像素（CSS 像素）。"""
    return 156543.03392 * math.cos(math.radians(lat)) / (2**zoom)


# IAMSAR 常見量級：人體在水中（含救生衣）風偏約為 10 m 風速的 ~1.1%。
DEFAULT_LEEWAY_RATE = 0.011
# 風偏相對「下風向」往右側偏轉角（ENU、北向上，搜救文獻常取約 15°～40°）。
DEFAULT_LEEWAY_ANGLE_DEG = 25.0

# IAMSAR 合成速度多為 0.05～0.4 m/s 量級，若用與舊「整段風速加權」相同的倍率，畫面上幾乎不動；
# 此係數在「已用 MPP 對齊地圖幾何」之後，僅放大可視速度，不改向量間比例。
DEFAULT_SAR_MOTION_VISUAL_SCALE = 120.0


def build_drift_simulation_html(lat: float, lon: float, spot_name: str) -> str:
    """回傳可嵌入 Streamlit components.html 的單頁 HTML（內含 Canvas 與動畫邏輯）。"""
    safe_name = json.dumps(spot_name, ensure_ascii=False)
    lat_j = json.dumps(lat)
    lon_j = json.dumps(lon)
    mpp = _web_mercator_meters_per_pixel(lat, 11)
    mpp_j = json.dumps(mpp)
    lr_j = json.dumps(float(DEFAULT_LEEWAY_RATE))
    la_j = json.dumps(math.radians(DEFAULT_LEEWAY_ANGLE_DEG))
    ss_j = json.dumps(1.0)
    sv_j = json.dumps(float(DEFAULT_SAR_MOTION_VISUAL_SCALE))

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: system-ui, sans-serif; background: #0a1628; color: #e2e8f0; }}
  #wrap {{ padding: 8px 10px 12px; }}
  #meta {{ font-size: 12px; line-height: 1.45; opacity: 0.92; margin-bottom: 8px; }}
  #meta strong {{ color: #7dd3fc; }}
  canvas {{ display: block; width: 100%; max-width: 560px; height: 320px; border-radius: 8px;
    background: linear-gradient(180deg, #0c4a6e 0%, #075985 40%, #0369a1 100%); }}
  #bar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 10px; font-size: 12px; }}
  button {{
    background: #0284c7; color: #fff; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
  }}
  button:hover {{ background: #0369a1; }}
  input[type="range"] {{ width: 130px; vertical-align: middle; }}
  .err {{ color: #fca5a5; font-size: 12px; margin-top: 6px; }}
  #stat {{ font-size: 11px; line-height: 1.45; opacity: 0.95; max-width: 540px; }}
</style>
</head>
<body>
<div id="wrap">
  <div id="meta">
    浪點：<strong id="sn"></strong>　座標：{lat_j}, {lon_j}<br/>
    資料：<a href="https://open-meteo.com/" target="_blank" rel="noopener" style="color:#7dd3fc">Open-Meteo</a>
    風場＋海浪（與 Windy 地圖<strong>同一地理位置</strong>；數值非 Windy 引擎）<br/>
    漂移模型：<strong>IAMSAR 簡化</strong>（海流 + 風偏 0.011·W₁₀ + 弱斯托克斯近似）
  </div>
  <canvas id="c" width="560" height="320" aria-label="飄移模擬"></canvas>
  <div id="bar">
    <button type="button" id="reset">重置位置</button>
    <label>畫面倍率 <input type="range" id="gain" min="0.3" max="2.5" step="0.1" value="1"/></label>
  </div>
  <div id="stat"></div>
  <div id="err" class="err"></div>
</div>
<script>
(function() {{
  const spotName = {safe_name};
  const LAT = {lat_j};
  const LON = {lon_j};
  const MPP = {mpp_j};
  const BASE_VISUAL = {sv_j};
  const LEEWAY_RATE = {lr_j};
  const LEEWAY_ANGLE_RAD = {la_j};
  const STOKES_SCALE = {ss_j};
  document.getElementById('sn').textContent = spotName;

  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  let px = W / 2, py = H / 2;

  let windSpeed = 0, windFromDeg = 0;
  let ue_w = 0, un_w = 0;
  let waveHeight = 0, waveFromDeg = 0;
  let ue_s = 0, un_s = 0;
  let stokesMag = 0;
  let hasWave = false;
  let curSpeed = 0, curDirDeg = 0;
  let curSpeedKmh = 0;
  let ue_c = 0, un_c = 0;
  let hasCurrent = false;

  const gainEl = document.getElementById('gain');
  const statEl = document.getElementById('stat');
  const errEl = document.getElementById('err');

  function metFromDirToENU(speed, dirFromDeg) {{
    const rad = (dirFromDeg * Math.PI) / 180;
    const u = -speed * Math.sin(rad);
    const v = -speed * Math.cos(rad);
    return {{ u, v }};
  }}

  function stokesDriftSpeedMs(h) {{
    if (h == null || h <= 0) return 0;
    return Math.min(0.45, 0.08 * h * h + 0.04 * h) * STOKES_SCALE;
  }}

  /** IAMSAR 簡化：D ≈ U_current + L_leeway + S_stokes（m/s，ENU） */
  function sarDriftMs() {{
    const Ws = Math.hypot(ue_w, un_w);
    const L = LEEWAY_RATE * Ws;
    let dwE = 0, dwN = 0;
    if (Ws >= 1e-9) {{
      dwE = ue_w / Ws;
      dwN = un_w / Ws;
    }}
    const rtE = dwN;
    const rtN = -dwE;
    const c = Math.cos(LEEWAY_ANGLE_RAD);
    const s = Math.sin(LEEWAY_ANGLE_RAD);
    const leE = L * (dwE * c + rtE * s);
    const leN = L * (dwN * c + rtN * s);
    let se = 0, sn = 0;
    if (hasWave && waveHeight > 0) {{
      const sm = stokesDriftSpeedMs(waveHeight);
      const pr = metFromDirToENU(1, waveFromDeg);
      const pm = Math.hypot(pr.u, pr.v) || 1;
      se = sm * pr.u / pm;
      sn = sm * pr.v / pm;
    }}
    return {{ ue: ue_c + leE + se, un: un_c + leN + sn }};
  }}

  async function loadAll() {{
    errEl.textContent = '';
    statEl.textContent = '讀取風、海浪與海流資料…';
    const urlW = 'https://api.open-meteo.com/v1/forecast?latitude=' + LAT + '&longitude=' + LON
      + '&current=wind_speed_10m,wind_direction_10m&wind_speed_unit=ms';
    const urlM = 'https://marine-api.open-meteo.com/v1/marine?latitude=' + LAT + '&longitude=' + LON
      + '&current=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction&cell_selection=sea';

    try {{
      const [rw, rm] = await Promise.all([fetch(urlW), fetch(urlM)]);
      if (!rw.ok) throw new Error('風場 HTTP ' + rw.status);
      if (!rm.ok) throw new Error('海浪 HTTP ' + rm.status);
      const jw = await rw.json();
      const jm = await rm.json();
      const cw = jw.current;
      const cm = jm.current;

      if (!cw || cw.wind_speed_10m == null) throw new Error('無風場資料');
      windSpeed = cw.wind_speed_10m;
      windFromDeg = cw.wind_direction_10m;
      const ew = metFromDirToENU(windSpeed, windFromDeg);
      ue_w = ew.u; un_w = ew.v;

      hasWave = cm && cm.wave_direction != null;
      if (hasWave) {{
        waveHeight = cm.wave_height != null ? cm.wave_height : 0;
        waveFromDeg = cm.wave_direction;
        stokesMag = stokesDriftSpeedMs(waveHeight);
        const es = metFromDirToENU(stokesMag, waveFromDeg);
        ue_s = es.u; un_s = es.v;
      }} else {{
        waveHeight = 0; waveFromDeg = 0; stokesMag = 0; ue_s = 0; un_s = 0;
      }}

      hasCurrent = cm && cm.ocean_current_direction != null && cm.ocean_current_velocity != null;
      if (hasCurrent) {{
        curSpeedKmh = cm.ocean_current_velocity; // API 預設 km/h
        curSpeed = curSpeedKmh / 3.6; // 轉為 m/s，再與風速同量綱合成
        curDirDeg = cm.ocean_current_direction; // 去向
        const rad = (curDirDeg * Math.PI) / 180;
        ue_c = curSpeed * Math.sin(rad);
        un_c = curSpeed * Math.cos(rad);
      }} else {{
        curSpeed = 0; curSpeedKmh = 0; curDirDeg = 0; ue_c = 0; un_c = 0;
      }}

      statEl.innerHTML =
        '10m 風：<strong>' + windSpeed.toFixed(1) + ' m/s</strong>，來向 <strong>' + Math.round(windFromDeg) + '°</strong><br/>' +
        '風偏流（Leeway，係數 ' + LEEWAY_RATE + '·W）：<strong>' + (LEEWAY_RATE * windSpeed).toFixed(3)
        + ' m/s</strong>，相對下風向偏角 <strong>' + (LEEWAY_ANGLE_RAD * 180 / Math.PI).toFixed(0) + '°</strong><br/>' +
        (hasWave
          ? '海浪：波高 <strong>' + waveHeight.toFixed(2) + ' m</strong>，斯托克斯近似 <strong>' + stokesMag.toFixed(3)
            + ' m/s</strong>，浪向（來向）<strong>' + Math.round(waveFromDeg) + '°</strong>'
          : '<span style="opacity:0.85">此位置未取得海浪資料，斯托克斯項為 0。</span>')
        + '<br/>' +
        (hasCurrent
          ? '海流：流速 <strong>' + curSpeedKmh.toFixed(2) + ' km/h</strong>（'
            + curSpeed.toFixed(2) + ' m/s），流向（去向）<strong>'
            + Math.round(curDirDeg) + '°</strong>'
          : '<span style="opacity:0.8">此位置未取得海流資料。</span>');
    }} catch (err) {{
      errEl.textContent = '讀取失敗：' + err.message + ' — 使用預設風＋假浪示意。';
      windSpeed = 2; windFromDeg = 45;
      const ew = metFromDirToENU(windSpeed, windFromDeg);
      ue_w = ew.u; un_w = ew.v;
      waveHeight = 0.8; waveFromDeg = 200;
      stokesMag = stokesDriftSpeedMs(waveHeight);
      const es = metFromDirToENU(stokesMag, waveFromDeg);
      ue_s = es.u; un_s = es.v;
      hasWave = true;
      curSpeedKmh = 0.6;
      curSpeed = curSpeedKmh / 3.6;
      curDirDeg = 150;
      const rc = (curDirDeg * Math.PI) / 180;
      ue_c = curSpeed * Math.sin(rc);
      un_c = curSpeed * Math.cos(rc);
      hasCurrent = true;
      statEl.innerHTML = '（預設示意）風 2 m/s / 浪 0.8 m / 海流 0.6 km/h';
    }}
  }}

  function drawArrow(x0, y0, du, dv, len, stroke, fill) {{
    const mag = Math.hypot(du, dv) || 1;
    const nx = (du / mag) * len, ny = (dv / mag) * len;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x0 + nx, y0 + ny);
    ctx.stroke();
    const ah = 8;
    const ang = Math.atan2(ny, nx);
    ctx.beginPath();
    ctx.moveTo(x0 + nx, y0 + ny);
    ctx.lineTo(x0 + nx - ah * Math.cos(ang - 0.4), y0 + ny - ah * Math.sin(ang - 0.4));
    ctx.lineTo(x0 + nx - ah * Math.cos(ang + 0.4), y0 + ny - ah * Math.sin(ang + 0.4));
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
  }}

  let last = performance.now();
  function tick(now) {{
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    const g = parseFloat(gainEl.value, 10);
    const c = sarDriftMs();
    const factor = (BASE_VISUAL * g) / MPP;
    px += c.ue * factor * dt;
    py -= c.un * factor * dt;
    if (px < 8) px = 8; if (px > W - 8) px = W - 8;
    if (py < 8) py = 8; if (py > H - 8) py = H - 8;

    ctx.clearRect(0, 0, W, H);
    const grd = ctx.createLinearGradient(0, 0, 0, H);
    grd.addColorStop(0, '#0c4a6e');
    grd.addColorStop(0.45, '#075985');
    grd.addColorStop(1, '#0369a1');
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    for (let i = 0; i < 12; i++) {{
      const y = (i / 12) * H + (now * 0.01 + i * 17) % 40;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }}

    const lenW = Math.min(52, 16 + windSpeed * 6);
    drawArrow(W * 0.72, H * 0.14, ue_w, -un_w, lenW, 'rgba(255,255,255,0.65)', 'rgba(255,255,255,0.55)');
    ctx.fillStyle = 'rgba(255,255,255,0.4)';
    ctx.font = '11px sans-serif';
    ctx.fillText('風（吹向）', W * 0.72 - 20, H * 0.14 - 10);

    if (hasWave) {{
      const lenS = Math.min(50, 14 + stokesMag * 120);
      drawArrow(W * 0.72, H * 0.38, ue_s, -un_s, lenS, 'rgba(103,232,249,0.85)', 'rgba(34,211,238,0.75)');
      ctx.fillStyle = 'rgba(165,243,252,0.85)';
      ctx.fillText('浪（斯托克斯漂移近似）', W * 0.72 - 44, H * 0.38 - 10);
    }}

    const cc = sarDriftMs();
    drawArrow(W * 0.72, H * 0.62, cc.ue, -cc.un, Math.min(48, 20 + Math.hypot(cc.ue, cc.un) * 18),
      'rgba(251,191,36,0.9)', 'rgba(251,191,36,0.75)');
    ctx.fillStyle = 'rgba(253,224,71,0.95)';
    ctx.fillText('SAR 合成（流＋風偏＋斯托克斯）', W * 0.72 - 52, H * 0.62 - 10);

    ctx.beginPath();
    ctx.arc(px, py, 9, 0, Math.PI * 2);
    ctx.fillStyle = '#fbbf24';
    ctx.fill();
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 2;
    ctx.stroke();

    requestAnimationFrame(tick);
  }}

  document.getElementById('reset').addEventListener('click', function() {{
    px = W / 2; py = H / 2;
  }});

  loadAll().then(function() {{ requestAnimationFrame(tick); }});
}})();
</script>
</body>
</html>"""


def build_drift_overlay_layer_html(
    lat: float,
    lon: float,
    spot_name: str,
    *,
    map_zoom: int = 11,
    motion_scale: float = DEFAULT_SAR_MOTION_VISUAL_SCALE,
    gain: float = 1.0,
    leeway_rate: Optional[float] = None,
    leeway_angle_deg: float = DEFAULT_LEEWAY_ANGLE_DEG,
    stokes_scale: float = 1.0,
    cwa_drift: Optional[dict] = None,
    move_map_instead_of_dot: bool = False,
    map_iframe_id: str = "gmapBaseFrame",
    show_wave_particles: bool = True,
    show_wind_particles: bool = True,
    show_current_particles: bool = True,
) -> str:
    """
    產生「疊在地圖 iframe 上方」用的透明 Canvas + 動畫腳本。

    漂移採 IAMSAR 簡化：海流 + 風偏（預設 0.011·W₁₀，可改 leeway_rate）＋可選斯托克斯項。
    位移以 Web Mercator 在 (lat, map_zoom) 的公尺／像素換算；motion_scale／gain 為畫面可視化倍率。

    若傳入 cwa_drift（由鄉鎮沿海 F-D0047-095 預報列轉成），則風／浪／流數值以此為準，不再請求 Open-Meteo。

    使用方式：把回傳字串插入到一個已經是 position:relative 的容器內。
    """
    lr = float(leeway_rate) if leeway_rate is not None else DEFAULT_LEEWAY_RATE
    safe_name = json.dumps(spot_name, ensure_ascii=False)
    lat_j = json.dumps(lat)
    lon_j = json.dumps(lon)
    mpp = _web_mercator_meters_per_pixel(lat, map_zoom)
    mpp_j = json.dumps(mpp)
    motion_scale_j = json.dumps(float(motion_scale))
    lr_j = json.dumps(lr)
    la_j = json.dumps(math.radians(leeway_angle_deg))
    ss_j = json.dumps(float(stokes_scale))
    use_cwa = "true" if cwa_drift else "false"
    cwa_drift_j = json.dumps(cwa_drift, ensure_ascii=False) if cwa_drift else "null"
    move_map_j = "true" if move_map_instead_of_dot else "false"
    map_iframe_id_j = json.dumps(map_iframe_id)
    show_wave_j = "true" if show_wave_particles else "false"
    show_wind_j = "true" if show_wind_particles else "false"
    show_current_j = "true" if show_current_particles else "false"

    return f"""
<style>
  #driftOverlayCanvas {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }}
  #driftDot {{
    position: absolute;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #fbbf24;
    border: 2px solid #1e293b;
    box-sizing: border-box;
    transform: translate(-50%, -50%);
    cursor: grab;
    pointer-events: auto;
    touch-action: none;
    z-index: 3;
  }}
  #driftHalo {{
    position: absolute;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    border: 2px solid rgba(56, 189, 248, 0.55);
    background: radial-gradient(
      circle,
      rgba(56, 189, 248, 0.16) 0%,
      rgba(56, 189, 248, 0.07) 45%,
      rgba(56, 189, 248, 0.02) 70%,
      rgba(56, 189, 248, 0.0) 100%
    );
    transform: translate(-50%, -50%);
    pointer-events: none;
    z-index: 2;
  }}
  #driftDot:active {{
    cursor: grabbing;
  }}
  #driftVectorLayer {{
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 4;
  }}
  .driftVecBadge {{
    position: absolute;
    min-width: 68px;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.7);
    color: #f8fafc;
    font-size: 10px;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: 0.2px;
    text-align: center;
    transform-origin: 12px 50%;
    box-shadow: 0 2px 8px rgba(2, 6, 23, 0.35);
    white-space: nowrap;
  }}
  #driftVecWind {{
    background: rgba(71, 85, 105, 0.78);
  }}
  #driftVecSwell {{
    background: rgba(245, 158, 11, 0.8);
    color: #111827;
  }}
  #driftVecCurrent {{
    background: rgba(22, 163, 74, 0.8);
  }}
</style>
<canvas id="driftOverlayCanvas" aria-label="海上飄移示意"></canvas>
<div id="driftHalo" aria-hidden="true"></div>
<div id="driftDot" title="拖曳小黃點"></div>
<div id="driftVectorLayer" aria-hidden="true">
  <div id="driftVecWind" class="driftVecBadge"></div>
  <div id="driftVecSwell" class="driftVecBadge"></div>
  <div id="driftVecCurrent" class="driftVecBadge"></div>
</div>
<script>
(function() {{
  const spotName = {safe_name};
  const LAT = {lat_j};
  const LON = {lon_j};
  const MPP = {mpp_j};
  const MOTION_SCALE = {motion_scale_j};
  const LEEWAY_RATE = {lr_j};
  const LEEWAY_ANGLE_RAD = {la_j};
  const STOKES_SCALE = {ss_j};
  const USE_CWA_DRIFT = {use_cwa};
  const CWA_DRIFT = {cwa_drift_j};
  const MOVE_MAP_INSTEAD_OF_DOT = {move_map_j};
  const MAP_IFRAME_ID = {map_iframe_id_j};
  const SHOW_WAVE_PARTICLES = {show_wave_j};
  const SHOW_WIND_PARTICLES = {show_wind_j};
  const SHOW_CURRENT_PARTICLES = {show_current_j};

  const canvas = document.getElementById('driftOverlayCanvas');
  const dot = document.getElementById('driftDot');
  const halo = document.getElementById('driftHalo');
  const vecWind = document.getElementById('driftVecWind');
  const vecSwell = document.getElementById('driftVecSwell');
  const vecCurrent = document.getElementById('driftVecCurrent');
  if (!canvas || !dot || !halo || !vecWind || !vecSwell || !vecCurrent) return;
  const mapFrame = document.getElementById(MAP_IFRAME_ID);
  const ctx = canvas.getContext('2d');
  let W = 1, H = 1, dpr = 1;

  let px = 0, py = 0;
  let mapShiftX = 0, mapShiftY = 0;
  let isDraggingDot = false;
  const FLOW_PARTICLE_COUNT = 180;
  const waveParticles = [];
  const windParticles = [];
  const currentParticles = [];
  let windSpeed = 0, windFromDeg = 0;
  let ue_w = 0, un_w = 0;
  let waveHeight = 0, waveFromDeg = 0;
  let ue_s = 0, un_s = 0;
  let hasWave = false;
  let curSpeed = 0, curDirDeg = 0;
  let curSpeedKmh = 0;
  let ue_c = 0, un_c = 0;
  let hasCurrent = false;

  const gain = {float(gain)};

  function resize() {{
    const rect = canvas.getBoundingClientRect();
    W = Math.max(1, rect.width);
    H = Math.max(1, rect.height);
    dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    // 讓繪圖座標直接用 CSS px
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    px = W / 2;
    py = H / 2;
    dot.style.left = px + 'px';
    dot.style.top = py + 'px';
    halo.style.left = px + 'px';
    halo.style.top = py + 'px';
    if (!waveParticles.length) {{
      for (let i = 0; i < FLOW_PARTICLE_COUNT; i++) {{
        waveParticles.push({{ x: Math.random() * W, y: Math.random() * H, age: Math.random() * 120, maxAge: 80 + Math.random() * 120, speed: 0.5 + Math.random() * 0.9 }});
        windParticles.push({{ x: Math.random() * W, y: Math.random() * H, age: Math.random() * 120, maxAge: 80 + Math.random() * 120, speed: 0.5 + Math.random() * 0.9 }});
        currentParticles.push({{ x: Math.random() * W, y: Math.random() * H, age: Math.random() * 120, maxAge: 80 + Math.random() * 120, speed: 0.5 + Math.random() * 0.9 }});
      }}
    }}
  }}

  function applyMapShift() {{
    if (!MOVE_MAP_INSTEAD_OF_DOT || !mapFrame) return;
    mapFrame.style.transform = 'translate(' + mapShiftX.toFixed(2) + 'px,' + mapShiftY.toFixed(2) + 'px)';
  }}

  function metFromDirToENU(speed, dirFromDeg) {{
    // dirFromDeg: 風向（來向），0°=北來
    const rad = (dirFromDeg * Math.PI) / 180;
    const u = -speed * Math.sin(rad);
    const v = -speed * Math.cos(rad);
    return {{ u, v }};
  }}

  function stokesDriftSpeedMs(h) {{
    if (h == null || h <= 0) return 0;
    return Math.min(0.45, 0.08 * h * h + 0.04 * h) * STOKES_SCALE;
  }}

  function sarDriftMs() {{
    const Ws = Math.hypot(ue_w, un_w);
    const L = LEEWAY_RATE * Ws;
    let dwE = 0, dwN = 0;
    if (Ws >= 1e-9) {{
      dwE = ue_w / Ws;
      dwN = un_w / Ws;
    }}
    const rtE = dwN;
    const rtN = -dwE;
    const c = Math.cos(LEEWAY_ANGLE_RAD);
    const s = Math.sin(LEEWAY_ANGLE_RAD);
    const leE = L * (dwE * c + rtE * s);
    const leN = L * (dwN * c + rtN * s);
    let se = 0, sn = 0;
    if (hasWave && waveHeight > 0) {{
      const sm = stokesDriftSpeedMs(waveHeight);
      const pr = metFromDirToENU(1, waveFromDeg);
      const pm = Math.hypot(pr.u, pr.v) || 1;
      se = sm * pr.u / pm;
      sn = sm * pr.v / pm;
    }}
    return {{ ue: ue_c + leE + se, un: un_c + leN + sn }};
  }}

  function applyCwaDrift(d) {{
    windSpeed = parseFloat(d.windSpeed) || 0;
    windFromDeg = parseFloat(d.windFromDeg) || 0;
    const ew = metFromDirToENU(windSpeed, windFromDeg);
    ue_w = ew.u; un_w = ew.v;

    waveHeight = parseFloat(d.waveHeight) || 0;
    waveFromDeg = parseFloat(d.waveFromDeg) || 0;
    hasWave = waveHeight > 0;
    const sm = stokesDriftSpeedMs(waveHeight);
    const es = metFromDirToENU(sm, waveFromDeg);
    ue_s = es.u; un_s = es.v;

    curSpeed = parseFloat(d.currentSpeedMps) || 0;
    curSpeedKmh = curSpeed * 3.6;
    curDirDeg = parseFloat(d.currentToDeg) || 0;
    hasCurrent = curSpeed > 1e-6;
    const rad = (curDirDeg * Math.PI) / 180;
    ue_c = curSpeed * Math.sin(rad);
    un_c = curSpeed * Math.cos(rad);
  }}

  function applyFallbackDemo() {{
    windSpeed = 2; windFromDeg = 45;
    const ew = metFromDirToENU(windSpeed, windFromDeg);
    ue_w = ew.u; un_w = ew.v;
    waveHeight = 0.8; waveFromDeg = 200;
    const sm = stokesDriftSpeedMs(waveHeight);
    const es = metFromDirToENU(sm, waveFromDeg);
    ue_s = es.u; un_s = es.v;
    hasWave = true;
    curSpeedKmh = 0.6;
    curSpeed = curSpeedKmh / 3.6;
    curDirDeg = 150;
    const rc = (curDirDeg * Math.PI) / 180;
    ue_c = curSpeed * Math.sin(rc);
    un_c = curSpeed * Math.cos(rc);
    hasCurrent = true;
  }}

  async function loadAll() {{
    if (USE_CWA_DRIFT && CWA_DRIFT) {{
      applyCwaDrift(CWA_DRIFT);
      return;
    }}
    applyFallbackDemo();
  }}

  function drawArrow(x0, y0, du, dv, len, stroke, fill) {{
    const mag = Math.hypot(du, dv) || 1;
    const nx = (du / mag) * len, ny = (dv / mag) * len;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x0 + nx, y0 + ny);
    ctx.stroke();
    const ah = 7;
    const ang = Math.atan2(ny, nx);
    ctx.beginPath();
    ctx.moveTo(x0 + nx, y0 + ny);
    ctx.lineTo(x0 + nx - ah * Math.cos(ang - 0.4), y0 + ny - ah * Math.sin(ang - 0.4));
    ctx.lineTo(x0 + nx - ah * Math.cos(ang + 0.4), y0 + ny - ah * Math.sin(ang + 0.4));
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
  }}

  function respawnFlowParticle(p) {{
    p.x = Math.random() * W;
    p.y = Math.random() * H;
    p.age = 0;
    p.maxAge = 80 + Math.random() * 120;
    p.speed = 0.5 + Math.random() * 0.9;
  }}

  function drawParticleField(dt, particles, baseUe, baseUn, rgbaColor, dashLen, speedBoost) {{
    const mag = Math.hypot(baseUe, baseUn);
    if (mag < 1e-6) return;
    const dirX = baseUe / mag;
    const dirY = -baseUn / mag;
    const flowPxPerSec = Math.min(42, 7 + mag * speedBoost);
    ctx.lineWidth = 1.1;
    for (let i = 0; i < particles.length; i++) {{
      const p = particles[i];
      p.age += 1;
      if (p.age > p.maxAge || p.x < -10 || p.x > W + 10 || p.y < -10 || p.y > H + 10) {{
        respawnFlowParticle(p);
      }}
      const jitter = Math.sin((p.age + i * 0.17) * 0.08) * 0.25;
      p.x += (dirX + jitter) * flowPxPerSec * p.speed * dt;
      p.y += (dirY - jitter) * flowPxPerSec * p.speed * dt;
      const alpha = Math.max(0.08, Math.min(0.42, (1 - p.age / p.maxAge) * 0.45));
      ctx.strokeStyle = rgbaColor.replace("{{a}}", alpha.toFixed(3));
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(p.x - dirX * dashLen, p.y - dirY * dashLen);
      ctx.stroke();
    }}
  }}

  function setDotPosition(x, y) {{
    px = Math.max(9, Math.min(W - 9, x));
    py = Math.max(9, Math.min(H - 9, y));
    dot.style.left = px + 'px';
    dot.style.top = py + 'px';
    halo.style.left = px + 'px';
    halo.style.top = py + 'px';
  }}

  function updateVectorBadge(el, vx, vy, title, valueText, radialOffset, fallbackDeg, forceDeg) {{
    const mag = Math.hypot(vx, vy);
    let deg = mag > 1e-6 ? (Math.atan2(vy, vx) * 180 / Math.PI) : fallbackDeg;
    if (typeof forceDeg === 'number' && Number.isFinite(forceDeg)) {{
      deg = forceDeg;
    }}
    const rad = deg * Math.PI / 180;
    const bx = px + Math.cos(rad) * radialOffset;
    const by = py + Math.sin(rad) * radialOffset;
    el.style.left = bx.toFixed(1) + 'px';
    el.style.top = by.toFixed(1) + 'px';
    el.style.transform = 'translate(-10%, -50%) rotate(' + deg.toFixed(1) + 'deg)';
    el.textContent = title + '  ' + valueText;
    el.style.opacity = mag > 1e-6 ? '0.95' : '0.45';
  }}

  let last = performance.now();
  function tick(now) {{
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;

    const c = sarDriftMs();
    const factor = (MOTION_SCALE * gain) / MPP;
    if (!isDraggingDot) {{
      if (MOVE_MAP_INSTEAD_OF_DOT) {{
        const deltaX = c.ue * factor * dt;
        const deltaY = -c.un * factor * dt;
        mapShiftX -= deltaX;
        mapShiftY -= deltaY;
        applyMapShift();
        setDotPosition(W / 2, H / 2);
      }} else {{
        px += c.ue * factor * dt;
        py -= c.un * factor * dt;
        // 範圍限制（避免點飛出畫面）
        setDotPosition(px, py);
      }}
    }}

    ctx.clearRect(0, 0, W, H);
    if (SHOW_WAVE_PARTICLES) {{
      drawParticleField(dt, waveParticles, ue_s, un_s, "rgba(255,255,255,{{a}})", 8, 10);
    }}
    if (SHOW_WIND_PARTICLES) {{
      drawParticleField(dt, windParticles, ue_w, un_w, "rgba(191,219,254,{{a}})", 7, 9);
    }}
    if (SHOW_CURRENT_PARTICLES) {{
      drawParticleField(dt, currentParticles, ue_c, un_c, "rgba(125,211,252,{{a}})", 9, 12);
    }}

    const badgeRingOffset = 40;
    updateVectorBadge(
      vecWind,
      ue_w,
      -un_w,
      '風向',
      windSpeed.toFixed(1) + 'm/s',
      badgeRingOffset,
      -90,
      (Math.atan2(-un_w, ue_w) * 180 / Math.PI) + 180
    );
    updateVectorBadge(
      vecSwell,
      ue_s,
      -un_s,
      '浪向',
      waveHeight.toFixed(1) + 'm',
      badgeRingOffset,
      -35,
      (Math.atan2(-un_s, ue_s) * 180 / Math.PI) + 180
    );
    updateVectorBadge(
      vecCurrent,
      ue_c,
      -un_c,
      '流向',
      curSpeed.toFixed(2) + 'm/s',
      badgeRingOffset,
      20,
      (Math.atan2(-un_c, ue_c) * 180 / Math.PI) + 180
    );

    // 只畫簡單的方向箭頭（左上角）
    drawArrow(W * 0.78, H * 0.18, c.ue, -c.un, Math.min(56, 18 + Math.hypot(c.ue, c.un) * 14),
      'rgba(251,191,36,0.95)', 'rgba(251,191,36,0.75)');
    ctx.fillStyle = 'rgba(251,191,36,0.9)';
    ctx.font = '12px sans-serif';
    ctx.fillText('SAR 簡化（流＋風偏＋斯托克斯）', W * 0.78 - 68, H * 0.18 - 6);
    if (USE_CWA_DRIFT && CWA_DRIFT && CWA_DRIFT.dataTime) {{
      ctx.font = '10px sans-serif';
      ctx.fillStyle = 'rgba(251,191,36,0.78)';
      ctx.fillText('驅動：CWA 鄉鎮沿海預報 ' + String(CWA_DRIFT.dataTime).slice(0, 16), W * 0.78 - 68, H * 0.18 + 12);
    }}

    requestAnimationFrame(tick);
  }}

  // 提供全域函式，讓外部按鈕可以重置小黃點位置
  window.resetDriftOverlay = function() {{
    mapShiftX = 0;
    mapShiftY = 0;
    applyMapShift();
    setDotPosition(W / 2, H / 2);
  }};

  resize();
  window.addEventListener('resize', resize);
  loadAll().then(function() {{
    requestAnimationFrame(tick);
  }});

  dot.addEventListener('mousedown', function(ev) {{
    ev.preventDefault();
    isDraggingDot = true;
  }});

  window.addEventListener('mousemove', function(ev) {{
    if (!isDraggingDot) return;
    const rect = canvas.getBoundingClientRect();
    setDotPosition(ev.clientX - rect.left, ev.clientY - rect.top);
  }});

  window.addEventListener('mouseup', function() {{
    isDraggingDot = false;
  }});

  dot.addEventListener('touchstart', function(ev) {{
    if (!ev.touches || ev.touches.length === 0) return;
    isDraggingDot = true;
    ev.preventDefault();
  }}, {{ passive: false }});

  window.addEventListener('touchmove', function(ev) {{
    if (!isDraggingDot || !ev.touches || ev.touches.length === 0) return;
    const rect = canvas.getBoundingClientRect();
    const t = ev.touches[0];
    setDotPosition(t.clientX - rect.left, t.clientY - rect.top);
    ev.preventDefault();
  }}, {{ passive: false }});

  window.addEventListener('touchend', function() {{
    isDraggingDot = false;
  }});
}})();
</script>
"""
