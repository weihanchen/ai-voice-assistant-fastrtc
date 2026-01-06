# Implementation Plan: LangGraph Travel Flow

**Branch**: `006-langgraph-travel-flow` | **Date**: 2026-01-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-langgraph-travel-flow/spec.md`

## Summary

整合 LangGraph StateGraph 實現對話流程編排，包含意圖分類路由與多步驟旅遊規劃子流程。系統將根據使用者輸入自動分流至天氣/匯率/股票查詢（保留現有 Tool）或旅遊規劃流程（新增 SubGraph），並提供流程視覺化輸出功能。

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: LangGraph, OpenAI SDK >=1.58.x, Pydantic >=2.10.x, FastRTC >=0.0.33
**Storage**: N/A（無持久化需求）
**Testing**: pytest >=8.x（單元測試 + mock 測試）
**Target Platform**: Linux server / Windows（本地開發）/ Docker
**Project Type**: single
**Performance Goals**: 旅遊規劃流程回應 < 8 秒，路由額外延遲 < 1 秒
**Constraints**: 保持現有 Tool 功能 100% 向後相容
**Scale/Scope**: 4 種意圖路由、1 個多步驟子流程（5 個節點）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Tool-First Architecture** | ✅ Pass | 旅遊流程內部呼叫現有 WeatherTool，不直接呼叫 API |
| **II. LLM Auto-Routing** | ✅ Pass | 意圖分類由 LLM 判斷，LangGraph 負責流程編排 |
| **III. Human-Friendly Response** | ✅ Pass | 所有回應經 LLM 轉換為口語化繁體中文 |
| **IV. Safe Boundary** | ✅ Pass | 旅遊規劃僅限台灣城市，使用靜態景點清單 |
| **V. Extensible Design** | ✅ Pass | Flow 模組獨立，透過 FlowRegistry 管理，不影響現有架構 |

### Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| 每個模組必須有單元測試 | ✅ Required | flows/ 模組需有完整測試 |
| API 整合需有 mock 測試 | ✅ Required | WeatherTool 呼叫需 mock |
| 語音回應延遲 < 5 秒 | ⚠️ Adjusted | 旅遊流程允許 8 秒（多步驟） |
| 所有程式碼必須通過 Ruff 檢查 | ✅ Required | 包含型別標註 |

## Project Structure

### Documentation (this feature)

```text
specs/006-langgraph-travel-flow/
├── spec.md              # 規格文件
├── plan.md              # 實作計畫（本文件）
├── research.md          # Phase 0: 技術研究
├── data-model.md        # Phase 1: 資料模型
├── quickstart.md        # Phase 1: 快速開始指南
├── contracts/           # Phase 1: 介面合約
│   └── flow-interface.md
├── checklists/          # 檢查清單
│   └── requirements.md
└── tasks.md             # Phase 2: 任務清單
```

### Source Code (repository root)

```text
src/voice_assistant/
├── flows/                      # 🆕 LangGraph 流程模組
│   ├── __init__.py             # 模組匯出
│   ├── state.py                # FlowState, TravelPlanState 定義
│   ├── nodes/                  # 流程節點
│   │   ├── __init__.py
│   │   ├── classifier.py       # 意圖分類節點
│   │   ├── tool_executor.py    # Tool 執行節點
│   │   └── travel/             # 旅遊規劃子流程節點
│   │       ├── __init__.py
│   │       ├── destination.py  # 解析目的地
│   │       ├── weather.py      # 查詢天氣
│   │       ├── evaluator.py    # 評估天氣條件
│   │       └── recommender.py  # 產生建議
│   ├── graphs/                 # 流程圖定義
│   │   ├── __init__.py
│   │   ├── main_router.py      # 主路由流程
│   │   └── travel_planner.py   # 旅遊規劃子流程
│   └── visualization.py        # Mermaid 視覺化輸出
├── tools/                      # 現有工具（不變）
│   ├── weather.py
│   ├── exchange_rate.py
│   └── stock_price.py
├── llm/                        # 現有 LLM 客戶端（不變）
└── voice/
    └── pipeline.py             # 擴展：整合 FlowExecutor

tests/
├── unit/
│   └── flows/                  # 🆕 流程模組測試
│       ├── test_state.py
│       ├── test_classifier.py
│       ├── test_travel_nodes.py
│       └── test_graphs.py
└── integration/
    └── test_flow_integration.py
```

**Structure Decision**: 採用 Single Project 結構，在現有 `src/voice_assistant/` 下新增 `flows/` 子模組。保持與現有 `tools/`、`llm/`、`voice/` 平行的模組化設計。

## Complexity Tracking

> 無違反憲章的情況，此區塊不適用。

## Implementation Phases

### Phase 0: Research (見 research.md)

- LangGraph StateGraph 最佳實踐
- LangGraph 與 OpenAI SDK 整合模式
- 條件路由 (Conditional Edges) 實作方式
- SubGraph 組合模式
- Mermaid 視覺化 API 使用方式

### Phase 1: Design (見 data-model.md, contracts/)

- FlowState 資料模型設計
- TravelPlanState 資料模型設計
- 節點介面定義
- 主路由流程圖結構
- 旅遊子流程圖結構

### Phase 2: Tasks (見 tasks.md)

由 `/speckit.tasks` 指令產生，包含：
- 依賴套件安裝
- State 模型實作
- 各節點實作
- 流程圖組裝
- Pipeline 整合
- 單元測試
- 整合測試
