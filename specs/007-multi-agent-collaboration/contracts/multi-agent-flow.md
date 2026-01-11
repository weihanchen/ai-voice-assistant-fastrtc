# Contract: Multi-Agent Flow Interface

**Feature**: 007-multi-agent-collaboration
**Date**: 2025-01-11

## Overview

定義多代理協作流程的介面契約，包含 BaseAgent、Supervisor、各專家 Agent 及流程圖的 API 規格。

---

## 1. BaseAgent Interface

### 抽象基底類別

```python
from abc import ABC, abstractmethod
from voice_assistant.agents.state import AgentTask, AgentResult, AgentType

class BaseAgent(ABC):
    """Agent 抽象基底類別

    所有專家 Agent 必須繼承此類別並實作 execute 方法。
    """

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """回傳 Agent 類型識別碼

        Returns:
            AgentType: Agent 類型（WEATHER/FINANCE/TRAVEL/GENERAL）
        """
        ...

    @property
    def timeout(self) -> float:
        """執行逾時秒數（可覆寫）

        Returns:
            float: 預設 10.0 秒
        """
        return 10.0

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """執行任務

        Args:
            task: 待執行的任務

        Returns:
            AgentResult: 執行結果

        Raises:
            不應拋出例外，錯誤應包裝在 AgentResult.error 中
        """
        ...
```

### 使用範例

```python
class WeatherAgent(BaseAgent):
    @property
    def agent_type(self) -> AgentType:
        return AgentType.WEATHER

    async def execute(self, task: AgentTask) -> AgentResult:
        # 實作天氣查詢邏輯
        ...
```

---

## 2. SupervisorAgent Interface

### 類別定義

```python
class SupervisorAgent:
    """Supervisor Agent - 負責任務拆解與分派

    Args:
        llm_client: LLM 客戶端（用於意圖識別與任務拆解）
    """

    def __init__(self, llm_client: LLMClient) -> None:
        ...

    async def decompose(self, user_input: str) -> TaskDecomposition:
        """將使用者輸入拆解為多個 Agent 任務

        Args:
            user_input: 使用者原始輸入

        Returns:
            TaskDecomposition: 包含任務清單與拆解理由

        Example:
            >>> supervisor = SupervisorAgent(llm_client)
            >>> result = await supervisor.decompose("查台積電股價和美金匯率")
            >>> len(result.tasks)
            2
            >>> result.tasks[0].agent_type
            AgentType.FINANCE
        """
        ...

    async def aggregate(
        self,
        user_input: str,
        results: list[AgentResult]
    ) -> str:
        """彙整多個 Agent 結果為自然語言回應

        Args:
            user_input: 原始使用者輸入（用於上下文）
            results: Agent 執行結果清單

        Returns:
            str: 自然語言回應

        Example:
            >>> response = await supervisor.aggregate(
            ...     "查股價和匯率",
            ...     [stock_result, exchange_result]
            ... )
            >>> print(response)
            "台積電目前股價 580 元，美金兌台幣匯率為 31.5"
        """
        ...
```

---

## 3. Expert Agent Interfaces

### 3.1 WeatherAgent

```python
class WeatherAgent(BaseAgent):
    """天氣查詢 Agent

    Args:
        tool_registry: Tool 註冊表（用於取得 WeatherTool）
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        ...

    @property
    def agent_type(self) -> AgentType:
        return AgentType.WEATHER

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行天氣查詢

        支援的 task.parameters:
            - city: str - 城市名稱（必填）

        Returns:
            AgentResult with data:
                - city: str
                - temperature: float
                - weather: str
                - humidity: float
        """
        ...
```

### 3.2 FinanceAgent

```python
class FinanceAgent(BaseAgent):
    """財務查詢 Agent（匯率+股價）

    Args:
        tool_registry: Tool 註冊表
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        ...

    @property
    def agent_type(self) -> AgentType:
        return AgentType.FINANCE

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行財務查詢

        支援的 task.parameters:
            匯率查詢:
                - query_type: "exchange"
                - from_currency: str
                - to_currency: str
                - amount: float (optional)
            股價查詢:
                - query_type: "stock"
                - symbol: str

        Returns:
            AgentResult with data (匯率):
                - from_currency: str
                - to_currency: str
                - rate: float
                - amount: float (if provided)
                - converted: float (if amount provided)
            AgentResult with data (股價):
                - symbol: str
                - price: float
                - change: float
                - change_percent: float
        """
        ...
```

### 3.3 TravelAgent

