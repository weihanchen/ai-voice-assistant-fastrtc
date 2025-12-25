# Quickstart: Weather Query Tool

**Feature**: 002-weather-query
**Date**: 2025-12-25

## Prerequisites

- 已完成 001-fastrtc-voice-pipeline 功能
- Python 3.13 環境
- 網路連線（用於 Open-Meteo API）

## Installation

```bash
# 新增 httpx 相依套件
uv add httpx

# 更新 lock file
uv lock
```

## Quick Test

### 1. 測試 WeatherTool 獨立功能

```python
import asyncio
from voice_assistant.tools.weather import WeatherTool

async def main():
    tool = WeatherTool()

    # 基本查詢
    result = await tool.execute(city="台北")
    print(result.to_content())

    # 詳細查詢
    result = await tool.execute(city="高雄", include_details=True)
    print(result.to_content())

    # 測試錯誤處理
    result = await tool.execute(city="東京")
    print(result.to_content())

asyncio.run(main())
```

### 2. 整合 ToolRegistry

```python
from voice_assistant.tools.registry import ToolRegistry
from voice_assistant.tools.weather import WeatherTool

# 註冊工具
registry = ToolRegistry()
registry.register(WeatherTool())

# 確認註冊成功
print(registry.list_tools())  # ['get_weather']

# 取得 OpenAI tools 格式
tools = registry.get_openai_tools()
print(tools)
```

### 3. 語音測試

```bash
# 啟動應用
uv run python -m voice_assistant.main

# 開啟瀏覽器 http://localhost:7860
# 對著麥克風說：「台北天氣」
```

## Usage Examples

### 語音指令範例

| 語音輸入 | 預期回應 |
|----------|----------|
| 「台北天氣」 | 「台北目前氣溫 22 度，天氣多雲。」 |
| 「高雄現在天氣如何」 | 「高雄目前氣溫 25 度，天氣晴朗。」 |
| 「台中濕度多少」 | 「台中目前濕度為 70%。」 |
| 「東京天氣」 | 「抱歉，目前僅支援台灣主要城市...」 |

### 支援的城市

台北、新北、桃園、台中、台南、高雄、基隆、新竹、嘉義、屏東、宜蘭、花蓮、台東

## Running Tests

```bash
# 單元測試
uv run pytest tests/unit/test_weather_tool.py -v

# 所有測試
uv run pytest -v
```

## Troubleshooting

### API 連線失敗

```
Error: api_timeout
```

**解決方案**:
1. 確認網路連線正常
2. 檢查防火牆設定
3. 嘗試直接訪問 `https://api.open-meteo.com/v1/forecast?latitude=25&longitude=121&current=temperature_2m`

### 城市不支援

```
Error: unsupported_city
```

**解決方案**:
- 確認使用支援的城市名稱
- 嘗試使用標準名稱（如「台北」而非「北部」）

## Next Steps

1. 完成 `/speckit.tasks` 生成任務清單
2. 執行 `/speckit.implement` 開始實作
3. 測試語音端對端功能
