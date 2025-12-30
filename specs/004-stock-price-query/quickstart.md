# Quickstart: Stock Price Query

**Feature**: 004-stock-price-query
**Date**: 2025-12-29

## 快速開始

本指南說明如何實作股票報價查詢工具。

---

## 1. 安裝依賴

```bash
uv add yfinance
```

---

## 2. 實作 StockPriceTool

建立檔案 `src/voice_assistant/tools/stock_price.py`：

```python
"""Stock price query tool for voice assistant."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult

# 台股對照表（台灣 50 成分股）
TW_STOCK_ALIASES: dict[str, str] = {
    "台積電": "2330.TW",
    "鴻海": "2317.TW",
    "聯發科": "2454.TW",
    # ... 完整對照表見 data-model.md
    "2330": "2330.TW",
    "2317": "2317.TW",
}

# 美股對照表（S&P 500 前 30 大）
US_STOCK_ALIASES: dict[str, str] = {
    "蘋果": "AAPL",
    "微軟": "MSFT",
    "Apple": "AAPL",
    "AAPL": "AAPL",
    # ... 完整對照表見 data-model.md
}

# 顯示名稱對照表
STOCK_DISPLAY_NAMES: dict[str, str] = {
    "2330.TW": "台積電",
    "AAPL": "蘋果",
    # ...
}

API_TIMEOUT = 8.0  # 秒


class StockPriceTool(BaseTool):
    """股票報價查詢工具。"""

    @property
    def name(self) -> str:
        return "get_stock_price"

    @property
    def description(self) -> str:
        return (
            "查詢股票即時報價。"
            "支援台股（台灣 50 成分股）與美股（S&P 500 前 30 大市值股票）。"
            "可使用中文名稱、英文名稱或股票代碼查詢。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock": {
                    "type": "string",
                    "description": "要查詢的股票名稱或代碼",
                },
            },
            "required": ["stock"],
        }

    def _resolve_stock(self, stock: str) -> tuple[str, str] | None:
        """解析股票名稱為代碼與市場。"""
        normalized = stock.strip().replace("\u3000", "").replace(" ", "")

        # 先查台股
        if normalized in TW_STOCK_ALIASES:
            symbol = TW_STOCK_ALIASES[normalized]
            return (symbol, "TW")

        # 再查美股（大小寫不敏感）
        upper = normalized.upper()
        if upper in US_STOCK_ALIASES:
            symbol = US_STOCK_ALIASES[upper]
            return (symbol, "US")
        if normalized in US_STOCK_ALIASES:
            symbol = US_STOCK_ALIASES[normalized]
            return (symbol, "US")

        return None

    async def _fetch_price(self, symbol: str) -> dict[str, Any]:
        """從 yfinance 取得股價。"""
        def _sync_fetch() -> dict[str, Any]:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            return {
                "price": info.last_price,
                "currency": info.currency,
            }

        return await asyncio.wait_for(
            asyncio.to_thread(_sync_fetch),
            timeout=API_TIMEOUT,
        )

    async def execute(self, stock: str) -> ToolResult:
        """執行股價查詢。"""
        resolved = self._resolve_stock(stock)
        if not resolved:
            return ToolResult.fail(
                "unsupported_stock: 抱歉，找不到這支股票，請確認名稱或代碼是否正確"
            )

        symbol, market = resolved
        display_name = STOCK_DISPLAY_NAMES.get(symbol, symbol)

        try:
            data = await self._fetch_price(symbol)
            price = data.get("price")
            currency = data.get("currency")

            if price is None or not isinstance(price, (int, float)):
                return ToolResult.fail(
                    "no_data: 無法取得報價資訊，該股票可能已下市或暫停交易"
                )

            result = {
                "symbol": symbol,
                "name": display_name,
                "price": round(price, 2),
                "currency": currency or ("TWD" if market == "TW" else "USD"),
                "market": market,
                "queried_at": datetime.now(UTC).isoformat(),
            }
            return ToolResult.ok(result)

        except asyncio.TimeoutError:
            return ToolResult.fail("api_timeout: 股票查詢逾時，請稍後再試")
        except Exception:
            return ToolResult.fail("api_error: 股票服務暫時無法使用，請稍後再試")
```

---

## 3. 註冊工具

更新 `src/voice_assistant/tools/__init__.py`：

```python
from voice_assistant.tools.stock_price import StockPriceTool

# 在 create_default_registry() 中加入：
registry.register(StockPriceTool())
```

---

## 4. 更新 SYSTEM_PROMPT

更新 `src/voice_assistant/voice/pipeline.py`：

```python
SYSTEM_PROMPT = (
    "你是一個友善的 AI 語音助理。"
    "請用繁體中文回答，回答要簡潔、口語化，適合語音輸出。"
    "當使用者詢問天氣相關問題時，請使用 get_weather 工具查詢天氣資訊。"
    "當使用者詢問匯率或貨幣換算時，請使用 get_exchange_rate 工具。"
    "當使用者詢問股票價格或股價時，請使用 get_stock_price 工具查詢股票報價。"
    "根據工具回傳的資料，用自然的口語回應使用者。"
)
```

---

## 5. 測試

建立測試檔案 `tests/unit/tools/test_stock_price.py`：

```python
import pytest
from voice_assistant.tools.stock_price import StockPriceTool


@pytest.fixture
def tool():
    return StockPriceTool()


class TestResolveStock:
    def test_tw_chinese_name(self, tool):
        result = tool._resolve_stock("台積電")
        assert result == ("2330.TW", "TW")

    def test_tw_code(self, tool):
        result = tool._resolve_stock("2330")
        assert result == ("2330.TW", "TW")

    def test_us_english_name(self, tool):
        result = tool._resolve_stock("Apple")
        assert result == ("AAPL", "US")

    def test_us_chinese_name(self, tool):
        result = tool._resolve_stock("蘋果")
        assert result == ("AAPL", "US")

    def test_unsupported(self, tool):
        result = tool._resolve_stock("小明公司")
        assert result is None


class TestExecute:
    @pytest.mark.asyncio
    async def test_unsupported_stock(self, tool):
        result = await tool.execute("小明公司")
        assert not result.success
        assert "unsupported_stock" in result.error
```

---

## 6. 執行測試

```bash
uv run pytest tests/unit/tools/test_stock_price.py -v
```

---

## 注意事項

1. **報價延遲**: yfinance 免費版報價有 15-20 分鐘延遲
2. **API 限制**: 每 IP 每小時 2,000 請求
3. **非同步包裝**: yfinance 是同步套件，需用 `asyncio.to_thread()` 包裝
