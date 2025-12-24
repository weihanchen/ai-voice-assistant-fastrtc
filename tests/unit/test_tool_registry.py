"""Unit tests for BaseTool and ToolRegistry."""

from __future__ import annotations

import pytest

from tests.fixtures.mock_tool import (
    AnotherMockTool,
    FailingMockTool,
    MockTool,
)
from voice_assistant.tools.registry import ToolRegistry


class TestBaseTool:
    """Tests for BaseTool abstract class."""

    def test_to_openai_tool(self) -> None:
        """Test OpenAI tool format conversion."""
        tool = MockTool()
        openai_tool = tool.to_openai_tool()

        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "mock_tool"
        assert openai_tool["function"]["description"] == "A mock tool for testing"
        assert "properties" in openai_tool["function"]["parameters"]

    @pytest.mark.asyncio
    async def test_execute_returns_tool_result(self) -> None:
        """Test tool execution returns ToolResult."""
        tool = MockTool()
        result = await tool.execute(message="hello")

        assert result.success is True
        assert result.data == {"echo": "hello"}


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_register_tool(self) -> None:
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register(tool)

        assert registry.get("mock_tool") is tool

    def test_register_duplicate_raises_error(self) -> None:
        """Test registering duplicate tool name raises ValueError."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = MockTool()

        registry.register(tool1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool2)

    def test_get_nonexistent_returns_none(self) -> None:
        """Test getting non-existent tool returns None."""
        registry = ToolRegistry()

        assert registry.get("nonexistent") is None

    def test_list_tools(self) -> None:
        """Test listing all registered tool names."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())

        tools = registry.list_tools()

        assert "mock_tool" in tools
        assert "another_tool" in tools
        assert len(tools) == 2

    def test_list_tools_empty(self) -> None:
        """Test listing tools when registry is empty."""
        registry = ToolRegistry()

        assert registry.list_tools() == []

    def test_get_openai_tools(self) -> None:
        """Test getting all tools in OpenAI format."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())

        openai_tools = registry.get_openai_tools()

        assert len(openai_tools) == 2
        names = [t["function"]["name"] for t in openai_tools]
        assert "mock_tool" in names
        assert "another_tool" in names

    def test_get_openai_tools_empty(self) -> None:
        """Test getting OpenAI tools when registry is empty."""
        registry = ToolRegistry()

        assert registry.get_openai_tools() == []

    @pytest.mark.asyncio
    async def test_execute_tool(self) -> None:
        """Test executing a registered tool."""
        registry = ToolRegistry()
        registry.register(MockTool())

        result = await registry.execute("mock_tool", {"message": "test"})

        assert result.success is True
        assert result.data == {"echo": "test"}

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self) -> None:
        """Test executing non-existent tool returns error."""
        registry = ToolRegistry()

        result = await registry.execute("nonexistent", {})

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_handles_tool_error(self) -> None:
        """Test execute handles tool exceptions gracefully."""
        registry = ToolRegistry()
        registry.register(FailingMockTool())

        result = await registry.execute("failing_tool", {})

        assert result.success is False
        assert "always fails" in result.error
