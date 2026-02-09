"""ToolRegistry.auto_discover() 單元測試。"""

from __future__ import annotations

from voice_assistant.tools.registry import ToolRegistry


class TestAutoDiscover:
    """測試 ToolRegistry.auto_discover() 自動掃描機制。"""

    def test_discovers_existing_tools(self) -> None:
        """auto_discover 能發現現有 3 個 Tool。"""
        registry = ToolRegistry()
        registered = registry.auto_discover()

        assert "get_weather" in registered
        assert "get_exchange_rate" in registered
        assert "get_stock_price" in registered
        assert len(registered) == 3

    def test_does_not_register_base_tool(self) -> None:
        """auto_discover 不會註冊 BaseTool 本身。"""
        registry = ToolRegistry()
        registry.auto_discover()

        tool_names = registry.list_tools()
        # BaseTool 是 ABC，不應被註冊
        assert all(name != "BaseTool" for name in tool_names)

    def test_skips_already_registered_tools(self) -> None:
        """auto_discover 跳過已經註冊的工具。"""
        from voice_assistant.tools.weather import WeatherTool

        registry = ToolRegistry()
        registry.register(WeatherTool())

        registered = registry.auto_discover()

        # WeatherTool 已手動註冊，不應出現在 auto_discover 的回傳中
        assert "get_weather" not in registered
        # 但其他工具應被發現
        assert "get_exchange_rate" in registered
        assert "get_stock_price" in registered

    def test_import_error_does_not_interrupt_scan(self) -> None:
        """模組匯入失敗時不中斷掃描。"""
        # 傳入不存在的套件名稱，測試 import 錯誤處理
        registry = ToolRegistry()
        registered = registry.auto_discover(package_name="nonexistent.package")
        assert registered == []

    def test_returns_registered_tool_names(self) -> None:
        """auto_discover 回傳已註冊的工具名稱列表。"""
        registry = ToolRegistry()
        registered = registry.auto_discover()

        # 回傳的是工具名稱，不是類別名稱
        assert isinstance(registered, list)
        assert all(isinstance(name, str) for name in registered)

    def test_tools_are_functional_after_auto_discover(self) -> None:
        """auto_discover 註冊的工具可以正常使用。"""
        registry = ToolRegistry()
        registry.auto_discover()

        # 確認可以透過 get 取得工具
        weather_tool = registry.get("get_weather")
        assert weather_tool is not None
        assert weather_tool.name == "get_weather"

        exchange_tool = registry.get("get_exchange_rate")
        assert exchange_tool is not None

        stock_tool = registry.get("get_stock_price")
        assert stock_tool is not None

    def test_openai_tools_format_after_auto_discover(self) -> None:
        """auto_discover 後 get_openai_tools() 回傳正確格式。"""
        registry = ToolRegistry()
        registry.auto_discover()

        openai_tools = registry.get_openai_tools()
        assert len(openai_tools) == 3
        for tool in openai_tools:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
