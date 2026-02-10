"""美食推薦流程執行器。

提供美食推薦流程的完整執行介面。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from voice_assistant.flows.base import BaseFlowExecutor, NodeChangeCallback
from voice_assistant.flows.graphs.food import create_food_recommend_graph
from voice_assistant.flows.visualization import (
    apply_node_labels,
    get_mermaid_diagram,
)

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
    ) -> tuple[bool, str]:
        """執行美食推薦流程。

        Args:
            user_input: 使用者輸入文字。
            on_node_change: 節點狀態變更回呼。

        Returns:
            (success, message) 元組，其中 success 為布林值，message 為結果或錯誤訊息。
        """
        initial_state: dict = {"user_input": user_input}

        try:
            result = await self._graph.ainvoke(initial_state)
        except Exception as exc:
            logger.exception("美食推薦流程執行失敗")
            return (False, f"處理過程中發生錯誤：{exc}")

        if error := result.get("error"):
            return (False, f"處理過程中發生錯誤：{error}")

        message = result.get("response", "抱歉，無法產生回應。")
        return (True, message)

    def get_visualization(self) -> str | None:
        """取得 Mermaid 視覺化圖表。"""
        raw = get_mermaid_diagram(self._graph)
        return apply_node_labels(raw, self._NODE_LABELS)
