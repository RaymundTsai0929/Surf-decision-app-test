import os
import time
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma

from cwa_drift_directions import build_drift_injection_from_coastal_row
from cwa_service import CWAService, FD047_COASTAL_BY_SPOT
from drift_simulation import build_drift_overlay_layer_html

load_dotenv()

st.set_page_config(page_title="台灣衝浪 RAG 智能助手", layout="wide")

st.markdown(
    """
    <div id="cold-start-notice" style="
        background:#1e293b;
        color:#e2e8f0;
        border:1px solid #334155;
        border-radius:8px;
        padding:10px 12px;
        margin:0 0 12px 0;
        font-size:14px;
    ">
      首次開啟時間較久，請燒等
      <span class="loading-dots"><span>.</span><span>.</span><span>.</span></span>
    </div>
    <style>
      .loading-dots span {
        display: inline-block;
        width: 8px;
        text-align: center;
        animation: loadingDot 1.2s infinite ease-in-out;
        opacity: 0.25;
      }
      .loading-dots span:nth-child(1) { animation-delay: 0s; }
      .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
      .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes loadingDot {
        0%, 80%, 100% { opacity: 0.25; transform: translateY(0); }
        40% { opacity: 1; transform: translateY(-2px); }
      }
    </style>
    <script>
      setTimeout(function () {
        const el = document.getElementById('cold-start-notice');
        if (!el) return;
        el.style.transition = 'opacity 0.6s ease';
        el.style.opacity = '0';
        setTimeout(function () { el.remove(); }, 650);
      }, 10000);
    </script>
    """,
    unsafe_allow_html=True,
)

st.title("台灣衝浪智能助手")
st.caption(
    "左側預報優先使用氣象署「鄉鎮沿海」F-D0047-095（逐 3 小時，較貼近岸邊代表點），"
    "失敗時自動改為近海大區 F-A0012-001；中間地圖為視覺工具；"
    "最下方對話會併用預報文字與 PDF 知識庫。"
)

cwa = CWAService()

if "app_stage" not in st.session_state:
    st.session_state.app_stage = "quiz"
if "selected_spot" not in st.session_state:
    st.session_state.selected_spot = "烏石港"

# ---- Phase 1: 流程骨架（Quiz -> Map Select -> Main）----
if st.session_state.app_stage == "quiz":
    st.subheader("第一步：衝浪偏好問卷（骨架）")
    st.caption("先用簡版問卷確認需求，下一階段再套用 Dark UI 視覺。")
    with st.container(border=True):
        st.selectbox("你的程度", ["初學", "初階+", "中階", "進階"], index=1)
        st.selectbox("偏好浪點型態", ["沙灘浪型", "礁石浪型", "都可以"], index=0)
        st.selectbox("今天目標", ["練習基本動作", "找穩定浪況", "挑戰較大浪"], index=1)
        if st.button("完成問卷，前往地圖選點", type="primary", use_container_width=True):
            st.session_state.app_stage = "map-select"
            st.rerun()
    st.stop()

