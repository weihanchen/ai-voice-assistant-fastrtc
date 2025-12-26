# Quickstart: Exchange Rate Query Tool

## 概述

本指南說明如何實作並測試匯率查詢工具。

## 前置條件

- 已完成 001-fastrtc-voice-pipeline
- 已完成 002-weather-query（參考 Tool 實作模式）
- Python 3.13 + uv 環境

## 實作步驟

### 1. 建立 ExchangeRateTool

```python
# src/voice_assistant/tools/exchange_rate.py

from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult

class ExchangeRateTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_exchange_rate"

    @property
    def description(self) -> str:
        return "查詢貨幣匯率或進行金額換算"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string", "description": "來源貨幣"},
                "to_currency": {"type": "string", "description": "目標貨幣", "default": "TWD"},
                "amount": {"type": "number", "description": "金額", "default": 1}
            },
            "required": ["from_currency"]
        }

    async def execute(self, from_currency: str, to_currency: str = "TWD", amount: float = 1.0) -> ToolResult:
        # 實作查詢邏輯
        ...
```

### 2. 更新 __init__.py

```python
# src/voice_assistant/tools/__init__.py

from voice_assistant.tools.exchange_rate import ExchangeRateTool

__all__ = [..., "ExchangeRateTool"]
```

### 3. 註冊工具

```python
# src/voice_assistant/voice/handlers/reply_on_pause.py

from voice_assistant.tools import ExchangeRateTool

tool_registry.register(ExchangeRateTool())
```

### 4. 建立測試

```python
# tests/unit/test_exchange_rate_tool.py

import pytest
from voice_assistant.tools.exchange_rate import ExchangeRateTool

@pytest.fixture
def tool():
    return ExchangeRateTool()

class TestExchangeRateTool:
    def test_name(self, tool):
        assert tool.name == "get_exchange_rate"

    @pytest.mark.asyncio
    async def test_execute_success(self, tool):
        result = await tool.execute(from_currency="USD", to_currency="TWD")
        assert result.success
```

## 驗證

### 單元測試

```bash
uv run pytest tests/unit/test_exchange_rate_tool.py -v
```

### 語音測試

```bash
uv run python -m voice_assistant.main
```

對著麥克風說：
- 「美金匯率多少」
- 「100 日幣換台幣」
- 「歐元匯率」

## API 測試

```bash
uv run python -c "
import asyncio
from voice_assistant.tools.exchange_rate import ExchangeRateTool

async def test():
    tool = ExchangeRateTool()
    result = await tool.execute(from_currency='USD', to_currency='TWD', amount=100)
    print(result)

asyncio.run(test())
"
```

## 常見問題

### Q: 為什麼匯率不是最新的？

Frankfurter API 使用歐洲中央銀行資料，僅於工作日更新。週末查詢會取得上一個工作日的匯率。

### Q: 如何新增更多貨幣？

在 `CURRENCY_ALIASES` 和 `CURRENCY_NAMES` 字典中新增對應項目。確保 Frankfurter API 支援該貨幣代碼。

### Q: API 逾時怎麼處理？

工具內建 10 秒逾時處理，會回傳友善錯誤訊息：「匯率服務暫時無法使用，請稍後再試」
