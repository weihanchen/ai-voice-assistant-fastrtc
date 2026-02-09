# Tasks: Flow Architecture Refactoring

**Input**: Design documents from `/specs/009-flow-architecture-refactoring/`
**Prerequisites**: plan.md, spec.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: 建立 BaseFlowExecutor 介面與 FlowRegistry，這是所有 User Story 的基礎

**⚠️ CRITICAL**: 所有 User Story 必須等此階段完成才能開始

### BaseFlowExecutor 介面

- [x] T001 [P] 建立 `BaseFlowExecutor` ABC in `src/voice_assistant/flows/base.py`
  - 定義 `flow_name` 抽象 property
  - 定義 `execute(user_input: str) -> str` 抽象方法
  - 定義 `get_visualization() -> str | None` 預設回傳 None
- [x] T002 [P] 撰寫 BaseFlowExecutor 單元測試 in `tests/unit/flows/test_base_flow_executor.py`
  - 測試無法直接實例化（ABC）
  - 測試子類別必須實作抽象方法
  - 測試 `get_visualization()` 預設回傳 None

### FlowRegistry

- [x] T003 建立 `FlowRegistry` in `src/voice_assistant/flows/registry.py`
  - `register(executor: BaseFlowExecutor) -> None`
  - `get(name: str) -> BaseFlowExecutor`（找不到時拋 `FlowNotFoundError`）
  - `list_flows() -> list[str]`
  - `has(name: str) -> bool`
- [x] T004 [P] 建立 `FlowNotFoundError` 例外 in `src/voice_assistant/flows/exceptions.py`
- [x] T005 撰寫 FlowRegistry 單元測試 in `tests/unit/flows/test_flow_registry.py`
  - 測試 register / get / list_flows / has
  - 測試重複名稱註冊拋出 ValueError
  - 測試 get 不存在名稱拋出 FlowNotFoundError

**Checkpoint**: BaseFlowExecutor + FlowRegistry 基礎建設完成

---

## Phase 2: User Story 1 - 統一流程執行介面 (Priority: P1) 🎯 MVP

**Goal**: 將現有 3 種流程模式適配到 BaseFlowExecutor，消除 VoicePipeline 的 if/elif 分支

**Independent Test**: 現有 200+ 測試全部通過，VoicePipeline 中無流程模式的 if/elif

### 適配現有 Executor

- [x] T006 [P] [US1] 建立 `ToolCallingExecutor` in `src/voice_assistant/flows/tool_calling_executor.py`
  - 繼承 `BaseFlowExecutor`
  - `flow_name` = `"tools"`
  - 封裝 `VoicePipeline._process_with_legacy()` 的邏輯（LLMClient + ToolRegistry + Tool Calling loop）
  - 接受 `llm_client`、`tool_registry`、`system_prompt_provider`（callable）參數
- [x] T007 [P] [US1] 撰寫 ToolCallingExecutor 單元測試 in `tests/unit/flows/test_tool_calling_executor.py`
  - 測試 `flow_name` 回傳 `"tools"`
  - 測試 `execute()` 正確呼叫 LLM 和 Tool
  - 測試 `get_visualization()` 回傳 None
- [x] T008 [US1] 適配 `FlowExecutor` 繼承 `BaseFlowExecutor` in `src/voice_assistant/flows/__init__.py`
  - 新增 `flow_name` property 回傳 `"langgraph"`
  - `get_visualization()` 保持現有實作
- [x] T009 [US1] 適配 `MultiAgentExecutor` 繼承 `BaseFlowExecutor` in `src/voice_assistant/agents/executor.py`
  - 新增 `flow_name` property 回傳 `"multi_agent"`

### 重構 VoicePipeline

- [x] T010 [US1] 重構 `VoicePipeline.__init__()` in `src/voice_assistant/voice/pipeline.py`
  - 新增 `flow_registry: FlowRegistry` 參數
  - 移除 `self.flow_executor` 和 `self.multi_agent_executor` 個別屬性
  - 移除 FlowMode 相關的 if/elif 初始化邏輯
- [x] T011 [US1] 重構 `VoicePipeline.process_audio_with_outputs()` in `src/voice_assistant/voice/pipeline.py`
  - 消除 `if effective_flow_mode == FlowMode.MULTI_AGENT / LANGGRAPH / TOOLS` 分支
  - 改為 `executor = self.flow_registry.get(effective_flow_mode.value)` + `executor.execute()`
  - 移除 `_process_with_flow()`、`_process_with_multi_agent()`、`_process_with_legacy()` 三個私有方法
