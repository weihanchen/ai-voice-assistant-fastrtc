# Feature Specification: Flow Architecture Refactoring

**Feature Branch**: `009-flow-architecture-refactoring`  
**Created**: 2026-02-08  
**Status**: Draft  
**Input**: User description: "重構流程架構，統一 FlowExecutor 介面、建立 FlowRegistry 自動發現機制、Tool/Agent 自動註冊、Gradio UI 即時流程視覺化，為後續 Flow Builder Agent Skill 奠定基礎"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 統一流程執行介面 (Priority: P1)

開發者新增一種流程模式時，只需實作統一的 `BaseFlowExecutor` 介面，VoicePipeline 不需要任何修改即可使用新流程。現有的 `FlowExecutor`（LangGraph）、`MultiAgentExecutor`（Multi-Agent）和 legacy Tool Calling 模式都適配到同一介面。

**Why this priority**: 這是整個重構的核心基礎。目前 VoicePipeline 中以 `if/elif` 分支硬編碼三種流程模式，違反開放封閉原則（OCP）。不解決這個問題，後續所有擴充都會受限。

**Independent Test**: 建立一個最小的測試用 FlowExecutor 實作 `BaseFlowExecutor` 介面，驗證 VoicePipeline 可以不修改核心程式碼就使用該流程。

**Acceptance Scenarios**:

1. **Given** 系統已定義 `BaseFlowExecutor` 介面, **When** 開發者建立新的 `CustomFlowExecutor` 實作該介面, **Then** 該 executor 可被 VoicePipeline 使用而不需修改 VoicePipeline 的程式碼
2. **Given** 現有 `FlowExecutor` 已適配為 `BaseFlowExecutor`, **When** 設定 `FLOW_MODE=langgraph`, **Then** 系統行為與重構前完全一致
3. **Given** 現有 `MultiAgentExecutor` 已適配為 `BaseFlowExecutor`, **When** 設定 `FLOW_MODE=multi_agent`, **Then** 系統行為與重構前完全一致
4. **Given** legacy Tool Calling 已封裝為 `ToolCallingExecutor`, **When** 設定 `FLOW_MODE=tools`, **Then** 系統行為與重構前完全一致

---

### User Story 2 - FlowRegistry 自動發現與註冊 (Priority: P1)

開發者新增一個流程只需要在 `flows/` 目錄下新增一個 Python 模組並實作 `BaseFlowExecutor`，系統啟動時自動掃描並註冊。FlowRegistry 提供按名稱查詢和列舉已註冊流程的能力。

**Why this priority**: 與 P1-Story1 同等重要。沒有自動發現機制，每次新增流程仍需手動修改 composition root，無法達成「新增檔案即擴充」的目標。

**Independent Test**: 在 `flows/` 目錄下新增一個實作 `BaseFlowExecutor` 的模組，重啟系統後 `FlowRegistry.list_flows()` 能列出該新流程。

**Acceptance Scenarios**:

1. **Given** `FlowRegistry` 已初始化, **When** 呼叫 `registry.list_flows()`, **Then** 回傳所有已註冊流程的名稱列表，至少包含 `tools`、`langgraph`、`multi_agent`
2. **Given** `FlowRegistry` 已註冊多個流程, **When** 呼叫 `registry.get("langgraph")`, **Then** 回傳對應的 `BaseFlowExecutor` 實例
3. **Given** VoicePipeline 接收到使用者輸入, **When** 需要選擇流程模式, **Then** 透過 `FlowRegistry` 取得對應的 executor 而非硬編碼的 `if/elif`

---

### User Story 3 - Tool 與 Agent 自動註冊 (Priority: P2)

開發者新增 Tool 只需在 `tools/` 目錄下新增一個繼承 `BaseTool` 的模組；新增 Agent 只需在 `agents/` 目錄下新增一個繼承 `BaseAgent` 的模組。系統啟動時自動掃描並註冊，不需修改 composition root。

**Why this priority**: 降低新增工具和代理的摩擦力。目前每次新增都需修改 `reply_on_pause.py` 和 `agents/graph.py`，增加出錯風險。此 Story 依賴 P1 的基礎架構已到位。

**Independent Test**: 在 `tools/` 目錄下新增一個繼承 `BaseTool` 的模組，重啟系統後 `ToolRegistry.list_tools()` 能列出該新工具。

**Acceptance Scenarios**:

1. **Given** `ToolRegistry` 支援自動掃描, **When** `tools/` 目錄下存在繼承 `BaseTool` 的模組, **Then** 系統啟動時自動註冊該工具，不需修改 composition root
2. **Given** 自動註冊機制已啟用, **When** 列出已註冊工具, **Then** 至少包含 `get_weather`、`get_exchange_rate`、`get_stock_price` 三個現有工具
3. **Given** `agents/` 目錄下存在繼承 `BaseAgent` 的模組, **When** 系統初始化 Multi-Agent graph, **Then** 自動發現並納入該 Agent

---

### User Story 4 - Gradio UI 即時流程視覺化 (Priority: P3)

使用者在 Gradio 網頁 UI 中可以看到當前流程的即時執行狀態圖。流程圖以 Mermaid 格式渲染，執行中的節點以視覺高亮顯示（例如：綠色=完成、黃色=執行中、灰色=待執行）。

**Why this priority**: 這是使用者體驗的提升功能，不影響核心流程的正確性。依賴 P1 的 `BaseFlowExecutor` 介面中的 `get_visualization()` 方法已到位。

**Independent Test**: 在 Gradio UI 中發起一次對話，觀察流程視覺化面板是否即時顯示目前流程的執行狀態圖。