```python
class TravelAgent(BaseAgent):
    """旅遊規劃 Agent

    Args:
        tool_registry: Tool 註冊表
        llm_client: LLM 客戶端（用於生成建議）
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        llm_client: LLMClient
    ) -> None:
        ...

    @property
    def agent_type(self) -> AgentType:
        return AgentType.TRAVEL

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行旅遊規劃

        支援的 task.parameters:
            - destination: str - 目的地城市（必填）
            - date: str (optional) - 出遊日期

        Returns:
            AgentResult with data:
                - destination: str
                - weather: dict (天氣資訊)
                - recommendations: list[str] (景點推薦)
                - weather_suitable: bool
        """
        ...
```

### 3.4 GeneralAgent

```python
class GeneralAgent(BaseAgent):
    """通用 Agent（閒聊/Fallback）

    Args:
        llm_client: LLM 客戶端
    """

    def __init__(self, llm_client: LLMClient) -> None:
        ...

    @property
    def agent_type(self) -> AgentType:
        return AgentType.GENERAL

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行通用對話

        支援的 task.parameters:
            - message: str - 對話內容（必填）

        Returns:
            AgentResult with data:
                - response: str
        """
        ...
```

---

## 4. Multi-Agent Graph Interface

### 建立函式

```python
def create_multi_agent_graph(
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
) -> CompiledStateGraph:
    """建立多代理協作流程圖

    Args:
        llm_client: LLM 客戶端
        tool_registry: Tool 註冊表

    Returns:
        CompiledStateGraph: 編譯後的 LangGraph 流程圖

    Flow:
        START → supervisor_decompose → [parallel agents] → aggregate → END

    Example:
        >>> graph = create_multi_agent_graph(llm_client, tool_registry)
        >>> result = await graph.ainvoke({
        ...     "user_input": "查台積電股價和美金匯率"
        ... })
        >>> print(result["final_response"])
    """
    ...
```

### 流程圖結構

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Agent Graph                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [START]                                                    │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────┐                                   │
│  │ supervisor_decompose │  ← 任務拆解                       │
│  └──────────┬──────────┘                                   │
│             │                                               │
│             ▼ (conditional: route_to_agents)               │
│  ┌──────────────────────────────────────────────┐          │
│  │           Send() to multiple agents           │          │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │          │
│  │  │ Weather │ │ Finance │ │ Travel  │ ...    │          │
│  │  │  Agent  │ │  Agent  │ │  Agent  │        │          │
│  │  └────┬────┘ └────┬────┘ └────┬────┘        │          │
│  │       │           │           │              │          │
│  │       └───────────┴───────────┘              │          │
│  └──────────────────┬───────────────────────────┘          │
│                     │                                       │
│                     ▼                                       │
│  ┌─────────────────────┐                                   │
│  │     aggregate       │  ← 結果彙整                       │
│  └──────────┬──────────┘                                   │
│             │                                               │
│             ▼                                               │
│          [END]                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. MultiAgentExecutor Interface

### 類別定義

```python
class MultiAgentExecutor:
    """多代理流程執行器

    整合 Multi-Agent Graph，提供統一的執行介面。

    Args:
        llm_client: LLM 客戶端
        tool_registry: Tool 註冊表
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
    ) -> None:
        ...

    async def execute(self, user_input: str) -> str:
        """執行多代理流程

        Args:
            user_input: 使用者輸入

        Returns:
            str: 自然語言回應

        Example:
            >>> executor = MultiAgentExecutor(llm_client, tool_registry)
            >>> response = await executor.execute("查台積電股價和美金匯率")
            >>> print(response)
        """
        ...
```

---

## 6. Configuration Interface

### FlowMode Enum

```python
from enum import Enum

class FlowMode(str, Enum):
    """流程模式"""
    TOOLS = "tools"           # 純 Tool 呼叫
    LANGGRAPH = "langgraph"   # LangGraph 流程 (006)
    MULTI_AGENT = "multi_agent"  # 多代理協作 (007)
```

### Config Updates

```python
# config.py 新增
FLOW_MODE: FlowMode = FlowMode(os.getenv("FLOW_MODE", "multi_agent"))
```

---

## 7. Error Handling Contract

### 錯誤回傳格式

所有 Agent 的錯誤必須包裝在 AgentResult 中，不應拋出例外：

```python
# ✅ 正確
return AgentResult(
    task_id=task.task_id,
    agent_type=self.agent_type,
    success=False,
    error="無法查詢到台北天氣資訊",
    execution_time=elapsed
)

# ❌ 錯誤 - 不應拋出例外
raise WeatherAPIError("API 連線失敗")
```

### 逾時處理

```python
# 由 BaseAgent 或流程層統一處理逾時
try:
    result = await asyncio.wait_for(
        agent.execute(task),
        timeout=agent.timeout
    )
except asyncio.TimeoutError:
    result = AgentResult(
        task_id=task.task_id,
        agent_type=agent.agent_type,
        success=False,
        error=f"{agent.agent_type} 執行逾時（超過 {agent.timeout} 秒）",
        execution_time=agent.timeout
    )
```
