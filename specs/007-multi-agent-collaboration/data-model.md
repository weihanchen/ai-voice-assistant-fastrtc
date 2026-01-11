# Data Model: Multi-Agent Collaboration

**Feature**: 007-multi-agent-collaboration
**Date**: 2025-01-11

## Overview

定義多代理協作系統所需的資料結構，包含任務、結果、狀態等核心實體。

---

## Core Entities

### 1. AgentType (Enum)

**描述**: Agent 類型識別碼

```python
class AgentType(str, Enum):
    """Agent 類型"""
    WEATHER = "weather"
    FINANCE = "finance"
    TRAVEL = "travel"
    GENERAL = "general"
```

**用途**: 用於 Supervisor 分派任務時識別目標 Agent

---

### 2. AgentTask

**描述**: Supervisor 分派給專家 Agent 的單一任務

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `task_id` | str | ✅ | 任務唯一識別碼（UUID） |
| `agent_type` | AgentType | ✅ | 目標 Agent 類型 |
| `description` | str | ✅ | 任務描述（自然語言） |
| `parameters` | dict | ❌ | 任務參數（如城市名、股票代碼） |
| `created_at` | datetime | ✅ | 建立時間 |

**驗證規則**:
- `task_id` 自動產生 UUID
- `description` 不可為空字串
- `parameters` 預設為空字典

**Pydantic Model**:
```python
class AgentTask(BaseModel):
    """Agent 任務"""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_type: AgentType
    description: str = Field(min_length=1)
    parameters: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
```

---

### 3. AgentResult

**描述**: 專家 Agent 的執行結果

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `task_id` | str | ✅ | 對應的任務識別碼 |
| `agent_type` | AgentType | ✅ | 執行的 Agent 類型 |
| `success` | bool | ✅ | 執行是否成功 |
| `data` | dict | ❌ | 成功時的結果資料 |
| `error` | str | ❌ | 失敗時的錯誤訊息 |
| `execution_time` | float | ✅ | 執行耗時（秒） |

**驗證規則**:
- `success=True` 時 `data` 必須有值
- `success=False` 時 `error` 必須有值
- `execution_time` 必須 >= 0

**Pydantic Model**:
```python
class AgentResult(BaseModel):
    """Agent 執行結果"""
    task_id: str
    agent_type: AgentType
    success: bool
    data: dict | None = None
    error: str | None = None
    execution_time: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_result(self) -> "AgentResult":
        if self.success and self.data is None:
            raise ValueError("成功結果必須包含 data")
        if not self.success and self.error is None:
            raise ValueError("失敗結果必須包含 error")
        return self
```

---

### 4. TaskDecomposition

**描述**: Supervisor 的任務拆解結果

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `tasks` | list[AgentTask] | ✅ | 拆解出的任務清單 |
| `reasoning` | str | ✅ | 拆解理由（debug 用） |
| `requires_aggregation` | bool | ✅ | 是否需要彙整多個結果 |

**驗證規則**:
- `tasks` 至少包含一個任務
- 若 `tasks` 長度 > 1，則 `requires_aggregation` 應為 True

**Pydantic Model**:
```python
class TaskDecomposition(BaseModel):
    """任務拆解結果"""
    tasks: list[AgentTask] = Field(min_length=1)
    reasoning: str
    requires_aggregation: bool = False

    @model_validator(mode="after")
    def validate_aggregation(self) -> "TaskDecomposition":
        if len(self.tasks) > 1:
            self.requires_aggregation = True
        return self
```

---

### 5. MultiAgentState

**描述**: 多代理流程的完整狀態（LangGraph TypedDict）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `user_input` | str | 使用者原始輸入 |
| `decomposition` | TaskDecomposition | 任務拆解結果 |
| `pending_tasks` | list[AgentTask] | 待執行的任務 |
| `results` | list[AgentResult] | 已完成的結果 |
| `final_response` | str | 最終回應 |
| `error` | str | 流程錯誤訊息 |

**State Reducers**:
- `results` 使用 append reducer（累加新結果）

**TypedDict Definition**:
```python
class MultiAgentState(TypedDict, total=False):
    """多代理流程狀態"""
    # 輸入
    user_input: str

    # Supervisor 輸出
    decomposition: TaskDecomposition | None

    # 執行追蹤
    pending_tasks: list[AgentTask]
    results: Annotated[list[AgentResult], operator.add]  # append reducer

    # 輸出
    final_response: str
    error: str | None
```

---

## Entity Relationships

```
User Input
    │
    ▼
┌─────────────────────┐
│  TaskDecomposition  │
│  (Supervisor 產出)   │
└──────────┬──────────┘
           │ 1:N
           ▼
┌─────────────────────┐
│     AgentTask       │──────┐
│  (單一任務)          │      │ 1:1
└──────────┬──────────┘      │
           │                  ▼
           │         ┌─────────────────────┐
           └────────▶│    AgentResult      │
                     │  (任務執行結果)      │
                     └─────────────────────┘
                              │ N:1
                              ▼
                     ┌─────────────────────┐
                     │  MultiAgentState    │
                     │  (流程狀態彙整)      │
                     └─────────────────────┘
```

---

## State Transitions

```
INIT ──▶ DECOMPOSED ──▶ EXECUTING ──▶ AGGREGATING ──▶ COMPLETED
  │          │              │              │              │
  │          │              │              │              ▼
  │          │              │              │         final_response
  │          │              │              ▼
  │          │              │         results[]
  │          │              ▼
  │          │         pending_tasks[]
  │          ▼
  │     decomposition
  ▼
user_input
```

---

## Integration with Existing Models

### 與現有 FlowState 的關係

```python
# flows/state.py (現有)
class FlowState(TypedDict, total=False):
    user_input: str
    intent: IntentType
    ...

# agents/state.py (新增)
class MultiAgentState(TypedDict, total=False):
    user_input: str  # 共用輸入
    ...
```

**整合策略**: MultiAgentState 為獨立的狀態定義，不繼承 FlowState。兩者透過 `user_input` 共用入口。

### 與現有 ToolResult 的關係

```python
# tools/schemas.py (現有)
class ToolResult(BaseModel):
    success: bool
    data: dict | None
    error: str | None

# agents/state.py (新增)
class AgentResult(BaseModel):
    task_id: str  # 額外：任務追蹤
    agent_type: AgentType  # 額外：Agent 識別
    success: bool  # 相同
    data: dict | None  # 相同
    error: str | None  # 相同
    execution_time: float  # 額外：效能追蹤
```

**整合策略**: AgentResult 擴充 ToolResult 概念，增加任務追蹤與效能監控欄位。Agent 內部可將 ToolResult 轉換為 AgentResult。
