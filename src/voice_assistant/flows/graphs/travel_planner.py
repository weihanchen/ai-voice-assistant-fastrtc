"""旅遊規劃子流程圖。

定義旅遊規劃的多步驟流程：
解析目的地 → 查詢天氣 → 評估天氣 → 產生建議
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from langgraph.graph import END, StateGraph

from voice_assistant.flows.nodes.travel.destination import (
    create_destination_parser_node,
)
from voice_assistant.flows.nodes.travel.evaluator import evaluate_weather
from voice_assistant.flows.nodes.travel.recommender import (
    recommend_indoor,
    recommend_outdoor,
)
from voice_assistant.flows.nodes.travel.weather import create_weather_query_node
from voice_assistant.flows.state import FlowState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from voice_assistant.llm.client import LLMClient
    from voice_assistant.tools.registry import ToolRegistry


def route_by_destination_valid(
    state: FlowState,
) -> Literal["query_weather", "handle_invalid_destination"]:
    """根據目的地驗證結果決定下一個節點。

    Args:
        state: 流程狀態

    Returns:
        下一個節點名稱
    """
    travel_state = state.get("travel_state", {})
    destination_valid = travel_state.get("destination_valid", False)

    if destination_valid:
        return "query_weather"
    return "handle_invalid_destination"


def route_by_weather(
    state: FlowState,
) -> Literal["recommend_outdoor", "recommend_indoor"]:
    """根據天氣評估結果決定建議類型。

    Args:
        state: 流程狀態

    Returns:
        下一個節點名稱
    """
    travel_state = state.get("travel_state", {})
    weather_suitable = travel_state.get("weather_suitable", False)

    if weather_suitable:
        return "recommend_outdoor"
    return "recommend_indoor"


async def handle_invalid_destination(state: FlowState) -> dict:
    """處理無效目的地的節點。

    Args:
        state: 流程狀態

    Returns:
        更新的狀態欄位
    """
    travel_state = state.get("travel_state", {})
    destination = travel_state.get("destination")

    if destination:
        error_msg = (
            f"抱歉，目前僅支援台灣城市的旅遊規劃，「{destination}」不在支援範圍內"
        )
    else:
        error_msg = "請問您想去哪個城市旅遊呢？目前支援台灣主要城市"

    return {"error": error_msg}


def create_travel_planner_graph(
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
) -> CompiledStateGraph:
    """建立旅遊規劃子流程圖。

    Args:
        llm_client: LLM 客戶端
        tool_registry: Tool 註冊表

    Returns:
        編譯後的 StateGraph
    """
    # 建立 StateGraph
    builder = StateGraph(FlowState)

    # 建立節點函式
    parse_destination = create_destination_parser_node(llm_client)
    query_weather = create_weather_query_node(tool_registry)

    # 新增節點
    builder.add_node("parse_destination", parse_destination)
    builder.add_node("query_weather", query_weather)
    builder.add_node("evaluate_weather", evaluate_weather)
    builder.add_node("recommend_outdoor", recommend_outdoor)
    builder.add_node("recommend_indoor", recommend_indoor)
    builder.add_node("handle_invalid_destination", handle_invalid_destination)

    # 設定起始邊
    builder.set_entry_point("parse_destination")

    # 設定條件邊：目的地驗證
    builder.add_conditional_edges(
        "parse_destination",
        route_by_destination_valid,
        {
            "query_weather": "query_weather",
            "handle_invalid_destination": "handle_invalid_destination",
        },
    )

    # 設定邊：天氣查詢 → 天氣評估
    builder.add_edge("query_weather", "evaluate_weather")

    # 設定條件邊：天氣評估
    builder.add_conditional_edges(
        "evaluate_weather",
        route_by_weather,
        {
            "recommend_outdoor": "recommend_outdoor",
            "recommend_indoor": "recommend_indoor",
        },
    )

    # 設定結束邊
    builder.add_edge("recommend_outdoor", END)
    builder.add_edge("recommend_indoor", END)
    builder.add_edge("handle_invalid_destination", END)

    # 編譯並回傳
    return builder.compile()
