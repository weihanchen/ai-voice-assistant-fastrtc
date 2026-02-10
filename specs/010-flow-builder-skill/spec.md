# Feature Specification: Flow Builder Agent Skill

**Feature Branch**: `010-flow-builder-skill`  
**Created**: 2026-02-10  
**Status**: Draft  
**Input**: User description: "Flow Builder Agent Skill：開發 OpenCode Agent Skill，讓開發者用自然語言描述流程，OpenCode 自動產生完整的 LangGraph 流程程式碼。基於 009 重構後的 BaseFlowExecutor + FlowRegistry 架構，產生的程式碼可直接插入系統運行。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Skill 基礎框架與工作流程 (Priority: P1)

作為開發者，我希望當我在 OpenCode 中說「建立流程」、「新增 flow」或「設計一個工作流」時，OpenCode 能載入 Flow Builder Skill 並引導我完成流程定義和程式碼產生，以便我不需要手動撰寫重複的 boilerplate 程式碼。

**Why this priority**: 這是 Skill 的核心價值。沒有基礎框架和工作流程定義，後續的模板和驗證都無法運作。Skill 檔案本身就是最小可交付單元。

**Independent Test**: 可透過在 OpenCode 中載入 Skill 檔案並確認其格式正確、步驟完整來獨立測試。

**Acceptance Scenarios**:

1. **Given** Skill 檔案已放置在正確路徑，**When** 開發者觸發 Skill 載入，**Then** OpenCode 成功載入並顯示 Skill 內容，包含完整的 10 步工作流程。
2. **Given** Skill 已載入，**When** 開發者提供自然語言流程描述（如「建立一個美食推薦流程」），**Then** OpenCode 依照 Skill 定義的步驟依序執行，從需求解析到程式碼產生。
3. **Given** Skill 已載入，**When** 開發者的流程描述過於模糊（如只說「建立一個流程」），**Then** OpenCode 根據 Skill 的指引向開發者詢問關鍵細節（流程目標、步驟、資料流）。

---

### User Story 2 - 程式碼模板系統 (Priority: P1)

作為 OpenCode agent，我希望 Skill 內含完整的程式碼模板（FlowState、Node、Graph、Executor、Test），以便產生的程式碼一致遵循專案的架構慣例，不需要每次重新推斷正確的程式結構。

**Why this priority**: 模板是程式碼產生的基礎。沒有準確的模板，產生的程式碼將無法與現有架構整合，也無法通過品質檢查。

**Independent Test**: 可透過檢視 Skill 中的模板是否涵蓋所有必要元件類型，並驗證模板語法正確來獨立測試。

**Acceptance Scenarios**:

1. **Given** Skill 中定義了 FlowState 模板，**When** agent 需要產生新的流程狀態，**Then** 產生的程式碼遵循 TypedDict + `total=False` 模式，並包含必要的型別標註。
2. **Given** Skill 中定義了 Node 工廠函式模板，**When** agent 需要產生新的節點，**Then** 產生的程式碼遵循 `create_*_node()` 閉包注入模式，回傳 `dict[str, Any]`。
3. **Given** Skill 中定義了 StateGraph 模板，**When** agent 需要產生新的流程圖，**Then** 產生的程式碼包含 `StateGraph` 定義、節點新增、邊設定、條件路由。
4. **Given** Skill 中定義了 Executor 模板，**When** agent 需要產生新的流程執行器，**Then** 產生的程式碼繼承 `BaseFlowExecutor`，正確實作 `flow_name`、`execute`、`get_visualization` 方法。
5. **Given** Skill 中定義了測試模板，**When** agent 需要產生測試，**Then** 產生的程式碼使用 pytest + pytest-asyncio，mock 外部依賴，覆蓋正常和異常情境。

---

### User Story 3 - 現有工具整合指引 (Priority: P2)

作為 OpenCode agent，我希望 Skill 說明如何識別和重用現有工具（如 WeatherTool、ExchangeRateTool），以便產生的流程能正確調用已註冊的工具，而不是重複實作相同功能。

**Why this priority**: 工具重用是避免功能重複的關鍵，但開發者仍可手動處理工具整合。此 Story 提升效率但非核心阻斷項。

**Independent Test**: 可透過確認 Skill 中包含工具查詢和調用的說明來獨立測試。

**Acceptance Scenarios**:

1. **Given** 系統中已註冊 WeatherTool，**When** 開發者描述的流程包含天氣查詢步驟，**Then** agent 依照 Skill 指引識別可重用的 WeatherTool，而非產生新的天氣查詢程式碼。
2. **Given** 流程需要的功能不在現有工具中，**When** agent 評估後判斷需要新工具，**Then** agent 依照 Skill 指引提醒開發者需要先建立新工具。

---

### User Story 4 - 驗證與品質保證流程 (Priority: P2)

