"""美食推薦流程圖定義。

定義美食推薦流程的 LangGraph StateGraph。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from voice_assistant.flows.state import FlowState

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient
    from voice_assistant.tools.registry import ToolRegistry

# 匯入節點工廠函式
from voice_assistant.flows.nodes.food import (
    create_extract_city_node,
    create_generate_recommendation_node,
    create_query_weather_node,
    decide_venue_type,
)


def create_food_recommend_graph(
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
) -> CompiledStateGraph:
    """建立美食推薦流程圖。

    Args:
        llm_client: LLM 客戶端實例。
        tool_registry: 工具註冊表實例。

    Returns:
        編譯後的 StateGraph。
    """
    builder = StateGraph(FlowState)

    # 建立節點
    extract_city_fn = create_extract_city_node(llm_client)
    query_weather_fn = create_query_weather_node(tool_registry)
    generate_recommendation_fn = create_generate_recommendation_node(llm_client)

    # 新增節點
    builder.add_node("extract_city", extract_city_fn)
    builder.add_node("query_weather", query_weather_fn)
    builder.add_node("decide_venue_type", decide_venue_type)
    builder.add_node("generate_recommendation", generate_recommendation_fn)

    # 設定入口點
    builder.set_entry_point("extract_city")

    # 新增邊（線性流程）
    builder.add_edge("extract_city", "query_weather")
    builder.add_edge("query_weather", "decide_venue_type")
    builder.add_edge("decide_venue_type", "generate_recommendation")
    builder.add_edge("generate_recommendation", END)

    return builder.compile()
