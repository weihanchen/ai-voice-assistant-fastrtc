# Feature Specification: LangGraph Travel Flow

**Feature Branch**: `006-langgraph-travel-flow`
**Created**: 2026-01-04
**Status**: Draft
**Input**: User description: "LangGraph 旅遊規劃流程：整合 StateGraph 實現意圖分類路由與多步驟旅遊規劃子流程，展示流程編排能力並保留現有 Tool 功能"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 旅遊規劃天氣建議 (Priority: P1)

使用者透過語音表達想去某個城市旅遊的意願，系統自動解析目的地、查詢天氣狀況，並根據天氣條件給予旅遊建議。這是一個多步驟的流程，展示了 LangGraph 的流程編排能力。

**Why this priority**: 這是本功能的核心展示場景，透過「旅遊規劃」這個多步驟流程充分展現 LangGraph StateGraph 的價值——條件分支、狀態管理、多節點串接。

**Independent Test**: 對著麥克風說「我想去台北玩」，系統查詢台北天氣後，根據天氣狀況給予適當的旅遊建議（天氣適合則推薦景點，不適合則建議備案）。

**Acceptance Scenarios**:

1. **Given** 系統處於待命狀態且台北天氣晴朗, **When** 使用者說「我想去台北玩」, **Then** 系統回應天氣狀況並推薦適合的戶外行程
2. **Given** 系統處於待命狀態且高雄正在下雨, **When** 使用者說「我想去高雄旅遊」, **Then** 系統回應天氣狀況並建議室內行程或改天出遊
3. **Given** 系統處於待命狀態, **When** 使用者說「想去台中走走」, **Then** 系統完成多步驟流程：解析目的地 → 查詢天氣 → 評估條件 → 產生建議

---

### User Story 2 - 保留原有工具功能 (Priority: P1)

使用者仍可使用原有的天氣查詢、匯率換算、股票查詢功能，這些功能透過 LangGraph 路由分流至對應的 Tool，確保向後相容。

**Why this priority**: 與 P1 同等重要，因為這確保了系統的向後相容性，不會因為新增 LangGraph 而破壞現有功能。

**Independent Test**: 分別測試「台北天氣」、「美金匯率」、「台積電股價」，確認三個原有功能皆正常運作。

**Acceptance Scenarios**:

1. **Given** 系統已整合 LangGraph 路由, **When** 使用者說「台北天氣如何」, **Then** 系統透過路由分流至 WeatherTool 並回應天氣資訊
2. **Given** 系統已整合 LangGraph 路由, **When** 使用者說「100 美金換台幣」, **Then** 系統透過路由分流至 ExchangeRateTool 並回應換算結果
3. **Given** 系統已整合 LangGraph 路由, **When** 使用者說「台積電現在多少錢」, **Then** 系統透過路由分流至 StockPriceTool 並回應股價

---

### User Story 3 - 流程視覺化輸出 (Priority: P2)

開發者或學習者可以透過系統產生的 Mermaid 圖來理解整個流程架構，包含主路由流程與旅遊規劃子流程，方便教學與除錯。

**Why this priority**: 這是教學展示的重要功能，但不影響核心對話功能的運作。

**Independent Test**: 執行視覺化輸出指令，產生可在 Mermaid Live Editor 渲染的流程圖。

**Acceptance Scenarios**:

1. **Given** 系統已建立 LangGraph 流程, **When** 呼叫視覺化輸出功能, **Then** 產生 Mermaid 格式的流程圖原始碼
2. **Given** 已產生 Mermaid 流程圖, **When** 在 Mermaid Live Editor 貼上, **Then** 正確渲染出節點與邊線關係

---

### Edge Cases

- 當使用者說出不支援的城市（如「東京」）作為旅遊目的地時，系統回應「抱歉，目前僅支援台灣城市的旅遊規劃」
- 當天氣 API 查詢失敗時，系統回應「抱歉，目前無法取得天氣資訊，無法提供旅遊建議，請稍後再試」
- 當使用者意圖模糊（如「幫我規劃行程」未指定地點）時，系統詢問「請問您想去哪個城市旅遊呢？」
- 當 LangGraph 流程執行過程中發生錯誤時，系統優雅降級並提供友善錯誤訊息

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 整合 LangGraph StateGraph 作為對話流程的編排引擎
- **FR-002**: 系統 MUST 實作意圖分類節點，將使用者輸入路由至對應的處理流程（天氣查詢、匯率查詢、股票查詢、旅遊規劃）
- **FR-003**: 系統 MUST 實作旅遊規劃子流程，包含：解析目的地 → 查詢天氣 → 評估天氣 → 產生建議
- **FR-004**: 旅遊規劃流程 MUST 根據天氣條件產生不同建議（適合出遊 vs 建議備案）
- **FR-005**: 系統 MUST 保留並正確路由至現有的 WeatherTool、ExchangeRateTool、StockPriceTool
- **FR-006**: 系統 MUST 提供流程視覺化輸出功能，產生 Mermaid 格式的流程圖
- **FR-007**: 系統 MUST 在流程執行過程中維護狀態（StateGraph State）
- **FR-008**: 系統 MUST 以口語化繁體中文回應所有結果
- **FR-009**: 系統 MUST 在任何流程節點失敗時提供友善錯誤訊息

### Key Entities

- **FlowState**: 流程狀態，包含使用者輸入、意圖分類結果、中間處理結果、最終回應
- **IntentType**: 意圖類型，區分天氣查詢、匯率查詢、股票查詢、旅遊規劃
- **TravelPlanState**: 旅遊規劃狀態，包含目的地城市、天氣資訊、天氣評估結果、旅遊建議
- **WeatherCondition**: 天氣條件評估，區分適合出遊與不適合出遊

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 旅遊規劃流程從使用者說出目的地到系統開始語音回應，延遲不超過 8 秒
- **SC-002**: 原有功能（天氣、匯率、股票查詢）經過 LangGraph 路由後，回應延遲增加不超過 1 秒
- **SC-003**: 意圖分類準確率達 95% 以上（正確區分四種意圖類型）
- **SC-004**: 流程視覺化輸出可在 Mermaid Live Editor 正確渲染，且節點數量與實際流程一致
- **SC-005**: 100% 的流程錯誤情境皆有友善中文錯誤訊息回應

## Assumptions

- 使用者會以繁體中文進行對話
- 旅遊規劃目前僅限台灣城市，與現有天氣查詢支援範圍一致
- LangGraph 與現有 OpenAI SDK 相容，不會產生版本衝突
- 天氣「適合出遊」的判斷標準：非雨天、氣溫介於 15-35°C
- 旅遊景點推薦使用預設建議清單，不涉及外部景點 API

## Dependencies

- 001-fastrtc-voice-pipeline（語音輸入輸出管線）
- 002-weather-query（天氣查詢 Tool，供旅遊流程呼叫）
- 003-exchange-rate-query（匯率查詢 Tool，路由分流目標）
- 004-stock-price-query（股票查詢 Tool，路由分流目標）
- LangGraph 套件（新增依賴）

## Out of Scope

- 多輪對話的旅遊規劃（如：持續追問細節）
- 旅遊行程儲存與歷史記錄
- 景點 API 整合（使用靜態推薦清單）
- 交通、住宿等旅遊規劃細節
- 非台灣地區的旅遊規劃
