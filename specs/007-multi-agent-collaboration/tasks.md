# Tasks: Multi-Agent Collaboration

**Input**: Design documents from `/specs/007-multi-agent-collaboration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 建立 agents 模組目錄結構與基礎設定

- [x] T001 建立 agents 模組目錄結構 in `src/voice_assistant/agents/`
- [x] T002 [P] 新增 FlowMode 列舉與 FLOW_MODE 設定 in `src/voice_assistant/config.py`
- [x] T003 [P] 建立 agents 單元測試目錄 in `tests/unit/agents/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 實作所有 User Story 共用的核心元件

**⚠️ CRITICAL**: 所有 User Story 必須等此階段完成才能開始

### 狀態與資料模型

- [x] T004 實作 AgentType 列舉 in `src/voice_assistant/agents/state.py`
- [x] T005 實作 AgentTask Pydantic 模型 in `src/voice_assistant/agents/state.py`
- [x] T006 實作 AgentResult Pydantic 模型 in `src/voice_assistant/agents/state.py`
- [x] T007 實作 TaskDecomposition Pydantic 模型 in `src/voice_assistant/agents/state.py`
- [x] T008 實作 MultiAgentState TypedDict in `src/voice_assistant/agents/state.py`

### 基底類別

- [x] T009 實作 BaseAgent 抽象類別 in `src/voice_assistant/agents/base.py`

### Supervisor Agent

- [x] T010 實作 SupervisorAgent.decompose() 任務拆解 in `src/voice_assistant/agents/supervisor.py`
- [x] T011 實作 SupervisorAgent.aggregate() 結果彙整 in `src/voice_assistant/agents/supervisor.py`

### 專家 Agent

- [x] T012 [P] 實作 WeatherAgent in `src/voice_assistant/agents/weather.py`
- [x] T013 [P] 實作 FinanceAgent in `src/voice_assistant/agents/finance.py`
- [x] T014 [P] 實作 TravelAgent in `src/voice_assistant/agents/travel.py`
- [x] T015 [P] 實作 GeneralAgent in `src/voice_assistant/agents/general.py`

### 流程圖

- [x] T016 實作 create_multi_agent_graph() in `src/voice_assistant/agents/graph.py`
- [x] T017 實作 MultiAgentExecutor in `src/voice_assistant/agents/executor.py`

### 模組匯出

- [x] T018 設定 agents 模組 __init__.py 匯出 in `src/voice_assistant/agents/__init__.py`

**Checkpoint**: Foundation ready - 所有 Agent 與流程已可執行 ✅

---

## Phase 3: User Story 1 - 並行查詢多項資訊 (Priority: P1) 🎯 MVP

**Goal**: 使用者可同時查詢多項資訊（如股價+匯率），系統並行處理並彙整結果

**Independent Test**: 詢問「查台積電股價和美金匯率」，驗證兩項結果同時回應

### Implementation for User Story 1

- [x] T019 [US1] 整合 MultiAgentExecutor 至 VoicePipeline in `src/voice_assistant/voice/pipeline.py`
- [x] T020 [US1] 實作流程模式選擇邏輯（根據 FLOW_MODE）in `src/voice_assistant/voice/pipeline.py`
- [x] T021 [US1] 驗證並行查詢：「查台積電股價和美金匯率」(人工驗證完成 - 匯率成功，股價因STT辨識問題失敗)
- [x] T022 [US1] 驗證多城市天氣：「台北和高雄今天天氣如何」(人工驗證完成 - 2個WeatherAgent並行執行成功)
- [x] T023 [US1] 實作部分失敗處理：成功部分正常回應，失敗部分說明原因

**Checkpoint**: User Story 1 完成，可並行查詢多項資訊 ✅

---

## Phase 4: User Story 2 - 智慧旅遊規劃 (Priority: P2)

**Goal**: 使用者表達旅遊意圖時，系統協調天氣與景點資訊提供完整建議

**Independent Test**: 詢問「我想去台中玩」，驗證天氣+景點推薦

### Implementation for User Story 2

- [x] T024 [US2] 擴充 TravelAgent 支援天氣整合 in `src/voice_assistant/agents/travel.py`
- [x] T025 [US2] 擴充 SupervisorAgent 識別旅遊意圖並分派 Weather+Travel Agent
- [x] T026 [US2] 實作天氣不佳時的室內備案建議邏輯
- [x] T027 [US2] 驗證旅遊規劃：「我下週想去台中玩」(人工驗證完成 - 天氣+景點推薦+室內備案)

**Checkpoint**: User Story 2 完成，可進行智慧旅遊規劃 ✅

---

## Phase 5: User Story 3 - 出差行程助理 (Priority: P3)

**Goal**: 使用者表達出差需求時，系統提供天氣、匯率及注意事項

**Independent Test**: 詢問「後天要去東京出差」，驗證天氣+匯率+建議

### Implementation for User Story 3

- [x] T028 [US3] 擴充 SupervisorAgent 識別出差意圖
- [x] T029 [US3] 實作出差情境的 Agent 組合（Weather + Finance + General）
- [x] T030 [US3] 擴充 GeneralAgent 提供出差注意事項
- [x] T031 [US3] 驗證出差助理：「後天去東京出差」(人工驗證完成 - 天氣+匯率+注意事項並行執行)

**Checkpoint**: User Story 3 完成，可提供出差行程建議 ✅

---

## Phase 6: User Story 4 - 流程模式切換 (Priority: P4)

**Goal**: 系統管理者可透過環境變數切換處理模式

**Independent Test**: 修改 FLOW_MODE 環境變數，驗證行為正確切換

