"""LangGraph 流程編排模組。

提供對話流程編排功能，包含意圖分類路由與多步驟旅遊規劃子流程。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from voice_assistant.flows.base import BaseFlowExecutor, NodeChangeCallback
from voice_assistant.flows.exceptions import FlowNotFoundError
from voice_assistant.flows.graphs.main_router import create_main_router_graph
from voice_assistant.flows.registry import FlowRegistry
from voice_assistant.flows.state import (
    CITY_RECOMMENDATIONS,
    FlowState,
    IntentType,
    RecommendationType,
    TravelPlanState,
    WeatherInfo,
    is_weather_suitable,
)
from voice_assistant.flows.tool_calling_executor import ToolCallingExecutor
from voice_assistant.flows.visualization import (
    NodeStatus,
    apply_node_labels,
    get_mermaid_diagram,
)

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient
    from voice_assistant.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class FlowExecutor(BaseFlowExecutor):
    """LangGraph 流程執行器。

    提供對話流程的執行與視覺化功能。
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
    ) -> None:
        """初始化流程執行器。

        Args:
            llm_client: LLM 客戶端
            tool_registry: Tool 註冊表
        """
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self._graph = create_main_router_graph(llm_client, tool_registry)

    @property
    def flow_name(self) -> str:
        """流程名稱。"""
        return "langgraph"

    async def execute(
        self,
        user_input: str,
        on_node_change: NodeChangeCallback | None = None,
    ) -> str:
        """執行對話流程。

        使用 astream(stream_mode="updates") 逐步追蹤節點執行狀態，
        並透過 on_node_change callback 即時回報。

        Args:
            user_input: 使用者輸入文字
            on_node_change: 節點狀態變更回呼

        Returns:
            回應文字
        """
        # 初始狀態
        initial_state: FlowState = {
            "user_input": user_input,
        }

        result: dict = {}
        async for chunk in self._graph.astream(
            initial_state,
            stream_mode="updates",
        ):
            # chunk 格式: {node_name: node_output}
            for node_name in chunk:
                if on_node_change:
                    on_node_change(node_name, NodeStatus.RUNNING)
                logger.debug("[FlowExecutor] 節點執行中: %s", node_name)
                result.update(chunk[node_name])
                if on_node_change:
                    on_node_change(node_name, NodeStatus.COMPLETED)

        return result.get("response", "抱歉，我無法處理您的請求")

    # 節點 ID → 使用者友善中文標籤
    # 包含主路由與旅遊子流程的所有節點
    _NODE_LABELS: dict[str, str] = {
        "__start__": "開始",
        "classifier": "意圖分類",
        "tool_executor": "工具執行",
        "travel_subgraph": "旅遊規劃",
        "response_generator": "回應產生",
        "__end__": "結束",
        # 旅遊子流程節點
        "parse_destination": "解析目的地",
        "query_weather": "查詢天氣",
        "evaluate_weather": "評估天氣",
        "recommend_outdoor": "戶外推薦",
        "recommend_indoor": "室內推薦",
        "handle_invalid_destination": "無效目的地處理",
    }

    def get_visualization(self) -> str:
        """取得流程視覺化 Mermaid 圖。

        Returns:
            附有中文標籤的 Mermaid 格式字串
        """
        raw = get_mermaid_diagram(self._graph)
        return apply_node_labels(raw, self._NODE_LABELS)


__all__ = [
    "BaseFlowExecutor",
    "CITY_RECOMMENDATIONS",
    "FlowExecutor",
    "FlowNotFoundError",
    "FlowRegistry",
    "FlowState",
    "IntentType",
    "RecommendationType",
    "ToolCallingExecutor",
    "TravelPlanState",
    "WeatherInfo",
    "is_weather_suitable",
]
