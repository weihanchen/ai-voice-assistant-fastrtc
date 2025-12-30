"""Smoke tests - 驗證系統基本功能可用。

執行方式：
    uv run pytest tests/smoke/ -v

注意：這些測試會呼叫真實的外部 API，需要網路連線。
"""

from __future__ import annotations

import pytest

from voice_assistant.tools import (
    ExchangeRateTool,
    StockPriceTool,
    ToolRegistry,
    WeatherTool,
)


class TestToolsCanExecute:
    """驗證各工具可以正常執行並取得結果。"""

    @pytest.mark.asyncio
    async def test_weather_tool(self) -> None:
        """天氣查詢工具可用。"""
        tool = WeatherTool()
        result = await tool.execute(city="台北")

        assert result.success, f"天氣查詢失敗: {result.error}"
        assert result.data is not None
        assert "temperature" in result.data

    @pytest.mark.asyncio
    async def test_exchange_rate_tool(self) -> None:
        """匯率查詢工具可用。"""
        tool = ExchangeRateTool()
        result = await tool.execute(
            from_currency="USD",
            to_currency="TWD",
            amount=100,
        )

        assert result.success, f"匯率查詢失敗: {result.error}"
        assert result.data is not None
        assert "to_amount" in result.data

    @pytest.mark.asyncio
    async def test_stock_price_tool(self) -> None:
        """股價查詢工具可用。"""
        tool = StockPriceTool()
        result = await tool.execute(stock="2330")

        assert result.success, f"股價查詢失敗: {result.error}"
        assert result.data is not None
        assert result.data["symbol"] == "2330.TW"
        assert "price" in result.data


class TestToolRegistry:
    """驗證 ToolRegistry 整合正常。"""

    @pytest.mark.asyncio
    async def test_registry_can_execute_tools(self) -> None:
        """ToolRegistry 可以註冊並執行工具。"""
        registry = ToolRegistry()
        registry.register(WeatherTool())
        registry.register(ExchangeRateTool())
        registry.register(StockPriceTool())

        # 驗證工具已註冊
        tools = registry.get_openai_tools()
        tool_names = [t["function"]["name"] for t in tools]

        assert "get_weather" in tool_names
        assert "get_exchange_rate" in tool_names
        assert "get_stock_price" in tool_names

        # 驗證可以透過 registry 執行
        result = await registry.execute("get_weather", {"city": "台北"})
        assert result.success, f"透過 registry 執行失敗: {result.error}"
