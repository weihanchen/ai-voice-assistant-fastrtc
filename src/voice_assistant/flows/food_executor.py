"""美食推薦流程執行器。

提供美食推薦流程的完整執行介面。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from voice_assistant.flows.base import BaseFlowExecutor, NodeChangeCallback
from voice_assistant.flows.graphs.food import create_food_recommend_graph

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient
    from voice_assistant.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class FoodRecommendFlowExecutor(BaseFlowExecutor):
    """美食推薦流程執行器。

    繼承 BaseFlowExecutor，封裝美食推薦的 LangGraph StateGraph。
    """

    # 節點 ID → 顯示名稱 對照表（用於視覺化）
    _NODE_LABELS: dict[str, str] = {
        "extract_city": "提取城市名稱",
        "query_weather": "查詢天氣",
        "decide_venue_type": "決定場地類型",
        "generate_recommendation": "生成餐廳推薦",
    }

    _MERMAID_DIAGRAM = """graph TD
    A[提取城市名稱] --> B[查詢天氣]
    B --> C[決定場地類型]
    C --> D[生成餐廳推薦]
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
    ) -> None:
        self._graph = create_food_recommend_graph(llm_client, tool_registry)

    @property
    def flow_name(self) -> str:
        """流程名稱。"""
        return "food"

    async def execute(
        self,
        user_input: str,
        on_node_change: NodeChangeCallback | None = None,
    ) -> str:
        """執行美食推薦流程。

        Args:
            user_input: 使用者輸入文字。
            on_node_change: 節點狀態變更回呼。

        Returns:
            流程產生的回應文字。
        """
        initial_state: dict = {"user_input": user_input}

        result = await self._graph.ainvoke(initial_state)

        if error := result.get("error"):
            return f"處理過程中發生錯誤：{error}"

        return result.get("response", "抱歉，無法產生回應。")

    def get_visualization(self) -> str | None:
        """取得 Mermaid 視覺化圖表。"""
        return self._MERMAID_DIAGRAM
