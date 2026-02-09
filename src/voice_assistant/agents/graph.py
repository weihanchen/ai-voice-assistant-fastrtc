"""Multi-Agent Graph.

使用 LangGraph 實作多代理協作流程圖。
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
import pkgutil
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.state import (
    AgentResult,
    AgentTask,
    AgentType,
    MultiAgentState,
)
from voice_assistant.agents.supervisor import SupervisorAgent
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def discover_agents(
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
    package_name: str = "voice_assistant.agents",
) -> dict[AgentType, BaseAgent]:
    """自動掃描指定套件下的 BaseAgent 子類別並實例化。

    根據各 Agent 建構式的參數簽章，自動注入 llm_client 和/或 tool_registry。
    過濾掉 BaseAgent 本身和 SupervisorAgent（由 graph 內部管理）。

    Args:
        llm_client: LLM 客戶端，用於需要 LLM 的 Agent
        tool_registry: 工具註冊表，用於需要工具的 Agent
        package_name: 要掃描的套件名稱

    Returns:
        dict[AgentType, BaseAgent]: Agent 類型到實例的映射
    """
    agents: dict[AgentType, BaseAgent] = {}

    try:
        package = importlib.import_module(package_name)
    except ImportError:
        logger.warning("無法匯入套件: %s", package_name)
        return agents

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return agents

    for _importer, module_name, _is_pkg in pkgutil.iter_modules(package_path):
        full_module_name = f"{package_name}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
        except Exception as e:
            logger.warning("匯入模組 %s 失敗: %s", full_module_name, e)
            continue

        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseAgent)
                and obj is not BaseAgent
                and not inspect.isabstract(obj)
                and obj.__name__ != "SupervisorAgent"
            ):
                try:
                    # 檢查建構式參數以決定注入方式
                    sig = inspect.signature(obj.__init__)
                    params = list(sig.parameters.keys())
                    kwargs: dict[str, Any] = {}
                    if "tool_registry" in params:
                        kwargs["tool_registry"] = tool_registry
                    if "llm_client" in params:
                        kwargs["llm_client"] = llm_client

                    instance = obj(**kwargs)
                    agents[instance.agent_type] = instance
                    logger.info("自動發現 Agent: %s", instance.agent_type.value)
                except Exception as e:
                    logger.warning("實例化 Agent %s 失敗: %s", obj.__name__, e)

    return agents


def create_multi_agent_graph(
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
    agents: dict[AgentType, BaseAgent] | None = None,
) -> CompiledStateGraph:
    """建立多代理協作流程圖。

    Args:
        llm_client: LLM 客戶端
        tool_registry: Tool 註冊表
        agents: Agent 映射（可選，預設使用 discover_agents 自動發現）

    Returns:
        CompiledStateGraph: 編譯後的 LangGraph 流程圖

    Flow:
        START → supervisor_decompose → [parallel agents] → aggregate → END
    """
    # 建立 Supervisor 和 Expert Agents
    supervisor = SupervisorAgent(llm_client)
    if agents is None:
        agents = discover_agents(llm_client, tool_registry)

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
