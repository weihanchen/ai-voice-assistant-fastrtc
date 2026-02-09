# Implementation Plan: Flow Architecture Refactoring

**Branch**: `009-flow-architecture-refactoring` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-flow-architecture-refactoring/spec.md`

## Summary

重構流程架構，達成「新增流程只需新增檔案」的目標。核心工作包含：(1) 定義 `BaseFlowExecutor` 統一介面，讓 `VoicePipeline` 不再硬編碼流程分支；(2) 建立 `FlowRegistry` 管理所有流程執行器；(3) `ToolRegistry` 和 Agent 支援自動掃描註冊；(4) Gradio UI 整合即時 Mermaid 流程視覺化。所有重構 100% 向後相容，現有 200+ 測試全部通過。

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: LangGraph >=1.0.5, OpenAI SDK >=1.58.x, Pydantic >=2.10.x, FastRTC >=0.0.33, Gradio >=5.x
**Storage**: N/A（無持久化需求）
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server / Windows / Docker container
**Project Type**: Single project（延續現有架構）
**Performance Goals**: 重構後流程執行延遲增加不超過 50ms（Registry 查詢開銷）
**Constraints**: 100% 向後相容，現有測試全部通過，不修改 pyproject.toml 版本要求
**Scale/Scope**: 3 種流程模式（tools/langgraph/multi_agent）+ 3 個 Tool + 4 個 Agent

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 檢查項目 | 狀態 |
|------|----------|------|
| **I. Tool-First Architecture** | Tool 自動掃描不改變 BaseTool 繼承模式 | ✅ 符合 |
| **II. LLM Auto-Routing** | FlowRegistry 不影響 LLM 路由邏輯 | ✅ 符合 |
| **III. Human-Friendly Response** | 重構不影響回應格式 | ✅ 符合 |
| **IV. Safe Boundary** | 自動掃描僅掃描專案內模組 | ✅ 符合 |
| **V. Extensible Design** | 統一介面 + Registry = 最大擴充彈性 | ✅ 符合 |

**Quality Gates:**
- ✅ 現有 200+ 測試全部通過
- ✅ 新增 BaseFlowExecutor / FlowRegistry / 自動掃描的單元測試
- ✅ Ruff lint + format 通過
- ✅ 重構後 VoicePipeline 無 flow mode `if/elif` 分支

## Project Structure

### Documentation (this feature)

```text
specs/009-flow-architecture-refactoring/
├── spec.md              # 規格文件
├── plan.md              # This file
├── data-model.md        # 資料模型
└── tasks.md             # 任務清單
```

### Source Code (repository root)

```text
src/voice_assistant/
├── config.py                       # 🔧 FlowMode 保持不變
├── flows/
│   ├── __init__.py                 # 🔧 匯出 FlowExecutor（適配後）
│   ├── base.py                     # 🆕 BaseFlowExecutor ABC
│   ├── registry.py                 # 🆕 FlowRegistry
│   ├── tool_calling_executor.py    # 🆕 ToolCallingExecutor（封裝 legacy Tool Calling）
│   ├── visualization.py            # 🔧 擴充：節點狀態追蹤
│   ├── state.py                    # 不變
│   ├── graphs/                     # 不變
│   └── nodes/                      # 不變
├── agents/
│   ├── executor.py                 # 🔧 MultiAgentExecutor 適配 BaseFlowExecutor
│   ├── graph.py                    # 🔧 支援動態 Agent 發現
│   └── ...                         # 其他不變
├── tools/
│   ├── registry.py                 # 🔧 新增 auto_discover() 方法
│   └── ...                         # BaseTool、具體 Tool 不變
├── voice/
│   ├── pipeline.py                 # 🔧 消除 if/elif，改用 FlowRegistry
│   ├── handlers/
│   │   └── reply_on_pause.py       # 🔧 簡化 composition root
│   └── ui/
│       └── blocks.py               # 🔧 新增流程視覺化面板
└── ui/                             # 不變

tests/
├── unit/
│   ├── flows/
│   │   ├── test_base_flow_executor.py   # 🆕 BaseFlowExecutor 測試
│   │   ├── test_flow_registry.py        # 🆕 FlowRegistry 測試
│   │   └── test_tool_calling_executor.py # 🆕 ToolCallingExecutor 測試
│   └── tools/
│       └── test_auto_discover.py        # 🆕 自動掃描測試
└── integration/
    └── test_flow_refactoring.py         # 🆕 重構整合測試
```

**Structure Decision**: 在現有 `flows/` 模組下新增 `base.py`（BaseFlowExecutor）和 `registry.py`（FlowRegistry），不建立新的頂層模組。`ToolCallingExecutor` 放在 `flows/` 下，因為它本質上是一種流程執行器。

## Data Model

### BaseFlowExecutor（抽象介面）

```python
from abc import ABC, abstractmethod


