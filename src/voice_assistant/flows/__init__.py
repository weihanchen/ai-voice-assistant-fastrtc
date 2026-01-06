"""LangGraph 流程編排模組。

提供對話流程編排功能，包含意圖分類路由與多步驟旅遊規劃子流程。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from voice_assistant.flows.graphs.main_router import create_main_router_graph
from voice_assistant.flows.state import (
    CITY_RECOMMENDATIONS,
    FlowState,
    IntentType,
    RecommendationType,
    TravelPlanState,
    WeatherInfo,
    is_weather_suitable,
)
from voice_assistant.flows.visualization import get_mermaid_diagram

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient
    from voice_assistant.tools.registry import ToolRegistry


class FlowExecutor:
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

    async def execute(self, user_input: str) -> str:
        """執行對話流程。

        Args:
            user_input: 使用者輸入文字

        Returns:
            回應文字
        """
        # 初始狀態
        initial_state: FlowState = {
            "user_input": user_input,
        }

        # 執行流程
        result = await self._graph.ainvoke(initial_state)

        # 回傳回應
        return result.get("response", "抱歉，我無法處理您的請求")

    def get_visualization(self) -> str:
        """取得流程視覺化 Mermaid 圖。

        Returns:
            Mermaid 格式字串
        """
        return get_mermaid_diagram(self._graph)


__all__ = [
    "CITY_RECOMMENDATIONS",
    "FlowExecutor",
    "FlowState",
    "IntentType",
    "RecommendationType",
    "TravelPlanState",
    "WeatherInfo",
    "is_weather_suitable",
]
