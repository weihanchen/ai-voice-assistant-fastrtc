"""Multi-Agent Graph.

使用 LangGraph 實作多代理協作流程圖。
"""

from __future__ import annotations

import asyncio
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.finance import FinanceAgent
from voice_assistant.agents.general import GeneralAgent
from voice_assistant.agents.state import (
    AgentResult,
    AgentTask,
    AgentType,
    MultiAgentState,
)
from voice_assistant.agents.supervisor import SupervisorAgent
from voice_assistant.agents.travel import TravelAgent
from voice_assistant.agents.weather import WeatherAgent
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools.registry import ToolRegistry


def create_multi_agent_graph(
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
) -> CompiledStateGraph:
    """建立多代理協作流程圖。

    Args:
        llm_client: LLM 客戶端
        tool_registry: Tool 註冊表

    Returns:
        CompiledStateGraph: 編譯後的 LangGraph 流程圖

    Flow:
        START → supervisor_decompose → [parallel agents] → aggregate → END
    """
    # 建立 Supervisor 和 Expert Agents
    supervisor = SupervisorAgent(llm_client)
    agents: dict[AgentType, BaseAgent] = {
        AgentType.WEATHER: WeatherAgent(tool_registry),
        AgentType.FINANCE: FinanceAgent(tool_registry),
        AgentType.TRAVEL: TravelAgent(tool_registry, llm_client),
        AgentType.GENERAL: GeneralAgent(llm_client),
    }

    # 定義節點函式
    async def supervisor_decompose(state: MultiAgentState) -> dict[str, Any]:
        """Supervisor 任務拆解節點。"""
        user_input = state.get("user_input", "")
        decomposition = await supervisor.decompose(user_input)
        return {
            "decomposition": decomposition,
            "pending_tasks": decomposition.tasks,
        }

    async def execute_agent(state: MultiAgentState) -> dict[str, Any]:
        """執行單一 Agent 任務節點。"""
        # 從 state 取得當前任務（由 Send 傳入）
        task: AgentTask = state.get("current_task")  # type: ignore
        if not task:
            return {"results": []}

        agent = agents.get(task.agent_type)
        if not agent:
            result = AgentResult(
                task_id=task.task_id,
                agent_type=task.agent_type,
                success=False,
                error=f"找不到對應的 Agent: {task.agent_type}",
                execution_time=0.0,
            )
            return {"results": [result]}

        # 執行 Agent（帶逾時）
        try:
            result = await asyncio.wait_for(
                agent.execute(task),
                timeout=agent.timeout,
            )
        except TimeoutError:
            result = AgentResult(
                task_id=task.task_id,
                agent_type=task.agent_type,
                success=False,
                error=f"{task.agent_type.value} 執行逾時（超過 {agent.timeout} 秒）",
                execution_time=agent.timeout,
            )

        return {"results": [result]}

    async def aggregate_results(state: MultiAgentState) -> dict[str, Any]:
        """結果彙整節點。"""
        user_input = state.get("user_input", "")
        results = state.get("results", [])

        # 如果只有一個結果且成功，直接回傳
        if len(results) == 1 and results[0].success:
            data = results[0].data or {}
            # 如果是 general agent，直接取 response
            if results[0].agent_type == AgentType.GENERAL:
                final_response = data.get("response", "")
            # 如果是 travel agent，取 recommendations
            elif results[0].agent_type == AgentType.TRAVEL:
                final_response = data.get("recommendations", "")
            else:
                # 其他情況由 supervisor 彙整
                final_response = await supervisor.aggregate(user_input, results)
        else:
            # 多個結果或有失敗，由 supervisor 彙整
            final_response = await supervisor.aggregate(user_input, results)

        return {"final_response": final_response}

    def route_to_agents(state: MultiAgentState) -> list[Send]:
        """路由函式：將任務分派給對應的 Agent。"""
        pending_tasks = state.get("pending_tasks", [])
        sends = []
        for task in pending_tasks:
            # 使用 Send 實現並行執行
            sends.append(
                Send(
                    "execute_agent",
                    {**state, "current_task": task},
                )
            )
        return sends

    # 建構流程圖
    graph = StateGraph(MultiAgentState)

    # 新增節點
    graph.add_node("supervisor_decompose", supervisor_decompose)
    graph.add_node("execute_agent", execute_agent)
    graph.add_node("aggregate", aggregate_results)

    # 定義邊
    graph.add_edge(START, "supervisor_decompose")
    graph.add_conditional_edges(
        "supervisor_decompose",
        route_to_agents,
        ["execute_agent"],
    )
    graph.add_edge("execute_agent", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()
