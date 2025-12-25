# Contract: Weather Tool

**Date**: 2025-12-25
**Feature**: 002-weather-query

## Overview

天氣查詢工具契約，定義 `WeatherTool` 類別的介面規範。

---

## Class Definition

```python
from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult

class WeatherTool(BaseTool):
    """
    天氣查詢工具

    查詢台灣主要城市的即時天氣資訊。
    """

    @property
    def name(self) -> str:
        """工具名稱"""
        return "get_weather"

    @property
    def description(self) -> str:
        """工具描述（供 LLM 判斷何時調用）"""
        return (
            "查詢台灣城市的即時天氣資訊。"
            "可查詢溫度、天氣狀況、濕度、風速等。"
            "支援的城市：台北、新北、桃園、台中、台南、高雄、"
            "基隆、新竹、嘉義、屏東、宜蘭、花蓮、台東。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON Schema 參數定義"""
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "要查詢的城市名稱，例如：台北、高雄、台中"
                },
                "include_details": {
                    "type": "boolean",
                    "description": "是否包含詳細資訊（濕度、風速、體感溫度）",
                    "default": False
                }
            },
            "required": ["city"]
        }

    async def execute(
        self,
        city: str,
        include_details: bool = False
    ) -> ToolResult:
        """
        執行天氣查詢

        Args:
            city: 城市名稱
            include_details: 是否包含詳細資訊

        Returns:
            ToolResult: 成功時包含天氣資料，失敗時包含錯誤訊息
        """
        ...
```

---

## OpenAI Function Calling Format

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "查詢台灣城市的即時天氣資訊。可查詢溫度、天氣狀況、濕度、風速等。支援的城市：台北、新北、桃園、台中、台南、高雄、基隆、新竹、嘉義、屏東、宜蘭、花蓮、台東。",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "要查詢的城市名稱，例如：台北、高雄、台中"
        },
        "include_details": {
          "type": "boolean",
          "description": "是否包含詳細資訊（濕度、風速、體感溫度）",
          "default": false
        }
      },
      "required": ["city"]
    }
  }
}
```

---

## Response Format

### Success Response (Basic)

```python
ToolResult.ok({
    "city": "台北",
    "temperature": 22.5,
    "weather": "多雲",
    "queried_at": "2025-12-25T14:30:00"
})
```

**LLM 轉換範例**:
> 「台北目前氣溫 22.5 度，天氣多雲。」

### Success Response (With Details)

```python
ToolResult.ok({
    "city": "台北",
    "temperature": 22.5,
    "apparent_temperature": 24.1,
    "humidity": 75,
    "weather": "多雲",
    "wind_speed": 12.3,
    "queried_at": "2025-12-25T14:30:00"
})
```

**LLM 轉換範例**:
> 「台北目前氣溫 22.5 度，體感溫度 24.1 度，天氣多雲。濕度 75%，風速每小時 12.3 公里。」

### Error Response

```python
ToolResult.fail("unsupported_city: 目前僅支援台灣主要城市的天氣查詢")
```

**LLM 轉換範例**:
> 「抱歉，目前僅支援台灣主要城市的天氣查詢，例如台北、高雄、台中等。」

---

## Supported Cities

| 城市 | 別名 |
|------|------|
| 台北 | 台北市 |
| 新北 | 新北市 |
| 桃園 | 桃園市 |
| 台中 | 台中市 |
| 台南 | 台南市 |
| 高雄 | 高雄市 |
| 基隆 | 基隆市 |
| 新竹 | 新竹市、新竹縣 |
| 嘉義 | 嘉義市、嘉義縣 |
| 屏東 | 屏東縣 |
| 宜蘭 | 宜蘭縣 |
| 花蓮 | 花蓮縣 |
| 台東 | 台東縣 |

---

## Error Handling

| 錯誤情況 | ToolResult | LLM 回應 |
|----------|------------|----------|
| 城市不支援 | `fail("unsupported_city: ...")` | 告知僅支援台灣城市，提供範例 |
| API 逾時 | `fail("api_timeout: ...")` | 請求稍後再試 |
| API 錯誤 | `fail("api_error: ...")` | 無法取得天氣資訊 |
| 網路錯誤 | `fail("network_error: ...")` | 網路連線異常 |

---

## Usage Example

### Registration

```python
from voice_assistant.tools.registry import ToolRegistry
from voice_assistant.tools.weather import WeatherTool

registry = ToolRegistry()
registry.register(WeatherTool())
```

### LLM Integration

```python
# 取得所有工具的 OpenAI 格式
tools = registry.get_openai_tools()

# LLM 回傳 tool_call 時執行
result = await registry.execute("get_weather", {"city": "台北"})
```

---

## Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestWeatherTool:

    @pytest.fixture
    def weather_tool(self):
        from voice_assistant.tools.weather import WeatherTool
        return WeatherTool()

    def test_implements_base_tool(self, weather_tool):
        """驗證實作 BaseTool"""
        assert hasattr(weather_tool, 'name')
        assert hasattr(weather_tool, 'description')
        assert hasattr(weather_tool, 'parameters')
        assert hasattr(weather_tool, 'execute')

    def test_name(self, weather_tool):
        """驗證工具名稱"""
        assert weather_tool.name == "get_weather"

    def test_parameters_schema(self, weather_tool):
        """驗證參數 schema"""
        params = weather_tool.parameters
        assert params["type"] == "object"
        assert "city" in params["properties"]
        assert "city" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_success(self, weather_tool):
        """測試成功查詢"""
        with patch.object(weather_tool, '_fetch_weather') as mock:
            mock.return_value = {...}
            result = await weather_tool.execute(city="台北")
            assert result.success is True
            assert "temperature" in result.data

    @pytest.mark.asyncio
    async def test_execute_unsupported_city(self, weather_tool):
        """測試不支援的城市"""
        result = await weather_tool.execute(city="東京")
        assert result.success is False
        assert "unsupported_city" in result.error
```

---

## Dependencies

- `httpx`: HTTP 客戶端（async）
- `voice_assistant.tools.base.BaseTool`: 基底類別
- `voice_assistant.tools.schemas.ToolResult`: 結果結構