class BaseFlowExecutor(ABC):
    """流程執行器的統一介面。

    所有流程模式（tools/langgraph/multi_agent/自定義）
    都必須實作此介面。
    """

    @property
    @abstractmethod
    def flow_name(self) -> str:
        """流程名稱（用於 FlowRegistry 查詢）。"""
        ...

    @abstractmethod
    async def execute(self, user_input: str) -> str:
        """執行流程。

        Args:
            user_input: 使用者輸入文字

        Returns:
            回應文字
        """
        ...

    def get_visualization(self) -> str | None:
        """取得流程視覺化 Mermaid 圖（可選實作）。

        Returns:
            Mermaid 格式字串，不支援時回傳 None
        """
        return None
```

### FlowRegistry

```python
class FlowRegistry:
    """流程執行器註冊表。"""

    def register(self, executor: BaseFlowExecutor) -> None: ...
    def get(self, name: str) -> BaseFlowExecutor: ...
    def list_flows(self) -> list[str]: ...
    def has(self, name: str) -> bool: ...
```

### ToolCallingExecutor（適配器）

```python
class ToolCallingExecutor(BaseFlowExecutor):
    """將 legacy Tool Calling 邏輯封裝為 BaseFlowExecutor。

    封裝原本在 VoicePipeline._process_with_legacy() 的邏輯。
    """

    @property
    def flow_name(self) -> str:
        return "tools"

    async def execute(self, user_input: str) -> str: ...
```

### 適配現有 Executor

```python
# FlowExecutor 新增
class FlowExecutor(BaseFlowExecutor):
    @property
    def flow_name(self) -> str:
        return "langgraph"
    # execute() 和 get_visualization() 已有

# MultiAgentExecutor 新增
class MultiAgentExecutor(BaseFlowExecutor):
    @property
    def flow_name(self) -> str:
        return "multi_agent"
    # execute() 已有
```

### VoicePipeline 重構後

```python
# 重構前（if/elif 分支）:
if effective_flow_mode == FlowMode.MULTI_AGENT:
    response = _run_async_safely(self._process_with_multi_agent(user_text))
elif effective_flow_mode == FlowMode.LANGGRAPH:
    response = _run_async_safely(self._process_with_flow(user_text))
else:
    response = _run_async_safely(self._process_with_legacy(user_text))

# 重構後（統一介面）:
executor = self.flow_registry.get(effective_flow_mode.value)
response = _run_async_safely(executor.execute(user_text))
```

### ToolRegistry 自動掃描

```python
class ToolRegistry:
    # 現有方法保持不變，新增：
    @classmethod
    def auto_discover(cls, package: str = "voice_assistant.tools") -> "ToolRegistry":
        """自動掃描套件下的 BaseTool 子類別並建立 Registry。"""
        ...
```

### 視覺化資料模型

```python
class NodeStatus(str, Enum):
    PENDING = "pending"      # 灰色
    RUNNING = "running"      # 黃色
    COMPLETED = "completed"  # 綠色
    FAILED = "failed"        # 紅色

class FlowVisualization(BaseModel):
    """流程視覺化狀態。"""
    mermaid_code: str
    node_statuses: dict[str, NodeStatus] = {}
```

## Implementation Strategy

### Phase 1: BaseFlowExecutor + FlowRegistry（P1 核心）

**目標**：建立統一介面和註冊表，消除 VoicePipeline 的 if/elif 分支。

1. 建立 `flows/base.py`：定義 `BaseFlowExecutor` ABC
2. 建立 `flows/registry.py`：實作 `FlowRegistry`
3. 建立 `flows/tool_calling_executor.py`：封裝 legacy Tool Calling
4. 適配 `FlowExecutor`：繼承 `BaseFlowExecutor`，新增 `flow_name` property
5. 適配 `MultiAgentExecutor`：繼承 `BaseFlowExecutor`，新增 `flow_name` property
6. 重構 `VoicePipeline`：注入 `FlowRegistry`，消除 if/elif 分支
7. 重構 `reply_on_pause.py`：使用 FlowRegistry 組裝

### Phase 2: Tool/Agent 自動註冊（P2）

**目標**：降低新增 Tool/Agent 的摩擦力。

1. `ToolRegistry.auto_discover()`：掃描 `tools/` 目錄，自動實例化 `BaseTool` 子類別
2. Agent 自動發現：掃描 `agents/` 目錄，自動實例化 `BaseAgent` 子類別
3. 簡化 `reply_on_pause.py`：替換手動 register 為 auto_discover

### Phase 3: Gradio UI 即時視覺化（P3）

**目標**：在 Gradio UI 中顯示即時流程圖。

1. 定義 `FlowVisualization` 資料模型
2. 擴充 `visualization.py`：支援節點狀態高亮的 Mermaid 輸出
3. Gradio UI 新增 `gr.HTML` 元件，載入 mermaid.js CDN 渲染
4. VoicePipeline 執行時透過 `AdditionalOutputs` 傳送流程圖更新

## Complexity Tracking

> 無憲章違規，不需填寫此區塊。
