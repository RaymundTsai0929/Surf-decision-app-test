## Context

此 App 整合四個主要外部系統（CWA API、Claude API、ESRI 衛星底圖、p5.js 物理引擎）於單一 Web 應用程式中。現有資產為一個 Python 原型，包含 SAR 國際漂流計算公式與 CWA API 整合，反饋良好。新系統需在保留漂流引擎的前提下，加入完整的前端體驗（手機框架、雙畫面手勢切換）與 AI 解讀層。

漂流動畫已從單一粒子升級為完整流場系統：海岸邊界碰撞產生離岸流效果、Windy 風格粒子場（可開關）、可拖曳黃點提供靜態箭頭與 SAR 軌跡動畫雙重互動。

核心設計限制：不顯示評分或等級給用戶，所有「危險程度」判斷以隱性方式影響 Claude 輸出，而非直接呈現。

## Goals / Non-Goals

**Goals:**

- 建立 React + FastAPI 全端架構，前端以手機框架呈現，後端包裝既有 Python 漂流引擎
- 定義雙畫面切換手勢、黃金比例版面與 p5.js 整合策略
- 確立用戶分級（測驗 → 內部等級 → 打折機制）與 Claude API 的串接介面
- 提供可填入 API key 的 .env.example，前後端各一份設定

**Non-Goals:**

- 不設計後台管理介面
- 不實作真正的 Swelleye API 串接
- 不設計用戶帳號系統（資料存 localStorage）
- 不做 PWA 離線功能

## Decisions

### 前端框架：React + TypeScript + Vite

選擇 React 而非 Vue 或 Svelte，原因：
- Leaflet、p5.js、Framer Motion 的 React 綁定套件成熟度最高
- TypeScript 在複雜狀態（用戶等級、打折邏輯、多畫面數據流）下提供型別安全

替代方案：Next.js（過重，無需 SSR）；Svelte（p5.js 整合較少範例）

### 地圖：Leaflet + ESRI World Imagery

使用 Leaflet 而非 Google Maps JavaScript API，原因：
- ESRI World Imagery 提供免費高解析度衛星底圖
- 避免 Google Maps billing 設定複雜度，降低原型門檻

p5.js canvas 以絕對定位疊加於 Leaflet map 容器上，監聽地圖 zoom/pan 事件同步更新粒子座標。

### 雙畫面切換：CSS transform + @use-gesture/react

使用手勢庫而非純 CSS，確保 iOS Safari touch event 相容性。畫面一為直向（portrait），畫面二為橫向（landscape），以 translateX/translateY 切換，Framer Motion 提供慣性動畫。

### 後端：FastAPI（Python）

直接複用既有 Python SAR 漂流引擎，無需重寫。FastAPI 提供 async 支援，適合同時呼叫 CWA API 與 Claude API。

### 用戶分級儲存：localStorage

用戶等級（測驗結果、上次測驗時間）存於 localStorage，不需後端帳號系統。週冷卻邏輯在前端計算，跳過測驗者預設最保守等級。

### Claude API 整合：Lazy fetch + Prompt Caching

- System prompt（角色設定 + 輸出原則）標記為 `cache_control: ephemeral`，避免重複計費
- User message 含有效等級、浪點名稱、CWA 數據快照、SAR 漂流速與終點判定
- 僅在用戶滑入畫面二時觸發，避免不必要的 API 呼叫
- Model: `claude-sonnet-4-6`，max_tokens: 400，temperature: 0.3

### 打折邏輯：前端計算，後端提供原始數據

打折計算完全在前端進行（測驗等級 + 條件判斷），後端只提供原始 CWA 數據與 SAR 計算結果。有效等級不存於後端，確保用戶無法透過 API 反查自己的等級。

### 危險物件資料庫：靜態 JSON hardcode

原型階段手動標記五個浪點的危險座標（礁石、防波堤），以靜態 JSON 存於前端 `src/data/spots.ts`，避免額外的地理資料 API 依賴。

### 流場系統：邊界碰撞取代水下地形資料

台灣水下地形資料（bathymetry）取得困難且格式複雜。採用幾何邊界碰撞模擬代替：

- 各浪點海岸線以手工描繪多邊形儲存（`spots.ts` 的 `coastline` 欄位）
- 粒子接觸海岸邊界時計算邊緣法向量，反射速度向量
- 凹型海岸（灣型）自然產生收斂 → 向外衝的離岸流效果，無需 bathymetry
- 粒子流場全域基底為 CWA 均勻向量場，邊界碰撞產生局部差異

### 可拖曳黃點：雙重互動模式

黃點同時支援靜態查詢與動態模擬：

- 拖曳至任意位置 → 即時靜態箭頭（向量方向 + m/s 數值）
- 按播放 → 呼叫 GET /api/v1/drift 以黃點座標為起點，動畫跑 SAR 軌跡
- 兩者同時顯示，拖曳至新位置時清除既有軌跡

## Risks / Trade-offs

- **p5.js + Leaflet 同步**：地圖縮放時粒子座標需重新計算，若效能不足考慮降為 Canvas 2D 直接繪製。→ 緩解：限制粒子數量上限（≤ 50），並以 requestAnimationFrame 節流
- **CWA API 可用性**：觀測站資料可能有缺值或延遲。→ 緩解：前端顯示最後更新時間，缺值欄位顯示 `--`
- **Claude API 延遲**：2–5 秒響應時間影響體驗。→ 緩解：進入畫面二立即顯示 loading skeleton，並快取當次結果（同一浪點同一小時不重複呼叫）
- **iOS Safari autoplay 限制**：影片需設定 `muted + playsInline + autoPlay`。→ 緩解：已知解法，在 VideoPlayer 元件中直接套用屬性
