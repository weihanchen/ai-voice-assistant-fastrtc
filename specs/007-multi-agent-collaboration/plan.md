# Implementation Plan: Multi-Agent Collaboration

**Branch**: `007-multi-agent-collaboration` | **Date**: 2025-01-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-multi-agent-collaboration/spec.md`

## Summary

實作多代理協作系統，透過 Supervisor Agent 將使用者的複雜請求拆解為多個子任務，並分派給專家 Agent（Weather/Finance/Travel/General）並行處理，最後彙整結果回應使用者。採用 LangGraph 作為流程編排框架，重用現有 Tool 實作，並支援透過 FLOW_MODE 環境變數切換處理模式。

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: LangGraph, OpenAI SDK, Pydantic, FastRTC
**Storage**: N/A（無持久化需求）
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server / Docker container
**Project Type**: Single project（延續現有架構）
**Performance Goals**: 多 Agent 並行處理時間 < 5 秒，總處理時間不超過最慢 Agent 的 1.2 倍
**Constraints**: 100% 向後相容現有流程，可透過環境變數切換模式
**Scale/Scope**: 4 個專家 Agent（Weather/Finance/Travel/General）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 檢查項目 | 狀態 |
|------|----------|------|
| **I. Tool-First Architecture** | Agent 透過現有 Tool 存取外部 API | ✅ 符合 |
| **II. LLM Auto-Routing** | Supervisor 使用 LLM 進行任務拆解 | ✅ 符合 |
| **III. Human-Friendly Response** | Aggregator 產生自然語言回應 | ✅ 符合 |
| **IV. Safe Boundary** | Agent 僅處理定義範圍內的任務 | ✅ 符合 |
| **V. Extensible Design** | Agent 採用統一介面，可擴展新增 | ✅ 符合 |

**Quality Gates:**
- ✅ 每個 Agent 需有單元測試
- ✅ 整合測試覆蓋 Multi-Agent 流程
- ✅ 延遲 < 5 秒
- ✅ 逾時處理機制

## Project Structure

### Documentation (this feature)

```text
specs/007-multi-agent-collaboration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── multi-agent-flow.md
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/voice_assistant/
├── agents/                    # 🆕 Multi-Agent 模組
│   ├── __init__.py
│   ├── state.py               # MultiAgentState 定義
│   ├── base.py                # BaseAgent 抽象類別
│   ├── supervisor.py          # SupervisorAgent（任務拆解）
│   ├── weather.py             # WeatherAgent
│   ├── finance.py             # FinanceAgent（匯率+股價）
│   ├── travel.py              # TravelAgent
│   ├── general.py             # GeneralAgent（閒聊/fallback）
│   └── graph.py               # create_multi_agent_graph()
├── config.py                  # 🔧 新增 FLOW_MODE 設定
├── flows/
│   ├── executor.py            # 🔧 修改：根據 FLOW_MODE 選擇流程
│   └── ...                    # 現有流程保持不變
└── ...

tests/
├── unit/
│   └── agents/                # 🆕 Agent 單元測試
│       ├── test_supervisor.py
│       ├── test_weather_agent.py
│       ├── test_finance_agent.py
│       ├── test_travel_agent.py
│       └── test_general_agent.py
└── integration/
    └── test_multi_agent_flow.py  # 🆕 整合測試
```

**Structure Decision**: 新增 `agents/` 模組與現有 `flows/` 平行，透過 `config.FLOW_MODE` 決定使用哪個流程。

## Complexity Tracking

> 無憲章違規，不需填寫此區塊。
