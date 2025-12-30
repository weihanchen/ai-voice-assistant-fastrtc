"""Unit tests for stock price tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from voice_assistant.tools.stock_price import StockPriceTool


@pytest.fixture
def tool() -> StockPriceTool:
    """建立 StockPriceTool 實例。"""
    return StockPriceTool()


# T006: _resolve_stock 方法測試
class TestResolveStock:
    """測試股票名稱解析。"""

    def test_tw_chinese_name(self, tool: StockPriceTool) -> None:
        """測試台股中文名稱解析。"""
        result = tool._resolve_stock("台積電")
        assert result == ("2330.TW", "TW")

    def test_tw_chinese_name_honhai(self, tool: StockPriceTool) -> None:
        """測試台股中文名稱解析 - 鴻海。"""
        result = tool._resolve_stock("鴻海")
        assert result == ("2317.TW", "TW")

    def test_tw_code_only(self, tool: StockPriceTool) -> None:
        """測試台股純數字代碼。"""
        result = tool._resolve_stock("2330")
        assert result == ("2330.TW", "TW")

    def test_tw_code_mediatek(self, tool: StockPriceTool) -> None:
        """測試台股純數字代碼 - 聯發科。"""
        result = tool._resolve_stock("2454")
        assert result == ("2454.TW", "TW")

    def test_us_english_name(self, tool: StockPriceTool) -> None:
        """測試美股英文名稱。"""
        result = tool._resolve_stock("Apple")
        assert result == ("AAPL", "US")

    def test_us_english_name_microsoft(self, tool: StockPriceTool) -> None:
        """測試美股英文名稱 - Microsoft。"""
        result = tool._resolve_stock("Microsoft")
        assert result == ("MSFT", "US")

    def test_us_chinese_name(self, tool: StockPriceTool) -> None:
        """測試美股中文名稱。"""
        result = tool._resolve_stock("蘋果")
        assert result == ("AAPL", "US")

    def test_us_chinese_name_tesla(self, tool: StockPriceTool) -> None:
        """測試美股中文名稱 - 特斯拉。"""
        result = tool._resolve_stock("特斯拉")
        assert result == ("TSLA", "US")

    def test_us_code_uppercase(self, tool: StockPriceTool) -> None:
        """測試美股代碼（大寫）。"""
        result = tool._resolve_stock("AAPL")
        assert result == ("AAPL", "US")

    def test_us_code_lowercase(self, tool: StockPriceTool) -> None:
        """測試美股代碼（小寫轉換）。"""
        result = tool._resolve_stock("aapl")
        assert result == ("AAPL", "US")

    def test_us_code_mixedcase(self, tool: StockPriceTool) -> None:
        """測試美股代碼（混合大小寫）。"""
        result = tool._resolve_stock("Msft")
        assert result == ("MSFT", "US")

    def test_unsupported_stock(self, tool: StockPriceTool) -> None:
        """測試不支援的股票名稱。"""
        result = tool._resolve_stock("小明公司")
        assert result is None

    def test_unsupported_code(self, tool: StockPriceTool) -> None:
        """測試不支援的股票代碼。"""
        result = tool._resolve_stock("XYZ123")
        assert result is None

    def test_empty_string(self, tool: StockPriceTool) -> None:
        """測試空字串。"""
        result = tool._resolve_stock("")
        assert result is None

    def test_whitespace_handling(self, tool: StockPriceTool) -> None:
        """測試空白處理。"""
        result = tool._resolve_stock("  台積電  ")
        assert result == ("2330.TW", "TW")

    def test_fullwidth_space(self, tool: StockPriceTool) -> None:
        """測試全形空白處理。"""
        result = tool._resolve_stock("台積電\u3000")
        assert result == ("2330.TW", "TW")

    def test_non_string_input(self, tool: StockPriceTool) -> None:
        """測試非字串輸入。"""
        result = tool._resolve_stock(123)  # type: ignore
        assert result is None


# T007: execute 成功情境測試
class TestExecuteSuccess:
    """測試 execute 方法成功情境。"""

    @pytest.mark.asyncio
    async def test_tw_stock_success(self, tool: StockPriceTool) -> None:
        """測試台股查詢成功。"""
        mock_info = MagicMock()
        mock_info.last_price = 1080.5
        mock_info.currency = "TWD"

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("台積電")

        assert result.success is True
        assert result.data is not None
        assert result.data["symbol"] == "2330.TW"
        assert result.data["name"] == "台積電"
        assert result.data["price"] == 1080.5
        assert result.data["currency"] == "TWD"
        assert result.data["market"] == "TW"
        assert "queried_at" in result.data

    @pytest.mark.asyncio
    async def test_us_stock_success(self, tool: StockPriceTool) -> None:
        """測試美股查詢成功。"""
        mock_info = MagicMock()
        mock_info.last_price = 254.50
        mock_info.currency = "USD"

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("Apple")

        assert result.success is True
        assert result.data is not None
        assert result.data["symbol"] == "AAPL"
        assert result.data["name"] == "蘋果"
        assert result.data["price"] == 254.5
        assert result.data["currency"] == "USD"
        assert result.data["market"] == "US"

    @pytest.mark.asyncio
    async def test_tw_stock_by_code(self, tool: StockPriceTool) -> None:
        """測試用代碼查詢台股。"""
        mock_info = MagicMock()
        mock_info.last_price = 500.0
        mock_info.currency = "TWD"

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("2317")

        assert result.success is True
        assert result.data is not None
        assert result.data["symbol"] == "2317.TW"
        assert result.data["name"] == "鴻海"

    @pytest.mark.asyncio
    async def test_us_stock_chinese_name(self, tool: StockPriceTool) -> None:
        """測試用中文名稱查詢美股。"""
        mock_info = MagicMock()
        mock_info.last_price = 430.20
        mock_info.currency = "USD"

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("特斯拉")

        assert result.success is True
        assert result.data is not None
        assert result.data["symbol"] == "TSLA"
        assert result.data["name"] == "特斯拉"

    @pytest.mark.asyncio
    async def test_currency_fallback_tw(self, tool: StockPriceTool) -> None:
        """測試台股貨幣預設值。"""
        mock_info = MagicMock()
        mock_info.last_price = 100.0
        mock_info.currency = None

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("2330")

        assert result.success is True
        assert result.data is not None
        assert result.data["currency"] == "TWD"

    @pytest.mark.asyncio
    async def test_currency_fallback_us(self, tool: StockPriceTool) -> None:
        """測試美股貨幣預設值。"""
        mock_info = MagicMock()
        mock_info.last_price = 100.0
        mock_info.currency = None

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("AAPL")

        assert result.success is True
        assert result.data is not None
        assert result.data["currency"] == "USD"


# T014-T016: User Story 2 錯誤測試（提前撰寫）
class TestExecuteErrors:
    """測試 execute 方法錯誤情境。"""

    @pytest.mark.asyncio
    async def test_unsupported_stock(self, tool: StockPriceTool) -> None:
        """測試不支援的股票。"""
        result = await tool.execute("小明公司")

        assert result.success is False
        assert result.error is not None
        assert "unsupported_stock" in result.error
        assert "找不到這支股票" in result.error

    @pytest.mark.asyncio
    async def test_unsupported_code(self, tool: StockPriceTool) -> None:
        """測試不支援的代碼。"""
        result = await tool.execute("XYZ123")

        assert result.success is False
        assert "unsupported_stock" in result.error

    @pytest.mark.asyncio
    async def test_api_timeout(self, tool: StockPriceTool) -> None:
        """測試 API 逾時。"""
        import asyncio

        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(10)
            return {}

        with patch.object(tool, "_fetch_price", side_effect=TimeoutError()):
            result = await tool.execute("台積電")

        assert result.success is False
        assert result.error is not None
        assert "api_timeout" in result.error
        assert "逾時" in result.error

    @pytest.mark.asyncio
    async def test_api_error(self, tool: StockPriceTool) -> None:
        """測試 API 一般錯誤。"""
        with patch.object(tool, "_fetch_price", side_effect=Exception("Network error")):
            result = await tool.execute("台積電")

        assert result.success is False
        assert result.error is not None
        assert "api_error" in result.error
        assert "暫時無法使用" in result.error

    @pytest.mark.asyncio
    async def test_no_price_data(self, tool: StockPriceTool) -> None:
        """測試無報價資料。"""
        mock_info = MagicMock()
        mock_info.last_price = None
        mock_info.currency = "TWD"

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("台積電")

        assert result.success is False
        assert result.error is not None
        assert "no_data" in result.error
        assert "無法取得報價" in result.error

    @pytest.mark.asyncio
    async def test_invalid_price_type(self, tool: StockPriceTool) -> None:
        """測試無效的價格類型。"""
        mock_info = MagicMock()
        mock_info.last_price = "invalid"
        mock_info.currency = "TWD"

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("台積電")

        assert result.success is False
        assert "no_data" in result.error

    @pytest.mark.asyncio
    async def test_bool_price_rejected(self, tool: StockPriceTool) -> None:
        """測試布林值價格被拒絕。"""
        mock_info = MagicMock()
        mock_info.last_price = True
        mock_info.currency = "TWD"

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_info

        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await tool.execute("台積電")

        assert result.success is False
        assert "no_data" in result.error


class TestToolProperties:
    """測試工具屬性。"""

    def test_name(self, tool: StockPriceTool) -> None:
        """測試工具名稱。"""
        assert tool.name == "get_stock_price"

    def test_description(self, tool: StockPriceTool) -> None:
        """測試工具描述。"""
        desc = tool.description
        assert "股票" in desc
        assert "台股" in desc
        assert "美股" in desc

    def test_parameters_schema(self, tool: StockPriceTool) -> None:
        """測試參數 schema。"""
        params = tool.parameters
        assert params["type"] == "object"
        assert "stock" in params["properties"]
        assert params["required"] == ["stock"]

    def test_to_openai_tool(self, tool: StockPriceTool) -> None:
        """測試 OpenAI 工具格式。"""
        openai_tool = tool.to_openai_tool()
        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "get_stock_price"
        assert "parameters" in openai_tool["function"]