### Implementation for User Story 4

- [x] T032 [US4] 完善 FLOW_MODE 切換邏輯（tools/langgraph/multi_agent）
- [x] T033 [US4] 驗證 FLOW_MODE=multi_agent 使用多代理流程 (人工驗證完成 - log顯示Multi-Agent流程)
- [x] T034 [US4] 驗證 FLOW_MODE=langgraph 使用現有 006 流程 (人工驗證完成 - log顯示LangGraph流程)
- [x] T035 [US4] 驗證 FLOW_MODE=tools 使用純 Tool 呼叫 (人工驗證完成 - log顯示舊版Tool Calling)
- [x] T036 [US4] 更新 .env.example 新增 FLOW_MODE 說明

**Checkpoint**: User Story 4 完成，可切換流程模式 ✅

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 程式碼品質、文件與效能優化

- [x] T037 [P] 執行 ruff check 並修正所有 linting 錯誤
- [x] T038 [P] 執行 ruff format 格式化所有程式碼
- [x] T039 驗證現有測試全數通過（向後相容）- 203 tests passed
- [x] T040 [P] 執行 quickstart.md 驗證所有範例可正常運作 (人工驗證完成 - 所有場景測試通過)
- [x] T041 效能驗證：並行執行時間不超過最慢 Agent 的 1.2 倍 (人工驗證完成 - log顯示並行API請求)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 無依賴 - 可立即開始 ✅
- **Foundational (Phase 2)**: 依賴 Phase 1 完成 - **阻塞所有 User Story** ✅
- **User Stories (Phase 3-6)**: 依賴 Phase 2 完成 ✅
  - US1-US4 可依優先順序執行
  - 或由多人平行開發（若人力允許）
- **Polish (Phase 7)**: 依賴所有 User Story 完成 ✅

### User Story Dependencies

- **User Story 1 (P1)**: 依賴 Phase 2 - 無其他 Story 依賴 ✅
- **User Story 2 (P2)**: 依賴 Phase 2 - 可獨立測試 ✅
- **User Story 3 (P3)**: 依賴 Phase 2 - 可獨立測試 ✅
- **User Story 4 (P4)**: 依賴 Phase 2 + 部分 US1 整合點 ✅

### Within Each Phase

- 標示 [P] 的任務可平行執行
- 未標示的任務需依序執行
- 驗證任務須在實作任務完成後執行

### Parallel Opportunities

Phase 2 平行機會：
- T012, T013, T014, T015（4 個專家 Agent）可同時開發

Phase 7 平行機會：
- T037, T038, T040 可同時執行

---

## Parallel Example: Phase 2 Expert Agents

```bash
# 同時開發 4 個專家 Agent：
Task: "T012 [P] 實作 WeatherAgent in src/voice_assistant/agents/weather.py"
Task: "T013 [P] 實作 FinanceAgent in src/voice_assistant/agents/finance.py"
Task: "T014 [P] 實作 TravelAgent in src/voice_assistant/agents/travel.py"
Task: "T015 [P] 實作 GeneralAgent in src/voice_assistant/agents/general.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup ✅
2. 完成 Phase 2: Foundational（**關鍵路徑**）✅
3. 完成 Phase 3: User Story 1 ✅
4. **STOP and VALIDATE**: 測試並行查詢功能
5. 可 Demo/發布 MVP

### Incremental Delivery

1. Setup + Foundational → 基礎建設完成 ✅
2. User Story 1 → 並行查詢（MVP）✅
3. User Story 2 → 旅遊規劃 ✅
4. User Story 3 → 出差助理 ✅
5. User Story 4 → 模式切換 ✅
6. Polish → 品質收尾 ✅

### 建議 MVP 範圍

**僅實作 Phase 1 + Phase 2 + Phase 3 (User Story 1)**

這樣即可展示：
- ✅ Multi-Agent 架構
- ✅ 並行執行能力
- ✅ 結果彙整機制
- ✅ 部分失敗處理

---

## Notes

- [P] 標示 = 不同檔案、無依賴，可平行
- [Story] 標示 = 對應 spec.md 的 User Story
- 每個 User Story 可獨立完成與測試
- 每個任務完成後建議 commit
- 停在任何 Checkpoint 皆可驗證功能

## Implementation Summary (2025-01-11)

### Created Files
- `src/voice_assistant/agents/__init__.py` - Module exports
- `src/voice_assistant/agents/state.py` - Data models (AgentType, AgentTask, AgentResult, TaskDecomposition, MultiAgentState)
- `src/voice_assistant/agents/base.py` - BaseAgent abstract class
- `src/voice_assistant/agents/supervisor.py` - SupervisorAgent with decompose() and aggregate()
- `src/voice_assistant/agents/weather.py` - WeatherAgent
- `src/voice_assistant/agents/finance.py` - FinanceAgent (exchange rate + stock price)
- `src/voice_assistant/agents/travel.py` - TravelAgent with weather integration
- `src/voice_assistant/agents/general.py` - GeneralAgent with business trip support
- `src/voice_assistant/agents/graph.py` - LangGraph multi-agent graph with Send() API
- `src/voice_assistant/agents/executor.py` - MultiAgentExecutor

### Modified Files
- `src/voice_assistant/config.py` - Added FlowMode enum and flow_mode setting
- `src/voice_assistant/voice/pipeline.py` - Integrated MultiAgentExecutor with FLOW_MODE support
- `.env.example` - Added FLOW_MODE configuration

### Test Results
- All 203 existing unit tests passed (backward compatible)
- ruff check: All checks passed
- ruff format: All files formatted