if st.session_state.app_stage == "map-select":
    st.subheader("第二步：地圖選點（骨架）")
    st.caption("先選擇浪點，下一步進入完整功能頁。")
    spot_options = ["東港大鵬灣", "雙獅海灘", "烏石港", "蜜月灣", "佳樂水", "金樽"]
    selected = st.selectbox(
        "選擇浪點",
        spot_options,
        index=spot_options.index(st.session_state.selected_spot)
        if st.session_state.selected_spot in spot_options
        else 2,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("回到問卷", use_container_width=True):
            st.session_state.app_stage = "quiz"
            st.rerun()
    with c2:
        if st.button("進入主頁", type="primary", use_container_width=True):
            st.session_state.selected_spot = selected
            st.session_state.app_stage = "main"
            st.rerun()
    st.stop()


@st.cache_data(ttl=600, show_spinner=False)
def cached_cwa_drift_payload(coastal_name: str) -> Optional[dict]:
    """鄉鎮沿海第一筆時段 → 注入小黃點 SAR 疊圖（與側邊欄同源 F-D0047 fileapi）。"""
    svc = CWAService()
    if not svc.auth_code:
        return None
    try:
        series = svc.get_coastal_timeseries(coastal_name)
        if not series:
            return None
        return build_drift_injection_from_coastal_row(series[0])
    except Exception:
        return None


# —— 側邊欄：只做「有後果」的操作 ——
with st.sidebar:
    st.subheader("中央氣象署")
    st.caption("按下「更新」後，以鄉鎮沿海（精細）為主寫入預報，供下方對話使用。")
    location = st.selectbox(
        "預報代表點（鄉鎮沿海）",
        ["東港大鵬灣", "雙獅海灘", "烏石港", "蜜月灣", "佳樂水", "金樽"],
    )
    if st.button("更新預報文字", type="primary", use_container_width=True):
        with st.spinner("抓取中…"):
            st.session_state.current_weather = cwa.get_surf_spot_forecast(location)
        st.success("已更新。")
    if st.session_state.get("current_weather"):
        with st.expander("目前預報內容", expanded=False):
            st.text(st.session_state.current_weather)
    else:
        st.info("尚未更新預報，對話中會顯示「無即時海象」。")

    st.divider()

    st.subheader("外部連結")
    st.link_button("Swelleye 浪況直播", "https://swelleye.com/surfcams", use_container_width=True)
    st.link_button(
        "Windy（另開完整地圖）",
        "https://www.windy.com/?waves,23.7,121.0,7",
        use_container_width=True,
        help="開啟 Windy 台灣海域總覽（waves 圖層）。",
    )

# —— 主區：浪點跳轉地圖（預設 zoom 15，之後可自由拖曳與縮放）——
spot_configs = [
    ("東港大鵬灣", 22.445262, 120.454680),
    ("雙獅海灘", 24.889792, 121.851581),
    ("烏石港", 24.871452, 121.843828),
    ("蜜月灣", 24.932229, 121.886763),
    ("佳樂水", 21.988794, 120.848127),
    ("金樽", 22.954101, 121.295311),
]
spot_lookup = {name: (lat, lon) for name, lat, lon in spot_configs}
spot_names = [name for name, _, _ in spot_configs]
default_spot = location if location in spot_lookup else spot_names[0]
if st.session_state.get("selected_spot") in spot_lookup:
    default_spot = st.session_state["selected_spot"]
map_spot = st.selectbox("浪點選擇（點選後自動跳轉）", spot_names, index=spot_names.index(default_spot))
st.session_state.selected_spot = map_spot
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 17
if "move_map_mode" not in st.session_state:
    st.session_state.move_map_mode = False
if "show_wave_particles" not in st.session_state:
    st.session_state.show_wave_particles = True
if "show_wind_particles" not in st.session_state:
    st.session_state.show_wind_particles = False
if "show_current_particles" not in st.session_state:
    st.session_state.show_current_particles = False

# 粒子圖層改為單選：同一時間只允許一種開啟。
active_count = sum(
    [
        bool(st.session_state.show_wave_particles),
        bool(st.session_state.show_wind_particles),
        bool(st.session_state.show_current_particles),
    ]
)
if active_count != 1:
    st.session_state.show_wave_particles = True
    st.session_state.show_wind_particles = False
    st.session_state.show_current_particles = False

spot_lat, spot_lon = spot_lookup[map_spot]
initial_zoom = int(st.session_state.map_zoom)
map_height = 720
# 以 zoom 15 為基準，依縮放層級自動調整小黃點速度（zoom 越大，速度越慢）。
# 先前倍率偏大，改為保守區間避免「飛行感」。
motion_scale = min(14.0, max(4.0, 12.0 * ((15.0 / float(initial_zoom)) ** 2)))

mode_text = "黃點固定地圖移動" if st.session_state.move_map_mode else "地圖固定黃點移動"
st.caption(
    f"{map_spot}目前 zoom {initial_zoom}（由下方拉桿控制），模式：{mode_text}。"
)
gmap_embed_url = (
    "https://www.google.com/maps"
    f"?ll={spot_lat},{spot_lon}&z={initial_zoom}&hl=zh-TW&output=embed&t=k"
)
coastal_key = FD047_COASTAL_BY_SPOT.get(map_spot)
drift_payload = cached_cwa_drift_payload(coastal_key) if coastal_key else None
show_drift_overlay = initial_zoom < 19
drift_overlay_layer = ""
if show_drift_overlay:
    drift_overlay_layer = build_drift_overlay_layer_html(
        spot_lat,
        spot_lon,
        map_spot,
        map_zoom=initial_zoom,
        motion_scale=motion_scale,
        cwa_drift=drift_payload,
        move_map_instead_of_dot=st.session_state.move_map_mode,
        map_iframe_id="gmapBaseFrame",
        show_wave_particles=st.session_state.show_wave_particles,
        show_wind_particles=st.session_state.show_wind_particles,
        show_current_particles=st.session_state.show_current_particles,
    )
map_frame_style = (
    "position:absolute;left:-10%;top:-10%;border:0;width:120%;height:120%;"
    "pointer-events:auto;transition:transform 0s linear;will-change:transform;"
    if st.session_state.move_map_mode
    else "position:absolute;inset:0;border:0;width:100%;height:100%;pointer-events:auto;"
)
html = f"""
<div style="position:relative;width:100%;padding-top:70%;border-radius:12px;overflow:hidden;box-shadow:0 10px 30px rgba(15,23,42,0.55);">
  <iframe
    id="gmapBaseFrame"
    src="{gmap_embed_url}"
    style="{map_frame_style}"
    loading="lazy"
    referrerpolicy="no-referrer-when-downgrade"
  ></iframe>
  {drift_overlay_layer}
</div>
"""
if show_drift_overlay:
    html += """
<div style="margin-top:8px;text-align:right;">
  <button type="button"
          onclick="if(window.resetDriftOverlay){window.resetDriftOverlay();}"
          style="padding:4px 10px;border-radius:6px;border:1px solid #4b5563;background:#020617;color:#e5e7eb;font-size:12px;cursor:pointer;">
    重置小黃點位置
  </button>
</div>
"""
else:
    html += """
<div style="margin-top:8px;text-align:right;color:#94a3b8;font-size:12px;">
  zoom 19 以上已自動關閉小黃點顯示
</div>
"""
map_col, layer_col = st.columns([5, 1])
with map_col:
    components.html(html, height=map_height, scrolling=False)
with layer_col:
    st.markdown("### 粒子圖層")
    if st.button(
        f"浪向 {'ON' if st.session_state.show_wave_particles else 'OFF'}",
        use_container_width=True,
        type="primary" if st.session_state.show_wave_particles else "secondary",
    ):
        st.session_state.show_wave_particles = True
        st.session_state.show_wind_particles = False
        st.session_state.show_current_particles = False
        st.rerun()
    if st.button(
        f"風向 {'ON' if st.session_state.show_wind_particles else 'OFF'}",
        use_container_width=True,
        type="primary" if st.session_state.show_wind_particles else "secondary",
    ):
        st.session_state.show_wave_particles = False
        st.session_state.show_wind_particles = True
        st.session_state.show_current_particles = False
        st.rerun()
    if st.button(
        f"流向 {'ON' if st.session_state.show_current_particles else 'OFF'}",
        use_container_width=True,
        type="primary" if st.session_state.show_current_particles else "secondary",
    ):
        st.session_state.show_wave_particles = False
        st.session_state.show_wind_particles = False
        st.session_state.show_current_particles = True
        st.rerun()

zoom_col, mode_col = st.columns([4, 1])
with zoom_col:
    st.slider("地圖縮放", min_value=15, max_value=21, step=1, key="map_zoom")
with mode_col:
    st.write("")
    st.write("")
    if st.button("切換模式", use_container_width=True):
        st.session_state.move_map_mode = not st.session_state.move_map_mode
        st.rerun()

st.divider()
st.subheader("問答")

# RAG
@st.cache_resource
def init_rag():
    data_path = "dataPDF"
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    pdf_files = [f for f in os.listdir(data_path) if f.endswith(".pdf")]
    if not pdf_files:
        return None, "請在 dataPDF 資料夾中放入 PDF 檔案。"

    all_docs = []
    for pdf in pdf_files:
        loader = PyPDFLoader(os.path.join(data_path, pdf))
        all_docs.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(all_docs)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_db",
    )
    return vectorstore, None


