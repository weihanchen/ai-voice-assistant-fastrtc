"""Multi-Agent Executor.

多代理流程執行器，提供統一的執行介面。
"""

from __future__ import annotations

import logging

from voice_assistant.agents.graph import create_multi_agent_graph
from voice_assistant.flows.base import BaseFlowExecutor, NodeChangeCallback
from voice_assistant.flows.visualization import (
    NodeStatus,
    apply_node_labels,
    get_mermaid_diagram,
)
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class MultiAgentExecutor(BaseFlowExecutor):
    """多代理流程執行器。

    整合 Multi-Agent Graph，提供統一的執行介面。

    Args:
        llm_client: LLM 客戶端
        tool_registry: Tool 註冊表
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
    ) -> None:
        """初始化執行器。"""
        self._llm_client = llm_client
        self._tool_registry = tool_registry
        self._graph = create_multi_agent_graph(llm_client, tool_registry)

    @property
    def flow_name(self) -> str:
        """流程名稱。"""
        return "multi_agent"

    async def execute(
        self,
        user_input: str,
        on_node_change: NodeChangeCallback | None = None,
    ) -> str:
        """執行多代理流程。

        使用 astream(stream_mode="updates") 逐步追蹤節點執行狀態，
        並透過 on_node_change callback 即時回報。

        Args:
            user_input: 使用者輸入
            on_node_change: 節點狀態變更回呼

        Returns:
            str: 自然語言回應
        """
        try:
            result: dict = {}
            async for chunk in self._graph.astream(
                {"user_input": user_input},
                stream_mode="updates",
            ):
                # chunk 格式: {node_name: node_output}
                for node_name in chunk:
                    if on_node_change:
                        on_node_change(node_name, NodeStatus.RUNNING)
                    logger.debug("[MultiAgentExecutor] 節點執行中: %s", node_name)
                    result.update(chunk[node_name])
                    if on_node_change:
                        on_node_change(node_name, NodeStatus.COMPLETED)

            return result.get("final_response", "抱歉，處理過程中發生錯誤。")
        except Exception as e:
            return f"抱歉，處理過程中發生錯誤: {e}"

    # 節點 ID → 使用者友善中文標籤
    _NODE_LABELS: dict[str, str] = {
        "__start__": "開始",
        "supervisor_decompose": "任務分解",
        "execute_agent": "代理執行",
        "aggregate": "結果彙整",
        "__end__": "結束",
    }

    def get_visualization(self) -> str:
        """取得多代理流程視覺化 Mermaid 圖。

        Returns:
            附有中文標籤的 Mermaid 格式字串
        """
        raw = get_mermaid_diagram(self._graph)
        return apply_node_labels(raw, self._NODE_LABELS)