**Acceptance Scenarios**:

1. **Given** 使用者開啟 Gradio UI, **When** 頁面載入完成, **Then** 右側面板顯示當前流程模式的靜態 Mermaid 流程圖
2. **Given** 使用者正在與助理對話, **When** 流程執行到某個節點, **Then** 流程圖中對應節點以高亮顏色標示（黃色=執行中）
3. **Given** 流程執行完畢, **When** 所有節點處理完成, **Then** 完成的節點以綠色標示，整體流程圖呈現完成狀態

---

### Edge Cases

- 當 `FlowRegistry` 中不存在指定名稱的流程時，回傳友善錯誤訊息並 fallback 到預設流程（tools 模式）
- 當自動掃描發現有 import 錯誤的模組時，記錄警告 log 但不影響其他模組的註冊
- 當 `BaseFlowExecutor.execute()` 執行逾時時，VoicePipeline 回傳超時錯誤訊息
- 當 Mermaid 視覺化渲染失敗時，流程圖面板顯示「無法載入流程圖」提示，不影響對話功能
- 當角色的 `preferred_flow_mode` 指向的流程不存在時，fallback 到全域設定的流程模式
- 當自動註冊發現重複名稱的 Tool 或 Agent 時，記錄警告 log 並使用後掃描到的版本

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 定義 `BaseFlowExecutor` 抽象介面，包含 `execute(user_input) -> str`、`flow_name -> str` 和可選的 `get_visualization() -> str | None` 方法
- **FR-002**: 系統 MUST 將現有 `FlowExecutor` 適配為 `BaseFlowExecutor` 的實作
- **FR-003**: 系統 MUST 將現有 `MultiAgentExecutor` 適配為 `BaseFlowExecutor` 的實作
- **FR-004**: 系統 MUST 將 legacy Tool Calling 邏輯封裝為 `ToolCallingExecutor`，實作 `BaseFlowExecutor` 介面
- **FR-005**: 系統 MUST 提供 `FlowRegistry`，支援 `register()`、`get(name)`、`list_flows()` 操作
- **FR-006**: `VoicePipeline` MUST 僅依賴 `BaseFlowExecutor` 介面，消除 `if/elif` 流程分支
- **FR-007**: 系統 MUST 支援 `ToolRegistry` 自動掃描 `tools/` 目錄下的 `BaseTool` 子類別
- **FR-008**: 系統 MUST 支援自動掃描 `agents/` 目錄下的 `BaseAgent` 子類別
- **FR-009**: `BaseFlowExecutor` MUST 提供 `get_visualization()` 方法，回傳 Mermaid 格式流程圖
- **FR-010**: Gradio UI MUST 新增流程視覺化面板，渲染 Mermaid 流程圖
- **FR-011**: 流程執行時 MUST 透過 callback 機制回報當前節點狀態，供視覺化即時更新
- **FR-012**: 所有重構 MUST 100% 向後相容，現有測試全部通過
- **FR-013**: `FlowRegistry` MUST 在查詢不存在的流程時拋出明確異常或 fallback 到預設流程

### Key Entities

- **BaseFlowExecutor**: 流程執行器的統一介面，定義所有流程模式必須實作的契約
- **FlowRegistry**: 流程註冊表，管理所有已註冊的 `BaseFlowExecutor` 實例，支援按名稱查詢
- **ToolCallingExecutor**: 將 legacy Tool Calling 邏輯封裝為 `BaseFlowExecutor` 的適配器
- **FlowVisualization**: 流程視覺化資料模型，包含 Mermaid 圖和節點狀態（待執行/執行中/完成）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 現有 200+ 測試全部通過，零迴歸
- **SC-002**: VoicePipeline 中消除所有流程模式相關的 `if/elif` 分支，僅依賴 `BaseFlowExecutor` 介面
- **SC-003**: 新增一個流程模式所需修改的檔案數從 3+ 降為 1（僅新增流程模組本身）
- **SC-004**: Composition root（`reply_on_pause.py`）中的硬編碼工具/代理註冊程式碼替換為自動掃描
- **SC-005**: Gradio UI 中可見流程視覺化面板，顯示當前流程的 Mermaid 圖
- **SC-006**: Ruff lint 和 format 檢查全部通過

## Assumptions

- 現有 `FlowExecutor` 和 `MultiAgentExecutor` 的 `execute()` 簽名可統一為 `async execute(user_input: str) -> str`
- 自動掃描使用 `importlib` 和 `inspect` 模組，不需要額外依賴
- Mermaid 流程圖可透過前端 JavaScript（mermaid.js CDN）在 Gradio 的 `gr.HTML` 元件中渲染
- LangGraph 的 `graph.get_graph().draw_mermaid()` 方法持續可用
- 重構過程中可逐步進行，每個 User Story 完成後系統仍可正常運作

## Dependencies

- 000-ai-voice-assistant（BaseTool, ToolRegistry 基礎架構）
- 006-langgraph-travel-flow（FlowExecutor, LangGraph 流程）
- 007-multi-agent-collaboration（MultiAgentExecutor, Multi-Agent 流程）
- 008-role-switching（角色系統的 `preferred_flow_mode` 需適配新 FlowRegistry）

## Out of Scope

- 新增額外的流程模式（本 spec 僅重構現有三種模式的架構）
- Flow Builder Agent Skill（將在 010 spec 中實作，基於本 spec 的重構成果）
- 多輪對話的流程狀態持久化
- 流程的版本管理或 A/B 測試機制
- 效能優化（如流程快取、預載入）
- 角色系統的重構（僅適配 `preferred_flow_mode` 到新 FlowRegistry）