vectorstore, error = init_rag()
if error:
    st.warning(error)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("詢問衝浪、浪點或海象…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("思考中…"):
            # 若尚未取得 CWA 預報，或先前抓到的是錯誤字串（SSL/404），先自動抓一次
            cw = st.session_state.get("current_weather")
            bad_markers = [
                "SSL",
                "憑證",
                "404",
                "Resource not found",
                "抓取近海海象資料時發生錯誤",
                "找不到 CWA_AUTH_CODE",
            ]
            if (not cw) or any(m in str(cw) for m in bad_markers):
                with st.spinner("抓取 CWA 預報中…"):
                    st.session_state.current_weather = cwa.get_surf_spot_forecast(location)
                    st.session_state.current_weather_updated_at = time.time()

            weather_context = st.session_state.get("current_weather") or ""

            llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)

            context_text = ""
            if vectorstore:
                docs = vectorstore.as_retriever(search_kwargs={"k": 5}).invoke(prompt)
                context_text = "\n\n".join([doc.page_content for doc in docs])

            full_prompt = f"""你是一個台灣衝浪專家。請結合以下即時海象資訊與檢索到的知識來回答問題。
如果問題與浪況有關，請務必參考即時海象。

即時海象參考資訊:
{weather_context}

檢索到的知識內容:
{context_text if context_text else "無相關文件資料"}

使用者問題: {prompt}
"""

            response = llm.invoke(full_prompt)
            answer = response.content

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
