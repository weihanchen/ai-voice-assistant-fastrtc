# 實作計畫：Flow Builder Agent Skill

**分支**: `010-flow-builder-skill` | **日期**: 2026-02-10 | **規格**: [spec.md](./spec.md)
**輸入**: 功能規格文件 `/specs/010-flow-builder-skill/spec.md`

## 摘要

建立 OpenCode Agent Skill（`.opencode/skills/flow-builder/SKILL.md`），讓開發者用自然語言描述流程需求，OpenCode 自動依照 009 架構（BaseFlowExecutor + FlowRegistry + 節點工廠模式）產生完整的 LangGraph 流程程式碼。此功能的交付物為單一 Markdown 檔案，不涉及任何 Python 原始碼變更。

## 技術背景

**語言/版本**: Python 3.13（Skill 模板中引用的目標程式碼語言）  
**主要依賴**: OpenCode Skill 系統（YAML frontmatter + Markdown）  
**儲存**: 不適用（靜態 Markdown 檔案，無持久化需求）  
**測試**: 人工驗證 — 確認 Skill 可被 OpenCode 載入、模板語法正確  
**目標平台**: OpenCode CLI（跨平台）  
**專案類型**: 單一檔案交付  
**效能目標**: Skill 檔案載入 < 3 秒  
**限制條件**: 檔案大小合理（預估 < 500 行 Markdown）  
**規模/範圍**: 單一 SKILL.md 檔案，5 種程式碼模板，10 步工作流程

## 憲章檢查

*門檻：Phase 0 研究前必須通過。Phase 1 設計完成後需重新檢查。*

| 原則 | 評估 | 說明 |
|------|------|------|
| I. Tool-First Architecture | ✅ PASS | Skill 模板指引 agent 使用既有 Tool 模組（WeatherTool、ExchangeRateTool），並透過 ToolRegistry 自動發現已註冊工具 |
| II. LLM Auto-Routing | ✅ PASS | Skill 模板中的 StateGraph 遵循 LLM 意圖路由模式，不在前端做意圖判斷 |
| III. Human-Friendly Response | ✅ PASS | Skill 指引 agent 產生的 Executor 最終回傳自然語言回應，不直接暴露 JSON |
| IV. Safe Boundary | ✅ PASS | Skill 定義了工具查詢指引，確保 agent 不產生超出範圍的功能 |
| V. Extensible Design | ✅ PASS | Skill 遵循 FlowRegistry 註冊機制，新增流程不需修改核心邏輯，符合 OCP |

**門檻結果**: 全部 PASS，無違規項目。

## 專案結構

### 文件（本功能）

```text
specs/010-flow-builder-skill/
├── plan.md              # 本檔案（/speckit.plan 指令產出）
├── research.md          # Phase 0 產出（/speckit.plan 指令）
├── data-model.md        # Phase 1 產出（/speckit.plan 指令）
├── quickstart.md        # Phase 1 產出（/speckit.plan 指令）
├── checklists/          # 需求檢查清單
│   └── requirements.md
└── tasks.md             # Phase 2 產出（/speckit.tasks 指令，非 /speckit.plan 產出）
```

### 原始碼（專案根目錄）

```text
.opencode/skills/flow-builder/
└── SKILL.md             # 唯一交付物：Flow Builder Agent Skill 定義檔
```

**結構決策**: 此功能僅產出單一 Skill 檔案（`.opencode/skills/flow-builder/SKILL.md`），不涉及 `src/` 或 `tests/` 目錄的任何變更。Skill 內嵌的程式碼模板是指引 agent 在未來使用時產生程式碼的參考範本，不是本次交付的程式碼。

## 合約

不適用 — 此功能產出為 Markdown 檔案（OpenCode Agent Skill），不涉及 API 端點、REST/GraphQL 介面或程式化合約。

## 複雜度追蹤

> 無 Constitution Check 違規項目，此區段不適用。

| 違規項目 | 必要原因 | 拒絕更簡單替代方案的理由 |
|----------|----------|--------------------------|
| （無違規） | — | — |
