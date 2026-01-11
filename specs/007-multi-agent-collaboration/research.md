# Research: Multi-Agent Collaboration

**Feature**: 007-multi-agent-collaboration
**Date**: 2025-01-11

## Research Topics

### 1. LangGraph Multi-Agent Pattern

**Decision**: 採用 LangGraph Supervisor Pattern 實作多代理協作

**Rationale**:
- LangGraph 已是專案現有的流程編排框架（006 已使用）
- Supervisor Pattern 符合需求：中央協調者分派任務給專家 Agent
- 支援 StateGraph 並行節點執行（Send API）
- 與現有 FlowState 架構相容

**Alternatives Considered**:
| 方案 | 優點 | 缺點 | 結論 |
|------|------|------|------|
| LangGraph Supervisor | 中央協調、易於追蹤、符合現有架構 | 單點協調 | ✅ 採用 |
| LangGraph Hierarchical | 多層結構、可擴展 | 過於複雜、不符 MVP | ❌ 不採用 |
| AutoGen/CrewAI | 成熟的多代理框架 | 引入新依賴、學習曲線 | ❌ 不採用 |
| 自定義 asyncio | 最大彈性 | 重造輪子、維護成本 | ❌ 不採用 |

**Implementation Approach**:
```
Supervisor Agent
    │
    ├── 解析使用者意圖
    ├── 拆解為多個 AgentTask
    ├── 使用 LangGraph Send() 分派給專家 Agent
    └── 彙整所有 AgentResult 產生回應
```

---

### 2. 並行執行機制

**Decision**: 使用 LangGraph 的 `Send()` API 實現並行分派

**Rationale**:
- LangGraph 2.0 提供 `Send()` 機制，可動態分派多個並行任務
- 無需自行管理 asyncio.gather()，由框架統一處理
- 支援部分失敗處理（Partial Results）

**Pattern**:
```python
def supervisor_route(state: MultiAgentState) -> list[Send]:
    """Supervisor 決定分派哪些 Agent"""
    tasks = state["tasks"]
    return [
        Send(task.agent_type, {"task": task})
        for task in tasks
    ]
```

**Alternatives Considered**:
| 方案 | 優點 | 缺點 | 結論 |
|------|------|------|------|
| LangGraph Send() | 框架原生、統一管理 | 需 LangGraph 2.0+ | ✅ 採用 |
| asyncio.gather() | 熟悉、直接 | 需自行處理錯誤聚合 | ❌ 不採用 |
| Sequential | 簡單 | 無法並行、不符需求 | ❌ 不採用 |

---

### 3. Agent 設計模式

**Decision**: 採用統一的 BaseAgent 抽象類別，各專家 Agent 繼承實作

**Rationale**:
- 統一介面便於擴展新 Agent
- 符合 Constitution V. Extensible Design 原則
- 可在 BaseAgent 統一處理逾時、錯誤處理

**Agent Interface**:
```python
class BaseAgent(ABC):
    """Agent 基底類別"""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Agent 類型識別碼"""
        ...

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """執行任務"""
        ...
```

**Agent Types**:
| Agent | 職責 | 使用的 Tool |
|-------|------|-------------|
| WeatherAgent | 天氣查詢 | WeatherTool |
| FinanceAgent | 匯率、股價查詢 | ExchangeRateTool, StockPriceTool |
| TravelAgent | 旅遊規劃建議 | WeatherTool + 內建景點推薦 |
| GeneralAgent | 閒聊、fallback | 無（直接 LLM 回應） |

---

### 4. Supervisor 任務拆解策略

**Decision**: 使用 LLM Function Calling 進行意圖識別與任務拆解

**Rationale**:
- 符合 Constitution II. LLM Auto-Routing 原則
- 複雜請求（如「查股價和匯率」）需要 LLM 理解語意
- Function Calling 可結構化輸出任務清單

**Task Decomposition Schema**:
```python
class TaskDecomposition(BaseModel):
    """Supervisor 的任務拆解結果"""
    tasks: list[AgentTask]
    reasoning: str  # 拆解理由（用於 debug）
```

**LLM Prompt 策略**:
- System Prompt 說明可用的 Agent 類型與能力
- 使用 JSON Schema 定義輸出格式
- 範例：「查台積電股價和美金匯率」→ 拆解為 2 個 FinanceAgent 任務

---

### 5. 結果彙整策略

**Decision**: 使用 LLM 將多個 AgentResult 彙整為自然語言回應

**Rationale**:
- 符合 Constitution III. Human-Friendly Response 原則
- 多個結果需要語意整合，非簡單字串拼接
- LLM 可根據結果內容調整回應語氣

**Aggregation Flow**:
```
AgentResult[] → Aggregator Node → LLM 整合 → 自然語言回應
```

**處理部分失敗**:
- 成功的結果正常呈現
- 失敗的結果說明原因（「無法查詢到 XX 資訊」）
- 全部失敗時提供友善錯誤訊息

---

### 6. FLOW_MODE 切換機制

**Decision**: 透過環境變數 `FLOW_MODE` 在啟動時決定使用的流程

**Rationale**:
- 符合 Constitution V. 配置與程式碼分離
- 便於測試、Demo 切換不同模式
- 向後相容現有功能

**Mode Options**:
| Mode | 說明 | 使用的 Executor |
|------|------|-----------------|
| `tools` | 純 Tool 呼叫（Phase 1-5 架構） | LLMClient.chat() |
| `langgraph` | LangGraph 流程（006 架構） | FlowExecutor.execute() |
| `multi_agent` | 多代理協作（007 架構） | MultiAgentExecutor.execute() |

**Implementation**:
```python
# config.py
from enum import Enum

class FlowMode(str, Enum):
    TOOLS = "tools"
    LANGGRAPH = "langgraph"
    MULTI_AGENT = "multi_agent"

FLOW_MODE = FlowMode(os.getenv("FLOW_MODE", "multi_agent"))
```

---

### 7. 逾時與錯誤處理

**Decision**: 每個 Agent 執行設定 10 秒逾時，並採用 Partial Results 策略

**Rationale**:
- 避免單一 Agent 阻塞整體流程
- 部分成功仍可提供價值
- 符合 Constitution Quality Gates 延遲 < 5 秒

**Timeout Strategy**:
```python
async def execute_with_timeout(agent: BaseAgent, task: AgentTask) -> AgentResult:
    try:
        return await asyncio.wait_for(
            agent.execute(task),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        return AgentResult(
            success=False,
            error=f"{agent.agent_type} 執行逾時"
        )
```

---

## Summary

| 研究項目 | 決策 |
|----------|------|
| Multi-Agent Pattern | LangGraph Supervisor Pattern |
| 並行執行 | LangGraph Send() API |
| Agent 設計 | BaseAgent 抽象類別 + 4 種專家 Agent |
| 任務拆解 | LLM Function Calling |
| 結果彙整 | LLM 自然語言整合 |
| 模式切換 | FLOW_MODE 環境變數 |
| 逾時處理 | 10 秒逾時 + Partial Results |

所有研究項目已解決，無 NEEDS CLARIFICATION 項目。