- [x] T012 [US1] 重構 `reply_on_pause.py` composition root in `src/voice_assistant/voice/handlers/reply_on_pause.py`
  - 建立 `FlowRegistry` 並註冊三個 executor
  - 將 FlowRegistry 傳入 VoicePipeline
  - 移除直接建立 FlowExecutor / MultiAgentExecutor 的舊邏輯

### 驗證

- [x] T013 [US1] 執行現有測試驗證向後相容 `uv run pytest`
  - 確認所有測試通過
- [x] T014 [US1] 執行 `uv run ruff check . && uv run ruff format .` 確認程式碼品質

**Checkpoint**: User Story 1 完成 — 3 種流程模式統一介面，VoicePipeline 零 if/elif ✅

---

## Phase 3: User Story 2 - FlowRegistry 自動發現 (Priority: P1)

**Goal**: 開發者新增流程只需新增檔案，FlowRegistry 自動發現並註冊

**Independent Test**: FlowRegistry.list_flows() 能列出所有已註冊流程

### Implementation for User Story 2

- [x] T015 [US2] 更新 `flows/__init__.py` 匯出 in `src/voice_assistant/flows/__init__.py`
  - 匯出 `BaseFlowExecutor`、`FlowRegistry`、`FlowNotFoundError`、`ToolCallingExecutor`
- [x] T016 [US2] 更新 `reply_on_pause.py` 驗證 FlowRegistry 整合 in `src/voice_assistant/voice/handlers/reply_on_pause.py`
  - 確認角色的 `preferred_flow_mode` 可透過 FlowRegistry 正確查詢
  - 確認不存在的 flow name fallback 到預設流程
- [x] T017 [US2] 撰寫 FlowRegistry 整合測試 in `tests/unit/flows/test_flow_registry.py`
  - 測試完整流程：建立 FlowRegistry → 註冊 3 個 executor → get/list_flows 正確
  - 測試 fallback 邏輯：preferred_flow_mode 指向不存在流程時的行為
- [x] T018 [US2] 執行全量測試 `uv run pytest` 確認向後相容

**Checkpoint**: User Story 2 完成 — FlowRegistry 自動發現機制 ✅

---

## Phase 4: User Story 3 - Tool 與 Agent 自動註冊 (Priority: P2)

**Goal**: 新增 Tool/Agent 只需新增檔案，不需修改 composition root

**Independent Test**: 新增一個 BaseTool 子類別後，auto_discover 能自動發現

### Tool 自動掃描

- [x] T019 [US3] 實作 `ToolRegistry.auto_discover()` in `src/voice_assistant/tools/registry.py`
  - 使用 `importlib` + `inspect` 掃描指定套件下的 `BaseTool` 子類別
  - 過濾掉 `BaseTool` 本身（ABC 不註冊）
  - 記錄 import 錯誤為 warning log，不中斷掃描
  - 回傳已註冊的工具名稱列表
- [x] T020 [P] [US3] 撰寫 auto_discover 單元測試 in `tests/unit/tools/test_auto_discover.py`
  - 測試能發現現有 3 個 Tool（WeatherTool, ExchangeRateTool, StockPriceTool）
  - 測試不會註冊 BaseTool 本身
  - 測試 import 錯誤不中斷掃描

### Agent 自動發現

- [x] T021 [US3] 實作 Agent 自動發現輔助函式 in `src/voice_assistant/agents/graph.py`
  - 新增 `discover_agents()` 函式掃描 `agents/` 目錄
  - 過濾 `BaseAgent` 和 `SupervisorAgent`（不自動註冊）
  - 回傳 `dict[AgentType, BaseAgent]`
- [x] T022 [P] [US3] 撰寫 Agent 自動發現單元測試 in `tests/unit/agents/test_auto_discover.py`
  - 測試能發現 4 個 Agent（Weather, Finance, Travel, General）
  - 測試不會註冊 BaseAgent 本身

### 更新 Composition Root

- [x] T023 [US3] 更新 `reply_on_pause.py` 使用自動掃描 in `src/voice_assistant/voice/handlers/reply_on_pause.py`
  - `ToolRegistry` 改用 `auto_discover()` 取代手動 register
  - Agent 建立改用 `discover_agents()` 取代硬編碼 dict
- [x] T024 [US3] 執行全量測試 `uv run pytest` 確認向後相容
- [x] T025 [US3] 執行 `uv run ruff check . && uv run ruff format .` 確認程式碼品質

