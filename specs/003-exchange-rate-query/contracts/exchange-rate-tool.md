# Contract: ExchangeRateTool

## Overview

`ExchangeRateTool` 是匯率查詢工具，透過 Frankfurter API 提供即時匯率查詢與貨幣換算功能。

## Class Definition

```python
class ExchangeRateTool(BaseTool):
    """匯率查詢工具"""

    @property
    def name(self) -> str:
        """工具名稱"""
        return "get_exchange_rate"

    @property
    def description(self) -> str:
        """工具描述"""
        return (
            "查詢貨幣匯率或進行金額換算。"
            "支援美金、日幣、歐元、人民幣、韓元、港幣、英鎊、澳幣與新台幣。"
        )

    @property
    def parameters(self) -> dict:
        """OpenAI Function Calling 參數定義"""
        return {
            "type": "object",
            "properties": {
                "from_currency": {
                    "type": "string",
                    "description": "來源貨幣（中文名稱或代碼，如「美金」或「USD」）"
                },
                "to_currency": {
                    "type": "string",
                    "description": "目標貨幣（預設為新台幣 TWD）",
                    "default": "TWD"
                },
                "amount": {
                    "type": "number",
                    "description": "換算金額（預設為 1）",
                    "default": 1
                }
            },
            "required": ["from_currency"]
        }
```

---

## Method: `execute`

### Signature

```python
async def execute(
    self,
    from_currency: str,
    to_currency: str = "TWD",
    amount: float = 1.0
) -> ToolResult:
```

### Parameters

| 參數 | 型別 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `from_currency` | str | ✅ | - | 來源貨幣（中文或 ISO 代碼） |
| `to_currency` | str | ❌ | `"TWD"` | 目標貨幣 |
| `amount` | float | ❌ | `1.0` | 換算金額 |

### Return Value

#### Success Case

```python
ToolResult.ok({
    "from_currency": "USD",
    "from_amount": 100,
    "to_currency": "TWD",
    "to_amount": 3250.0,
    "rate": 32.5,
    "queried_at": "2025-12-26T12:00:00+00:00"
})
```

#### Error Cases

| 錯誤代碼 | 觸發條件 | 回傳訊息 |
|----------|----------|----------|
| `unsupported_currency` | 貨幣不在支援清單 | `"unsupported_currency: 目前僅支援主要國際貨幣，例如美金、日幣、歐元、人民幣等"` |
| `same_currency` | 來源與目標相同 | `"same_currency: 您查詢的是相同貨幣，無需換算"` |
| `invalid_amount` | 金額 ≤ 0 | `"invalid_amount: 請提供有效的金額"` |
| `api_timeout` | API 逾時 | `"api_timeout: 匯率服務暫時無法使用，請稍後再試"` |
| `network_error` | 網路錯誤 | `"network_error: 網路連線異常，請檢查網路狀態"` |
| `api_error` | API 回傳錯誤 | `"api_error: 無法取得匯率資訊，請稍後再試"` |

---

## Private Methods

### `_resolve_currency`

```python
def _resolve_currency(self, currency: str) -> str | None:
    """
    解析貨幣名稱為 ISO 4217 代碼。

    Args:
        currency: 使用者輸入的貨幣名稱

    Returns:
        ISO 4217 代碼，或 None 表示不支援
    """
```

### `_fetch_exchange_rate`

```python
async def _fetch_exchange_rate(
    self,
    from_code: str,
    to_code: str,
    amount: float = 1.0
) -> dict:
    """
    呼叫 Frankfurter API 查詢匯率。

    Args:
        from_code: 來源貨幣代碼
        to_code: 目標貨幣代碼
        amount: 換算金額

    Returns:
        API 回應 dict

    Raises:
        httpx.TimeoutException: API 逾時
        httpx.RequestError: 網路錯誤
        ValueError: API 回應錯誤
    """
```

---

## OpenAI Function Calling Format

```python
def to_openai_tool(self) -> dict:
    """轉換為 OpenAI tools 參數格式"""
    return {
        "type": "function",
        "function": {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    }
```

### Example Tool Call

**User Input**: 「100 美金換台幣多少」

**LLM Tool Call**:
```json
{
  "name": "get_exchange_rate",
  "arguments": {
    "from_currency": "美金",
    "to_currency": "TWD",
    "amount": 100
  }
}
```

**Tool Response**:
```json
{
  "success": true,
  "data": {
    "from_currency": "USD",
    "from_amount": 100,
    "to_currency": "TWD",
    "to_amount": 3250.0,
    "rate": 32.5,
    "queried_at": "2025-12-26T12:00:00+00:00"
  }
}
```

**LLM Final Response**: 「100 美元約可兌換 3,250 新台幣，目前匯率為 1 美元兌 32.5 新台幣。」

---

## Constants

### FRANKFURTER_BASE_URL

```python
FRANKFURTER_BASE_URL = "https://api.frankfurter.app"
```

### API_TIMEOUT

```python
API_TIMEOUT = 10.0  # seconds
```

### CURRENCY_ALIASES

```python
CURRENCY_ALIASES: dict[str, str] = {
    "美金": "USD", "美元": "USD", "美刀": "USD", "USD": "USD",
    "日幣": "JPY", "日圓": "JPY", "日元": "JPY", "JPY": "JPY",
    "歐元": "EUR", "EUR": "EUR",
    "人民幣": "CNY", "人民币": "CNY", "CNY": "CNY",
    "韓元": "KRW", "韓幣": "KRW", "KRW": "KRW",
    "港幣": "HKD", "港元": "HKD", "HKD": "HKD",
    "英鎊": "GBP", "GBP": "GBP",
    "澳幣": "AUD", "澳元": "AUD", "AUD": "AUD",
    "台幣": "TWD", "新台幣": "TWD", "TWD": "TWD",
}
```

### CURRENCY_NAMES

```python
CURRENCY_NAMES: dict[str, str] = {
    "USD": "美元", "JPY": "日圓", "EUR": "歐元",
    "CNY": "人民幣", "KRW": "韓元", "HKD": "港幣",
    "GBP": "英鎊", "AUD": "澳幣", "TWD": "新台幣",
}
```

---

## Integration

### Registration in Composition Root

```python
# src/voice_assistant/voice/handlers/reply_on_pause.py

from voice_assistant.tools import ToolRegistry, WeatherTool, ExchangeRateTool

# 初始化工具註冊表（Composition Root）
tool_registry = ToolRegistry()
tool_registry.register(WeatherTool())
tool_registry.register(ExchangeRateTool())  # 新增
```

### Export in Package

```python
# src/voice_assistant/tools/__init__.py

from voice_assistant.tools.exchange_rate import ExchangeRateTool

__all__ = ["BaseTool", "ToolRegistry", "ToolResult", "WeatherTool", "ExchangeRateTool"]
```