作為開發者，我希望 Skill 定義產生程式碼後的驗證步驟，以便確保產生的程式碼品質符合專案標準，可直接合併到主分支。

**Why this priority**: 品質保證確保產生的程式碼可用，但即使沒有自動化驗證步驟，開發者也能手動執行檢查。

**Independent Test**: 可透過確認 Skill 中包含明確的驗證命令和檢查清單來獨立測試。

**Acceptance Scenarios**:

1. **Given** agent 已產生完整的流程程式碼，**When** 執行 Skill 定義的驗證步驟，**Then** 依序執行程式碼檢查、格式化、測試，並回報結果。
2. **Given** 驗證過程中發現問題（如 lint 錯誤），**When** agent 嘗試修復，**Then** agent 根據 Skill 的常見錯誤清單自動修正問題後重新驗證。

---

### Edge Cases

- 當開發者描述的流程與現有流程（如 travel_planner）功能重疊時，Skill 應指引 agent 提醒開發者，並建議擴展現有流程而非建立新流程。
- 當開發者描述的流程包含超過 10 個節點時，Skill 應指引 agent 建議拆分為多個子流程。
- 當開發者描述的流程需要外部 API 但專案中尚無對應工具時，Skill 應指引 agent 明確告知開發者需要先建立工具。
- 當流程描述語言不明確（如同時包含中英文技術術語），Skill 應指引 agent 以繁體中文為主要輸出語言。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Skill 檔案 MUST 存在於 `.opencode/skills/flow-builder/SKILL.md` 路徑
- **FR-002**: Skill MUST 包含觸發條件說明，列出觸發 Skill 的關鍵字清單
- **FR-003**: Skill MUST 定義完整的 10 步工作流程，每步有明確的輸入、動作、輸出
- **FR-004**: Skill MUST 包含 5 種程式碼模板：FlowState、Node、StateGraph、BaseFlowExecutor 子類別、pytest 測試
- **FR-005**: 所有程式碼模板 MUST 使用佔位符標記可替換部分（如 `<DOMAIN>`、`<NodeName>`）
- **FR-006**: Skill MUST 包含現有工具查詢和重用的指引說明
- **FR-007**: Skill MUST 定義驗證步驟（程式碼檢查、格式化、測試執行）
- **FR-008**: Skill MUST 包含常見錯誤檢查清單（import 路徑、型別標註、async/await 等）
- **FR-009**: Skill MUST 定義完成後的回報格式，列出產生的所有檔案
- **FR-010**: 所有模板和說明 MUST 使用繁體中文撰寫

### Key Entities

- **Skill 檔案**：OpenCode Agent Skill 定義檔，包含觸發條件、工作流程、程式碼模板、品質規則。格式為 YAML frontmatter + Markdown。
- **程式碼模板**：嵌入 Skill 中的 fenced code blocks，使用佔位符標記可替換部分。涵蓋 State、Node、Graph、Executor、Test 五種類型。
- **工作流程**：Skill 指引 agent 執行的 10 步驟流程，從需求解析到驗證完成。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Skill 檔案可在 3 秒內被 OpenCode 成功載入，且內容完整呈現
- **SC-002**: 開發者從輸入流程描述到取得完整程式碼套件，整個流程可在 10 分鐘內完成
- **SC-003**: 產生的程式碼 100% 通過專案的程式碼品質檢查（lint + format）
- **SC-004**: 產生的測試程式碼可獨立執行且 100% 通過
- **SC-005**: 產生的程式碼遵循專案架構慣例的符合率達 100%（正確繼承基底類別、使用標準模式）
- **SC-006**: 開發者在首次使用 Skill 時，無需額外查閱文件即可成功產生可運行的流程程式碼

## Assumptions

- 開發者已具備基本的 LangGraph 概念理解（節點、邊、狀態）
- 專案已完成 009 架構重構，BaseFlowExecutor、FlowRegistry 等介面穩定不變
- OpenCode 支援 `.opencode/skills/` 目錄下的 SKILL.md 格式
- Skill 的輸出是指引 OpenCode agent 產生程式碼，而非自動執行腳本
- 產生的程式碼需要開發者審查後才合併，Skill 不直接修改 production code

## Scope

### 包含

- `.opencode/skills/flow-builder/SKILL.md` 檔案的完整內容
- 嵌入 Skill 中的 5 種程式碼模板
- 10 步工作流程定義
- 品質規則和驗證步驟

### 不包含

- 不修改任何現有 Python 原始碼
- 不建立新的 Python 模組或套件
- 不修改 FlowRegistry、BaseFlowExecutor 等現有介面
- 不實作具體的流程（Skill 是產生器，不是成品）
- 不建立自動化腳本（Skill 指引 agent 手動執行命令）

## Dependencies

- Spec 009：Flow Architecture Refactoring（已完成）— 提供 BaseFlowExecutor、FlowRegistry、節點工廠模式等架構基礎
