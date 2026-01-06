"""工具執行節點。

執行對應的 Tool 並將結果轉換為流程狀態格式。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from voice_assistant.flows.state import FlowState

if TYPE_CHECKING:
    from voice_assistant.tools.registry import ToolRegistry


def create_tool_executor_node(tool_registry: ToolRegistry) -> Any:
    """建立工具執行節點。

    Args:
        tool_registry: Tool 註冊表

    Returns:
        可用於 LangGraph 的節點函式
    """

    async def execute_tool(state: FlowState) -> dict[str, Any]:
        """執行工具節點函式。

        Args:
            state: 流程狀態

        Returns:
            更新的狀態欄位
        """
        tool_name = state.get("tool_name")
        tool_args = state.get("tool_args", {})

        if not tool_name:
            return {
                "error": "未指定要執行的工具",
            }

        try:
            # 執行 Tool
            result = await tool_registry.execute(tool_name, tool_args)

            if result.success:
                return {
                    "tool_result": result.data,
                }
            else:
                return {
                    "error": result.error or "工具執行失敗",
                }

        except Exception as e:
            return {
                "error": f"執行工具時發生錯誤: {e!s}",
            }

    return execute_tool
