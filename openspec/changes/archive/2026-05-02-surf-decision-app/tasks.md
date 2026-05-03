## 1. 專案初始化與架構

- [x] 1.1 初始化前端：Vite + React TypeScript，安裝 Leaflet、p5.js、@use-gesture/react、Framer Motion、Tailwind（前端框架：React + TypeScript + Vite）
- [x] 1.2 初始化後端：FastAPI + httpx + anthropic，設定 uvicorn（後端：FastAPI（Python））
- [x] 1.3 建立 .env.example：含 CWA_API_KEY 與 ANTHROPIC_API_KEY 兩個欄位，加入說明文字
- [x] 1.4 建立 PhoneFrame.tsx 元件：螢幕寬 > 500px 時顯示手機外框，否則全版面顯示

## 2. 雙畫面切換系統

- [x] 2.1 實作雙畫面切換骨架：@use-gesture/react 捕捉左右滑動手勢，Framer Motion 執行 translateX 切換動畫（雙畫面切換：CSS transform + @use-gesture/react）
- [x] 2.2 設定畫面一直向（100dvh）與畫面二橫向（100vw）的 CSS 版面，黃金比例（38.2% / 61.8%）分割
- [x] 2.3 在 Chrome DevTools 手機模式與實機 iPhone Safari 確認手勢切換與動畫正常

## 3. 浪點資料與地圖入口

- [x] 3.1 建立 frontend/src/data/spots.ts：定義五個浪點（烏石港北堤、烏石港長堤、雙獅、蜜月灣、佳樂水、無尾港）的名稱、座標、區域標記、危險物件座標清單（危險物件資料庫：靜態 JSON hardcode）
- [x] 3.2 實作台灣全島地圖入口畫面：Leaflet 載入台灣邊界，以四個可點擊的區塊多邊形標示東西南北（Taiwan region map entry）
- [x] 3.3 實作區域點擊後 zoom in：依區域定義的 bounds 執行 flyToBounds，顯示該區域的浪點 Pin（Surf spot pins with condition color）
- [x] 3.4 實作 Pin 顏色計算：依 CWA 當前浪高與風速對照閾值表決定 Pin 顏色（綠/黃/橘/紅），CWA 無資料時顯示灰色
- [x] 3.5 實作 Pin 點擊事件：點擊 Pin 後導覽至該浪點的 Screen1Portrait（Navigate to spot detail）
- [x] 3.6 建立 SatelliteMap.tsx：使用 ESRI World Imagery tile（地圖：Leaflet + ESRI World Imagery）

## 4. CWA 數據管線

- [x] 4.1 實作 backend/services/cwa_client.py：呼叫 CWA 海岸天氣 API（pointID 對應各浪點），解析浪高(m)、週期(s)、浪向、風速(m/s)、風向、陣風(m/s)、氣溫、海溫、潮汐(m)，補齊單位換算
- [x] 4.2 實作 GET /api/v1/conditions?spot=<id> 端點：聚合 CWA 逐時預報，回傳 JSON，缺值欄位回傳 null
- [x] 4.3 實作 useCWAData.ts hook：fetch /api/v1/conditions，提供 loading / error / data 狀態
- [x] 4.4 實作 DataTable.tsx：橫向捲動逐時資料表，當前時間欄位高亮，缺值顯示 `--`（Hourly CWA data table display）
- [x] 4.5 實作逐欄固定閾值顏色編碼（Per-column color coding with fixed thresholds）：浪高藍色五階、風力綠→橘五階、陣風綠→橘四階、潮汐相對綠↔粉、波浪週期無色

## 5. 漂流動畫與流場系統

- [x] 5.1 移植既有 Python SAR 漂流計算至 backend/services/drift_sim.py：輸入起點座標(lat/lng) + Swell1/Swell2/風速向量，輸出漂流速度(m/s)與逐步座標軌跡陣列（後端：FastAPI（Python））
- [x] 5.2 實作 GET /api/v1/drift?lat=&lng=&spot= 端點：以傳入座標為起點執行 SAR 模擬，回傳 {speed_ms, trajectory: [{lat,lng}], endpoint_dangerous: bool}
- [x] 5.3 在 frontend/src/data/spots.ts 各浪點新增 `coastline: {lat,lng}[]` 欄位：沿著衛星底圖手工描繪各浪點海岸線頂點座標（Coastal boundary polygon per surf spot）
- [x] 5.4 實作 DriftCanvas.tsx：p5.js canvas 絕對定位疊加於 Leaflet 容器，渲染海岸邊界線（半透明填色）
- [x] 5.5 實作 Windy 風格粒子流場（Windy-style particle flow field with toggle）：50 個粒子分布於浪點 bounding box，依 CWA Swell1+Swell2+Wind 均勻向量場移動，預設隱藏，點擊開關按鈕顯示/隱藏
- [x] 5.6 實作海岸邊界碰撞反射（Coastal boundary collision and reflection）（流場系統：邊界碰撞取代水下地形資料）：粒子接觸 coastline 多邊形邊段時，計算邊緣法向量並反射速度向量；驗證凹型海岸出現收斂→向外衝效果
- [x] 5.7 實作可拖曳黃點（Draggable yellow dot with static arrow）（可拖曳黃點：雙重互動模式）：黃點初始於浪點參考座標，拖曳時即時更新靜態箭頭（方向 + m/s 數值，四捨五入至小數一位）
- [x] 5.8 實作 SAR 軌跡動畫（SAR trajectory animation from yellow dot position）：播放按鈕呼叫 GET /api/v1/drift 帶入黃點座標，動畫逐步繪製軌跡路徑；靜態箭頭保持顯示；拖曳黃點至新位置時清除軌跡並重置播放按鈕
- [x] 5.9 實作 Zoom-proportional particle speed：所有粒子位移在地理座標空間計算後透過 map.latLngToLayerPoint() 轉換為螢幕像素，map.on('zoom') 事件觸發座標重算
- [x] 5.10 確認 Particle count limit：流場粒子總數 ≤ 50，requestAnimationFrame 節流

