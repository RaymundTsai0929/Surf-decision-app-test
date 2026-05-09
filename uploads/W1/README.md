# W1 Streamlit Prototype

這份目錄是衝浪決策原型（Streamlit 版）的可執行快照。

## 目錄

- `src/`：主程式（地圖、漂移視覺、CWA 串接、RAG 問答）
- `data/`：靜態資料（含最佳浪況列表）
- `scripts/`：啟動與環境腳本
- `docs/`：開發說明文件

## 啟動方式

1. 建立虛擬環境並安裝相依（建議 Python 3.11+）。
2. 設定環境變數（見 `.env.example`）。
3. 在 `uploads/W1` 目錄執行：

```powershell
python -m streamlit run src/streamlit_app.py
```

## 需要的環境變數

- `CWA_AUTH_CODE`：中央氣象署 API 授權碼
- `GOOGLE_API_KEY`：Gemini / Google GenAI 金鑰

## 備註

- 本原型含大量前端疊圖邏輯（小黃點、粒子層、方向條示意）。
- `zoom >= 19` 時會自動關閉小黃點疊圖以便觀察底圖。
