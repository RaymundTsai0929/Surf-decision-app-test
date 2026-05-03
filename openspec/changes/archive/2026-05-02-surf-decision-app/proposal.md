## Why

台灣衝浪者在出發前缺乏一個能整合即時海況數據、視覺化漂流模擬與情境解讀的決策工具。現有工具（Windy、GoOcean）僅以靜態點與箭頭展示方向性數據，缺乏與體感連結的動態視覺化，也未針對不同程度浪人的思考方式提供差異化的資訊呈現。

## What Changes

- 新增 Web App（手機框架於瀏覽器呈現），包含台灣浪點地圖選擇介面
- 新增畫面一（直向）：衛星底圖上的 p5.js 動態漂流粒子 + CWA 逐時數據表（含顏色閾值）
- 新增畫面二（橫向，手指滑動切換）：影片播放 + 扇形原始數據區塊 + Claude AI 敘述
- 新增用戶分級系統：強制 onboarding 測驗（5–10 題，週冷卻）→ 三個內部等級
- 新增隱性打折機制：固定降一級 + 依海況條件加重，漂流終點危險則鎖定最保守等級
- 新增 Claude API 整合：以 prompt caching 的靜態系統提示 + 動態數據快照，輸出繁體中文情境敘述

## Non-Goals

- 不做社群回報功能（避免複雜度擴大，聚焦整合現有數據）
- 不做主觀評分或危險等級標示（顏色僅輔助辨識數值大小，不代表「危不危險」）
- 不整合 Swelleye API（目前無公開 API，以本地錄影替代）
- 不支援台灣以外的浪點（此版本 For Taiwan）
- 不做社群帳號系統，用戶資料僅存於本地

## Capabilities

### New Capabilities

- `spot-selection`：台灣全島地圖 → 區域縮放 → 浪點 Pin 選擇器（含 Pin 顏色快速辨識）
- `drift-animation`：p5.js 完整流場系統 — 手繪海岸邊界碰撞產生離岸流效果；Windy 風格粒子場（可開關）；可拖曳黃點顯示靜態箭頭（即時方向+速度）與 SAR 軌跡動畫（雙重互動）；Zoom 比例尺速度自動換算
- `conditions-table`：CWA API 逐時數據表，各欄位依固定閾值獨立顏色編碼（浪高藍、風力綠→橘、潮汐綠↔粉）
- `video-player`：橫向畫面左側影片播放（黃金比例 62%），以本地錄影替代即時影像
- `data-pizza`：橫向畫面右側扇形區塊，顯示五項原始數字（浪高、週期、風速、流速、SAR漂流速）
- `user-profiling`：onboarding 隨機題型測驗，界定三個內部等級（謹慎型/理解型/掌握型），結果對用戶不可見
- `ability-deflation`：依測驗等級與當日海況條件自動計算有效等級（隱性打折），漂流終點危險則強制最保守等級
- `ai-narrative`：Claude API（claude-sonnet-4-6）接收有效等級 + 浪點 + CWA 快照 + SAR 結果，輸出 2–3 段繁體中文情境敘述，啟用 prompt caching

### Modified Capabilities

(none)

## Impact

- Affected specs: spot-selection, drift-animation, conditions-table, video-player, data-pizza, user-profiling, ability-deflation, ai-narrative
- Affected code:
  - New: frontend/src/App.tsx
  - New: frontend/src/screens/Screen1Portrait.tsx
  - New: frontend/src/screens/Screen2Landscape.tsx
  - New: frontend/src/components/PhoneFrame.tsx
  - New: frontend/src/components/SatelliteMap.tsx
  - New: frontend/src/components/DriftCanvas.tsx
  - New: frontend/src/components/DataTable.tsx
  - New: frontend/src/components/VideoPlayer.tsx
  - New: frontend/src/components/PizzaChart.tsx
  - New: frontend/src/components/AIStory.tsx
  - New: frontend/src/hooks/useCWAData.ts
  - New: frontend/src/hooks/useDriftSim.ts
  - New: frontend/src/hooks/useClaudeStory.ts
  - New: frontend/src/data/spots.ts
  - New: backend/main.py
  - New: backend/routers/cwb.py
  - New: backend/routers/drift.py
  - New: backend/routers/ai.py
  - New: backend/services/cwa_client.py
  - New: backend/services/drift_sim.py
  - New: backend/services/claude_client.py
  - New: .env.example
