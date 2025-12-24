"""Mock tool for testing."""

from __future__ import annotations

from typing import Any

from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult


class MockTool(BaseTool):
    """測試用的 Mock 工具。"""

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo",
                }
            },
            "required": ["message"],
        }

    async def execute(self, message: str = "default") -> ToolResult:
        return ToolResult.ok({"echo": message})


class FailingMockTool(BaseTool):
    """會失敗的 Mock 工具。"""

    @property
    def name(self) -> str:
        return "failing_tool"

    @property
    def description(self) -> str:
        return "A tool that always fails"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        raise ValueError("This tool always fails")


class AnotherMockTool(BaseTool):
    """另一個 Mock 工具，用於測試多工具註冊。"""

    @property
    def name(self) -> str:
        return "another_tool"

    @property
    def description(self) -> str:
        return "Another mock tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult.ok({"status": "ok"})