**Checkpoint**: User Story 3 完成 — Tool/Agent 自動註冊 ✅

---

## Phase 5: User Story 4 - Gradio UI 即時流程視覺化 (Priority: P3)

**Goal**: Gradio UI 顯示即時 Mermaid 流程圖，執行時節點高亮

**Independent Test**: 開啟 Gradio UI，發起對話後可看到流程圖

### 視覺化資料模型

- [x] T026 [P] [US4] 建立 `FlowVisualization` 和 `NodeStatus` in `src/voice_assistant/flows/visualization.py`
  - `NodeStatus` 列舉：PENDING / RUNNING / COMPLETED / FAILED
  - `FlowVisualization` Pydantic 模型：mermaid_code + node_statuses dict

### Mermaid 渲染增強

- [x] T027 [US4] 實作帶節點狀態的 Mermaid 輸出 in `src/voice_assistant/flows/visualization.py`
  - 新增 `render_mermaid_with_status(mermaid_code, node_statuses)` 函式
  - 為不同狀態的節點注入 CSS class（`:::running`、`:::completed` 等）
- [x] T028 [P] [US4] 撰寫視覺化單元測試 in `tests/unit/flows/test_visualization.py`
  - 測試 `render_mermaid_with_status()` 正確注入 CSS class
  - 測試空 node_statuses 時回傳原始 Mermaid

### Gradio UI 整合

- [x] T029 [US4] 新增 Mermaid 渲染 HTML 元件 in `src/voice_assistant/voice/ui/blocks.py`
  - 建立 `create_flow_visualization()` 函式回傳 `gr.HTML` 元件
  - 內嵌 mermaid.js CDN script
  - 建立 `update_flow_visualization(mermaid_code)` 更新函式
- [x] T030 [US4] 整合流程圖面板到 Gradio UI in `src/voice_assistant/voice/handlers/reply_on_pause.py`
  - 在右側面板新增流程視覺化區塊
  - 頁面載入時顯示當前流程的靜態 Mermaid 圖
- [x] T031 [US4] VoicePipeline 執行時傳送流程圖更新 in `src/voice_assistant/voice/pipeline.py`
  - `AdditionalOutputs` 增加流程圖 HTML 輸出
  - 執行前：取得 executor 的 `get_visualization()` 並顯示
  - 執行後：更新節點狀態為完成
- [x] T032 [US4] 撰寫 UI 視覺化整合測試 in `tests/unit/ui/test_flow_visualization_ui.py`
  - 測試 `create_flow_visualization()` 回傳 gr.HTML
  - 測試 `update_flow_visualization()` 產生正確 HTML

### 驗證

- [x] T033 [US4] 執行全量測試 `uv run pytest`
- [x] T034 [US4] 執行 `uv run ruff check . && uv run ruff format .`

**Checkpoint**: User Story 4 完成 — Gradio UI 即時流程視覺化 ✅

---

## Phase 5b: User Story 4 補完 - 即時節點狀態追蹤 (Priority: P3)

**Goal**: 補完 US4 的即時視覺化功能（FR-011），流程執行時節點依序高亮（running → completed）

**背景**: Phase 5 僅實作靜態快照（flow_viz_html 只在開頭計算一次），未達到 spec 要求的即時節點狀態追蹤

### 執行器 Callback 機制

- [x] T038 [US4] BaseFlowExecutor.execute() 新增 `on_node_change` callback 參數 in `src/voice_assistant/flows/base.py`
  - 定義 `NodeChangeCallback = Callable[[str, NodeStatus], None]` 型別別名
  - execute() 新增 `on_node_change: NodeChangeCallback | None = None` 參數
- [x] T039 [US4] FlowExecutor: ainvoke → astream + callback in `src/voice_assistant/flows/__init__.py`
  - 使用 `astream(stream_mode="updates")` 取代 `ainvoke()`
  - 每個 chunk 呼叫 `on_node_change(node_name, RUNNING/COMPLETED)`
- [x] T040 [US4] MultiAgentExecutor: ainvoke → astream + callback in `src/voice_assistant/agents/executor.py`
  - 同 T039 模式
- [x] T041 [US4] ToolCallingExecutor: 手動 Mermaid 圖 + callback in `src/voice_assistant/flows/tool_calling_executor.py`
  - 覆寫 `get_visualization()` 回傳手工 Mermaid 圖（llm_call → tool_execute → response_generate）
  - execute() 各步驟呼叫 on_node_change

### Pipeline 即時視覺化

