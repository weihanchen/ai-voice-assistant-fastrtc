"""工具執行節點單元測試。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from voice_assistant.flows.nodes.tool_executor import create_tool_executor_node
from voice_assistant.flows.state import FlowState
from voice_assistant.tools.schemas import ToolResult


class TestToolExecutorNode:
    """工具執行節點測試。"""

    @pytest.mark.asyncio
    async def test_execute_weather_tool_success(self) -> None:
        """成功執行天氣工具。"""
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(
            return_value=ToolResult.ok(
                {
                    "city": "台北",
                    "temperature": 25.0,
                    "weather": "晴朗",
                }
            )
        )

        execute = create_tool_executor_node(mock_registry)
        state: FlowState = {
            "user_input": "台北天氣",
            "tool_name": "get_weather",
            "tool_args": {"city": "台北"},
        }

        result = await execute(state)

        assert "tool_result" in result
        assert result["tool_result"]["city"] == "台北"
        mock_registry.execute.assert_called_once_with(
            "get_weather", {"city": "台北"}
        )

    @pytest.mark.asyncio
    async def test_execute_tool_failure(self) -> None:
        """工具執行失敗應回傳錯誤。"""
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(
            return_value=ToolResult.fail("api_error: 服務暫時無法使用")
        )

        execute = create_tool_executor_node(mock_registry)
        state: FlowState = {
            "user_input": "台北天氣",
            "tool_name": "get_weather",
            "tool_args": {"city": "台北"},
        }

        result = await execute(state)

        assert "error" in result
        assert "服務暫時無法使用" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_without_tool_name(self) -> None:
        """缺少工具名稱應回傳錯誤。"""
        mock_registry = MagicMock()
        execute = create_tool_executor_node(mock_registry)
        state: FlowState = {
            "user_input": "台北天氣",
            "tool_args": {"city": "台北"},
        }

        result = await execute(state)

        assert "error" in result
        assert "未指定" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_exchange_tool(self) -> None:
        """成功執行匯率工具。"""
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(
            return_value=ToolResult.ok(
                {
                    "from_currency": "USD",
                    "to_currency": "TWD",
                    "amount": 100,
                    "rate": 31.5,
                    "result": 3150,
                }
            )
        )

        execute = create_tool_executor_node(mock_registry)
        state: FlowState = {
            "user_input": "100美金換台幣",
            "tool_name": "get_exchange_rate",
            "tool_args": {
                "from_currency": "USD",
                "to_currency": "TWD",
                "amount": 100,
            },
        }

        result = await execute(state)

        assert "tool_result" in result
        assert result["tool_result"]["result"] == 3150

    @pytest.mark.asyncio
    async def test_execute_stock_tool(self) -> None:
        """成功執行股票工具。"""
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(
            return_value=ToolResult.ok(
                {
                    "symbol": "2330.TW",
                    "name": "台積電",
                    "price": 580.0,
                    "change": 5.0,
                }
            )
        )

        execute = create_tool_executor_node(mock_registry)
        state: FlowState = {
            "user_input": "台積電股價",
            "tool_name": "get_stock_price",
            "tool_args": {"symbol": "2330.TW"},
        }

        result = await execute(state)

        assert "tool_result" in result
        assert result["tool_result"]["price"] == 580.0
