"""Multi-Agent Collaboration Module.

此模組實作多代理協作系統，包含 Supervisor Agent 與多個專家 Agent。

主要元件：
- SupervisorAgent: 負責任務拆解與結果彙整
- WeatherAgent: 天氣查詢專家
- FinanceAgent: 財務查詢專家（匯率、股價）
- TravelAgent: 旅遊規劃專家
- GeneralAgent: 通用對話處理

使用範例：
    from voice_assistant.agents import MultiAgentExecutor
    from voice_assistant.llm.client import LLMClient
    from voice_assistant.tools.registry import ToolRegistry

    executor = MultiAgentExecutor(llm_client, tool_registry)
    response = await executor.execute("查台積電股價和美金匯率")
"""

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.executor import MultiAgentExecutor
from voice_assistant.agents.finance import FinanceAgent
from voice_assistant.agents.general import GeneralAgent
from voice_assistant.agents.graph import create_multi_agent_graph
from voice_assistant.agents.state import (
    AgentResult,
    AgentTask,
    AgentType,
    MultiAgentState,
    TaskDecomposition,
)
from voice_assistant.agents.supervisor import SupervisorAgent
from voice_assistant.agents.travel import TravelAgent
from voice_assistant.agents.weather import WeatherAgent

__all__ = [
    # State & Models
    "AgentType",
    "AgentTask",
    "AgentResult",
    "TaskDecomposition",
    "MultiAgentState",
    # Base
    "BaseAgent",
    # Agents
    "SupervisorAgent",
    "WeatherAgent",
    "FinanceAgent",
    "TravelAgent",
    "GeneralAgent",
    # Graph & Executor
    "create_multi_agent_graph",
    "MultiAgentExecutor",
]