## 6. 影片播放與 Pizza 圖表

- [x] 6.1 實作 VideoPlayer.tsx：`<video muted playsInline autoPlay loop>` 播放 public/video/surf-test.mp4（Pre-recorded video playback in landscape screen）
- [x] 6.2 確認影片以 `object-fit: cover` 填滿左側 61.8% 面板，無黑邊（Video fills its container proportionally）
- [x] 6.3 實作 PizzaChart.tsx：手寫 SVG，五個等分扇形，各扇形中心顯示原始數字（浪高/週期/風速/流速/漂流速），缺值顯示 `--`（SVG sector chart with raw data values）
- [x] 6.4 確認 Pizza 圖不含評分、等級文字與警示顏色（No scores or levels displayed）

## 7. 用戶分級系統

- [x] 7.1 建立 frontend/src/data/quiz.ts：設計 15 題題庫（情境題、選擇題、是非題混合），每題含答案與思考成熟度權重（用戶分級儲存：localStorage）
- [x] 7.2 實作 Onboarding 畫面：第一次啟動強制顯示測驗，5–10 題從題庫隨機抽取，簡單點選輸入（Mandatory onboarding quiz）
- [x] 7.3 實作跳過處理：用戶關閉測驗時，localStorage 寫入 level: 'cautious' 與當前時間戳
- [x] 7.4 實作測驗評分與 Internal three-level classification：0–40% → cautious、41–70% → understanding、71–100% → proficient，結果存 localStorage 且不顯示給用戶
- [x] 7.5 實作 Weekly quiz cooldown：讀取 localStorage 的上次測驗時間，7 天內封鎖重測並顯示剩餘天數（Weekly quiz cooldown）

## 8. 打折邏輯

- [x] 8.1 建立 frontend/src/utils/deflation.ts：輸入測驗等級 + CWA 快照 + SAR 結果，輸出有效等級（打折邏輯：前端計算，後端提供原始數據）
- [x] 8.2 實作 Fixed one-level deflation from quiz result：proficient→understanding、understanding→cautious、cautious 不降
- [x] 8.3 實作 Condition-triggered additional deflation：浪高 > 2m 降一級、週期 < 7s 加旗標（不降級但傳遞 irregular wave flag）、風速 > 25kt 降一級、SAR 漂流速 > 1.5m/s 降一級，每次降級後不低於 cautious
- [x] 8.4 實作 Dangerous drift endpoint locks to cautious：SAR 終點座標距任一危險物件 ≤ 50m 時，強制有效等級 = cautious，忽略其他計算結果

## 9. Claude AI 敘述

- [x] 9.1 實作 backend/services/claude_client.py：Anthropic SDK，system prompt 含 `cache_control: {"type": "ephemeral"}` 標記（Claude API 整合：Lazy fetch + Prompt Caching）（Prompt caching for system prompt）
- [x] 9.2 實作 POST /api/v1/story 端點：接收有效等級、浪點名稱、CWA 快照七欄位、SAR 漂流速與 endpoint_dangerous 旗標（Narrative input includes effective level and data snapshot）
- [x] 9.3 確認 API parameters：claude-sonnet-4-6，max_tokens: 400，temperature: 0.3（API parameters）
- [x] 9.4 實作 useClaudeStory.ts hook：進入 Screen 2 時 lazy fetch，送出 POST /api/v1/story，提供 loading / error / data（Claude API narrative generation）
- [x] 9.5 實作記憶體快取：同浪點同整點小時內快取敘述結果，跨小時清除（Result cached per spot per hour）
- [x] 9.6 實作 AIStory.tsx：顯示 loading skeleton（文字骨架），收到回應後渲染繁體中文 2–3 段敘述

## 10. 整合測試與收尾

- [x] 10.1 curl 測試 GET /api/v1/conditions?spot=wushih，確認回傳含浪高、週期、風速等完整欄位
- [x] 10.2 瀏覽器確認衛星底圖載入、黃色漂流粒子出現於正確海域座標
- [x] 10.3 Chrome DevTools 手機模式確認滑動手勢切換畫面一↔畫面二動畫流暢
- [x] 10.4 確認 Pizza 圖五扇形正確顯示原始數字，無任何評分或等級標記
- [x] 10.5 iOS Safari 實機確認影片 autoplay（muted + playsInline）成功播放
- [x] 10.6 確認 Claude 敘述為繁體中文 2–3 段，無評分詞彙，且首次進入畫面二才觸發 API 呼叫