- [x] T042 [US4] Pipeline._get_flow_viz_html() 支援 flow_name + node_statuses in `src/voice_assistant/voice/pipeline.py`
  - 新增 `flow_name` 參數避免使用全域 flow_mode（role-aware bug fix）
  - 新增 `node_statuses` 參數注入狀態
- [x] T043 [US4] Pipeline._get_effective_flow_name() 抽取有效流程名稱 in `src/voice_assistant/voice/pipeline.py`
  - 角色專屬 > 全域設定 邏輯共用化
- [x] T044 [US4] Pipeline: 重構 process_audio_with_outputs 使用 queue + thread in `src/voice_assistant/voice/pipeline.py`
  - 使用 `threading.Thread` + `queue.Queue` 在背景執行 executor
  - executor callback 推送到 queue，generator 消費後即時 yield flow_viz_html
  - 每次 node_change 事件重新渲染 Mermaid + 注入 CSS class

### 測試更新

- [x] T045 [P] [US4] 更新 BaseFlowExecutor 測試 in `tests/unit/flows/test_base_flow_executor.py`
  - 子類別 execute() 簽名包含 on_node_change 參數
- [x] T046 [P] [US4] 更新 ToolCallingExecutor 測試 in `tests/unit/flows/test_tool_calling_executor.py`
  - 測試 get_visualization() 回傳 Mermaid 格式
  - 測試 callback 在有/無 tool_calls 時的完整呼叫序列
- [x] T047 [P] [US4] 新增 Pipeline 即時視覺化測試 in `tests/unit/test_voice_pipeline.py`
  - 測試 _get_effective_flow_name()
  - 測試 _get_flow_viz_html() 接受 flow_name + node_statuses
  - 測試 process_audio_with_outputs 執行期間有多次 UI 更新

### 驗證

- [x] T048 [US4] 執行全量測試 `uv run pytest`
- [x] T049 [US4] 執行 `uv run ruff check --fix . && uv run ruff format .`

**Checkpoint**: User Story 4 即時視覺化補完 ✅

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 程式碼品質、文件收尾

- [x] T035 [P] 最終 Ruff lint + format 檢查 `uv run ruff check --fix . && uv run ruff format .`
- [x] T036 最終全量測試 `uv run pytest` 確認所有測試通過
- [x] T037 [P] 驗證 VoicePipeline 中已無 FlowMode 相關 if/elif 分支（程式碼審查）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: 無依賴 - 可立即開始
- **User Story 1 (Phase 2)**: 依賴 Phase 1 完成 — **核心重構**
- **User Story 2 (Phase 3)**: 依賴 Phase 2 完成
- **User Story 3 (Phase 4)**: 依賴 Phase 2 完成（可與 Phase 3 平行）
- **User Story 4 (Phase 5)**: 依賴 Phase 2 完成（可與 Phase 3, 4 平行）
- **Polish (Phase 6)**: 依賴所有 User Story 完成

### Within Each Phase

- 標示 [P] 的任務可平行執行
- 未標示的任務需依序執行
- 測試任務須在對應實作任務完成後執行

### Parallel Opportunities

Phase 1 平行機會：
- T001, T002 可同時開發（BaseFlowExecutor 介面 + 測試）
- T004 可與 T003 平行

Phase 2 平行機會：
- T006, T007 可同時開發（ToolCallingExecutor + 測試）

Phase 4 平行機會：
- T020, T022 可同時開發（Tool 和 Agent 自動發現測試）

Phase 5 平行機會：
- T026, T028 可同時開發（資料模型 + 測試）

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. 完成 Phase 1: BaseFlowExecutor + FlowRegistry
2. 完成 Phase 2: 適配 3 個 Executor + 重構 VoicePipeline
3. **STOP and VALIDATE**: 所有測試通過，if/elif 消除
4. 可部署驗證

### Incremental Delivery

1. Phase 1 → 基礎介面完成
2. Phase 2 → 統一介面 MVP ✅
3. Phase 3 → FlowRegistry 整合驗證
4. Phase 4 → 自動掃描註冊
5. Phase 5 → UI 視覺化
6. Phase 6 → 收尾

---

## Notes

- [P] 標示 = 不同檔案、無依賴，可平行
- [Story] 標示 = 對應 spec.md 的 User Story
- 每個 User Story 可獨立完成與測試
- 重構過程中必須確保所有現有測試通過
- 不修改 pyproject.toml 版本要求（遵循 AGENTS.md 規範）
- 所有程式碼使用繁體中文註解
- 使用 `uv run` 執行所有 Python 指令
