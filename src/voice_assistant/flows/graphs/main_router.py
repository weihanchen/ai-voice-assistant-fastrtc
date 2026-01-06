"""主路由流程圖。

定義主對話流程的意圖分類與路由邏輯。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from langgraph.graph import END, StateGraph

from voice_assistant.flows.graphs.travel_planner import create_travel_planner_graph
from voice_assistant.flows.nodes.classifier import create_classifier_node
from voice_assistant.flows.nodes.response_generator import (
    create_response_generator_node,
)
from voice_assistant.flows.nodes.tool_executor import create_tool_executor_node
from voice_assistant.flows.state import FlowState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from voice_assistant.llm.client import LLMClient
    from voice_assistant.tools.registry import ToolRegistry


def route_by_intent(
    state: FlowState,
) -> Literal["tool_executor", "travel_subgraph", "response_generator"]:
    """根據意圖分類結果決定下一個節點。

    Args:
        state: 流程狀態

    Returns:
        下一個節點名稱
    """
    # 如果有錯誤，直接產生回應
    if state.get("error"):
        return "response_generator"

    intent = state.get("intent")

    # 旅遊意圖走子流程
    if intent == "travel":
        return "travel_subgraph"

    # 其他意圖（weather, exchange, stock）走工具執行
    return "tool_executor"


def create_main_router_graph(
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
) -> CompiledStateGraph:
    """建立主路由流程圖。

    Args:
        llm_client: LLM 客戶端
        tool_registry: Tool 註冊表

    Returns:
        編譯後的 StateGraph
    """
    # 建立 StateGraph
    builder = StateGraph(FlowState)

    # 建立節點函式
    classify_intent = create_classifier_node(llm_client)
    execute_tool = create_tool_executor_node(tool_registry)
    generate_response = create_response_generator_node(llm_client)

    # 建立旅遊子流程
    travel_subgraph = create_travel_planner_graph(llm_client, tool_registry)

    # 新增節點
    builder.add_node("classifier", classify_intent)
    builder.add_node("tool_executor", execute_tool)
    builder.add_node("travel_subgraph", travel_subgraph)
    builder.add_node("response_generator", generate_response)

    # 設定起始邊
    builder.set_entry_point("classifier")

    # 設定條件邊：意圖路由
    builder.add_conditional_edges(
        "classifier",
        route_by_intent,
        {
            "tool_executor": "tool_executor",
            "travel_subgraph": "travel_subgraph",
            "response_generator": "response_generator",
        },
    )

    # 設定邊
    builder.add_edge("tool_executor", "response_generator")
    builder.add_edge("travel_subgraph", "response_generator")
    builder.add_edge("response_generator", END)

    # 編譯並回傳
    return builder.compile()
