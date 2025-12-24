"""Tool registry for voice assistant."""

from __future__ import annotations

from typing import Any

from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult


class ToolRegistry:
    """工具註冊中心。"""

    def __init__(self) -> None:
        """初始化空的工具註冊表。"""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        註冊工具。

        Args:
            tool: BaseTool 實例

        Raises:
            ValueError: 工具名稱已存在時
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """
        依名稱取得工具。

        Args:
            name: 工具名稱

        Returns:
            BaseTool 實例，不存在時回傳 None
        """
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """
        列出所有已註冊的工具名稱。

        Returns:
            工具名稱列表
        """
        return list(self._tools.keys())

    def get_openai_tools(self) -> list[dict[str, Any]]:
        """
        取得所有工具的 OpenAI Function Calling 格式。

        Returns:
            工具定義列表，格式符合 OpenAI tools 參數
        """
        return [tool.to_openai_tool() for tool in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """
        執行指定工具。

        Args:
            name: 工具名稱
            arguments: 工具參數

        Returns:
            ToolResult 執行結果
        """
        tool = self.get(name)
        if not tool:
            return ToolResult.fail(f"Tool '{name}' not found")

        try:
            return await tool.execute(**arguments)
        except Exception as e:
            return ToolResult.fail(str(e))
