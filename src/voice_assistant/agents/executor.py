"""Multi-Agent Executor.

多代理流程執行器，提供統一的執行介面。
"""

from __future__ import annotations

from voice_assistant.agents.graph import create_multi_agent_graph
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools.registry import ToolRegistry


class MultiAgentExecutor:
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

    async def execute(self, user_input: str) -> str:
        """執行多代理流程。

        Args:
            user_input: 使用者輸入

        Returns:
            str: 自然語言回應
        """
        try:
            result = await self._graph.ainvoke(
                {"user_input": user_input},
            )
            return result.get("final_response", "抱歉，處理過程中發生錯誤。")
        except Exception as e:
            return f"抱歉，處理過程中發生錯誤: {e}"
