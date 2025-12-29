"""Unit tests for ExchangeRateTool."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

# Import mock data
from tests.fixtures.mock_exchange_rate import (
    MOCK_EXCHANGE_RATE_JPY,
    MOCK_EXCHANGE_RATE_TWD,
    MOCK_EXCHANGE_RATE_USD,
)
from voice_assistant.tools.exchange_rate import (
    CURRENCY_ALIASES,
    CURRENCY_NAMES,
    ExchangeRateTool,
)


class TestExchangeRateToolProperties:
    """T006: 測試 ExchangeRateTool 基本屬性。"""

    @pytest.fixture
    def exchange_rate_tool(self) -> ExchangeRateTool:
        return ExchangeRateTool()

    def test_implements_base_tool(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """驗證實作 BaseTool。"""
        assert hasattr(exchange_rate_tool, "name")
        assert hasattr(exchange_rate_tool, "description")
        assert hasattr(exchange_rate_tool, "parameters")
        assert hasattr(exchange_rate_tool, "execute")

    def test_name(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """驗證工具名稱。"""
        assert exchange_rate_tool.name == "get_exchange_rate"

    def test_description_contains_currencies(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """驗證描述包含支援的貨幣。"""
        desc = exchange_rate_tool.description
        assert "美金" in desc
        assert "日幣" in desc
        assert "歐元" in desc
        assert "新台幣" in desc

    def test_parameters_schema(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """驗證參數 schema。"""
        params = exchange_rate_tool.parameters
        assert params["type"] == "object"
        assert "from_currency" in params["properties"]
        assert "to_currency" in params["properties"]
        assert "amount" in params["properties"]
        assert "from_currency" in params["required"]

    def test_to_openai_tool_format(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """驗證 OpenAI tools 格式輸出。"""
        tool_def = exchange_rate_tool.to_openai_tool()
        assert tool_def["type"] == "function"
        assert tool_def["function"]["name"] == "get_exchange_rate"
        assert "parameters" in tool_def["function"]


class TestStaticData:
    """測試靜態資料結構。"""

    def test_currency_aliases_count(self) -> None:
        """驗證別名數量足夠。"""
        # 至少有 9 種貨幣，每種至少 2 個別名（ISO + 中文）
        assert len(CURRENCY_ALIASES) >= 18

    def test_currency_aliases_mapping(self) -> None:
        """驗證貨幣別名對照正確。"""
        # 美元
        assert CURRENCY_ALIASES["美金"] == "USD"
        assert CURRENCY_ALIASES["美元"] == "USD"
        assert CURRENCY_ALIASES["USD"] == "USD"
        # 日圓
        assert CURRENCY_ALIASES["日幣"] == "JPY"
        assert CURRENCY_ALIASES["日圓"] == "JPY"
        # 新台幣
        assert CURRENCY_ALIASES["台幣"] == "TWD"
        assert CURRENCY_ALIASES["新台幣"] == "TWD"

    def test_currency_names_count(self) -> None:
        """驗證貨幣名稱數量。"""
        assert len(CURRENCY_NAMES) == 9

    def test_currency_names_mapping(self) -> None:
        """驗證貨幣顯示名稱正確。"""
        assert CURRENCY_NAMES["USD"] == "美元"
        assert CURRENCY_NAMES["JPY"] == "日圓"
        assert CURRENCY_NAMES["TWD"] == "新台幣"


class TestResolveCurrencyMethod:
    """T007: 測試貨幣解析邏輯。"""

    @pytest.fixture
    def exchange_rate_tool(self) -> ExchangeRateTool:
        return ExchangeRateTool()

    def test_resolve_standard_code(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """測試標準 ISO 代碼解析。"""
        assert exchange_rate_tool._resolve_currency("USD") == "USD"
        assert exchange_rate_tool._resolve_currency("JPY") == "JPY"
        assert exchange_rate_tool._resolve_currency("TWD") == "TWD"

    def test_resolve_chinese_name(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """測試中文名稱解析。"""
        assert exchange_rate_tool._resolve_currency("美金") == "USD"
        assert exchange_rate_tool._resolve_currency("日幣") == "JPY"
        assert exchange_rate_tool._resolve_currency("台幣") == "TWD"

    def test_resolve_alias(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """測試別名解析。"""
        assert exchange_rate_tool._resolve_currency("美元") == "USD"
        assert exchange_rate_tool._resolve_currency("日圓") == "JPY"
        assert exchange_rate_tool._resolve_currency("新台幣") == "TWD"

    def test_resolve_with_whitespace(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試帶空白的輸入。"""
        assert exchange_rate_tool._resolve_currency(" USD ") == "USD"
        assert exchange_rate_tool._resolve_currency("美金 ") == "USD"

    def test_resolve_with_fullwidth_space(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試帶全形空白的輸入。"""
        assert exchange_rate_tool._resolve_currency("美金\u3000") == "USD"

    def test_resolve_unsupported_currency(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試不支援的貨幣。"""
        assert exchange_rate_tool._resolve_currency("比特幣") is None
        assert exchange_rate_tool._resolve_currency("BTC") is None

    def test_resolve_unrecognized_input(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試無法辨識的輸入。"""
        assert exchange_rate_tool._resolve_currency("ABCD") is None
        assert exchange_rate_tool._resolve_currency("") is None


class TestExecuteBasicQuery:
    """T014: 測試基本匯率查詢（User Story 1）。"""

    @pytest.fixture
    def exchange_rate_tool(self) -> ExchangeRateTool:
        return ExchangeRateTool()

    @pytest.mark.asyncio
    async def test_execute_success_usd_to_twd(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試成功查詢 USD → TWD。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_EXCHANGE_RATE_USD

            result = await exchange_rate_tool.execute(from_currency="USD")

            assert result.success is True
            assert result.data is not None
            assert result.data["from_currency"] == "USD"
            assert result.data["to_currency"] == "TWD"
            assert result.data["from_amount"] == 1.0
            assert result.data["rate"] == 32.58
            assert result.data["to_amount"] == 32.58
            assert "queried_at" in result.data

    @pytest.mark.asyncio
    async def test_execute_success_with_chinese_name(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試使用中文貨幣名稱查詢。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_EXCHANGE_RATE_USD

            result = await exchange_rate_tool.execute(from_currency="美金")

            assert result.success is True
            assert result.data is not None
            assert result.data["from_currency"] == "USD"
            assert result.data["to_currency"] == "TWD"

    @pytest.mark.asyncio
    async def test_execute_success_jpy_to_twd(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試 JPY → TWD 查詢。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_EXCHANGE_RATE_JPY

            result = await exchange_rate_tool.execute(
                from_currency="日幣", to_currency="台幣"
            )

            assert result.success is True
            assert result.data is not None
            assert result.data["from_currency"] == "JPY"
            assert result.data["to_currency"] == "TWD"


class TestExecuteAmountConversion:
    """T015-T016: 測試金額換算（User Story 2）。"""

    @pytest.fixture
    def exchange_rate_tool(self) -> ExchangeRateTool:
        return ExchangeRateTool()

    @pytest.mark.asyncio
    async def test_execute_with_amount(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """T015: 測試金額換算。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_EXCHANGE_RATE_USD

            result = await exchange_rate_tool.execute(
                from_currency="USD", to_currency="TWD", amount=100
            )

            assert result.success is True
            assert result.data is not None
            assert result.data["from_amount"] == 100
            assert result.data["to_amount"] == 3258.0  # 100 * 32.58

    @pytest.mark.asyncio
    async def test_execute_twd_to_usd(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """T016: 測試雙向換算 TWD → USD。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_EXCHANGE_RATE_TWD

            result = await exchange_rate_tool.execute(
                from_currency="TWD", to_currency="USD", amount=1000
            )

            assert result.success is True
            assert result.data is not None
            assert result.data["from_currency"] == "TWD"
            assert result.data["to_currency"] == "USD"
            assert result.data["from_amount"] == 1000
            assert result.data["to_amount"] == 30.7  # 1000 * 0.0307

    @pytest.mark.asyncio
    async def test_execute_invalid_amount_zero(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試無效金額（零）。"""
        result = await exchange_rate_tool.execute(
            from_currency="USD", to_currency="TWD", amount=0
        )

        assert result.success is False
        assert result.error is not None
        assert "invalid_amount" in result.error

    @pytest.mark.asyncio
    async def test_execute_invalid_amount_negative(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試無效金額（負數）。"""
        result = await exchange_rate_tool.execute(
            from_currency="USD", to_currency="TWD", amount=-100
        )

        assert result.success is False
        assert result.error is not None
        assert "invalid_amount" in result.error

    @pytest.mark.asyncio
    async def test_execute_same_currency(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試相同貨幣驗證。"""
        result = await exchange_rate_tool.execute(
            from_currency="USD", to_currency="美金", amount=100
        )

        assert result.success is False
        assert result.error is not None
        assert "same_currency" in result.error


class TestExecuteUnsupportedCurrency:
    """T021: 測試不支援貨幣錯誤處理（User Story 3）。"""

    @pytest.fixture
    def exchange_rate_tool(self) -> ExchangeRateTool:
        return ExchangeRateTool()

    @pytest.mark.asyncio
    async def test_execute_unsupported_from_currency(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試不支援的來源貨幣。"""
        result = await exchange_rate_tool.execute(from_currency="比特幣")

        assert result.success is False
        assert result.error is not None
        assert "unsupported_currency" in result.error

    @pytest.mark.asyncio
    async def test_execute_unsupported_to_currency(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試不支援的目標貨幣。"""
        result = await exchange_rate_tool.execute(
            from_currency="USD", to_currency="比特幣"
        )

        assert result.success is False
        assert result.error is not None
        assert "unsupported_currency" in result.error

    @pytest.mark.asyncio
    async def test_execute_unrecognized_currency(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試無法辨識的貨幣。"""
        result = await exchange_rate_tool.execute(from_currency="ABCD123")

        assert result.success is False
        assert result.error is not None
        assert "unsupported_currency" in result.error


class TestErrorHandling:
    """T022: 測試 API 錯誤處理。"""

    @pytest.fixture
    def exchange_rate_tool(self) -> ExchangeRateTool:
        return ExchangeRateTool()

    @pytest.mark.asyncio
    async def test_api_timeout(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """測試 API 逾時處理。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = httpx.TimeoutException("Timeout")

            result = await exchange_rate_tool.execute(from_currency="USD")

            assert result.success is False
            assert result.error is not None
            assert "api_timeout" in result.error

    @pytest.mark.asyncio
    async def test_network_error(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """測試網路錯誤處理。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = httpx.RequestError("Network error")

            result = await exchange_rate_tool.execute(from_currency="USD")

            assert result.success is False
            assert result.error is not None
            assert "network_error" in result.error

    @pytest.mark.asyncio
    async def test_api_error(self, exchange_rate_tool: ExchangeRateTool) -> None:
        """測試 API 回應錯誤處理。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = ValueError("API returned error")

            result = await exchange_rate_tool.execute(from_currency="USD")

            assert result.success is False
            assert result.error is not None
            assert "api_error" in result.error

    @pytest.mark.asyncio
    async def test_missing_rate_in_response(
        self, exchange_rate_tool: ExchangeRateTool
    ) -> None:
        """測試回應中缺少特定匯率。"""
        with patch.object(
            exchange_rate_tool, "_fetch_exchange_rate", new_callable=AsyncMock
        ) as mock_fetch:
            # 回應中沒有 TWD 匯率
            mock_fetch.return_value = {
                "result": "success",
                "base_code": "USD",
                "rates": {"EUR": 0.96},  # 缺少 TWD
            }

            result = await exchange_rate_tool.execute(from_currency="USD")

            assert result.success is False
            assert result.error is not None
            assert "api_error" in result.error
