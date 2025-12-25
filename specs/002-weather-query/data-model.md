# Data Model: Weather Query Tool

**Feature**: 002-weather-query
**Date**: 2025-12-25

## Overview

天氣查詢工具的資料模型，定義城市資訊、天氣資料、API 回應等結構。

---

## Entities

### 1. City（城市）

**Description**: 台灣主要城市的靜態資料，包含經緯度座標供 API 查詢使用。

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | Yes | 城市標準名稱（如「台北」） |
| `latitude` | float | Yes | 緯度（WGS84） |
| `longitude` | float | Yes | 經度（WGS84） |
| `aliases` | list[str] | No | 城市別名（如「台北市」） |

**Example**:

```python
City(
    name="台北",
    latitude=25.0330,
    longitude=121.5654,
    aliases=["台北市"]
)
```

**Validation Rules**:
- `latitude` 範圍：21.0 ~ 26.0（台灣範圍）
- `longitude` 範圍：119.0 ~ 123.0（台灣範圍）
- `name` 不可為空

---

### 2. WeatherCode（天氣代碼）

**Description**: WMO 標準天氣代碼與中文描述的對照。

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | int | Yes | WMO 天氣代碼（0-99） |
| `description_zh` | str | Yes | 繁體中文描述 |

**Example**:

```python
WeatherCode(code=0, description_zh="晴朗")
WeatherCode(code=61, description_zh="小雨")
```

---

### 3. WeatherData（天氣資料）

**Description**: 從 Open-Meteo API 取得的即時天氣資料。

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `city` | str | Yes | 查詢城市名稱 |
| `temperature` | float | Yes | 溫度（°C） |
| `apparent_temperature` | float | No | 體感溫度（°C） |
| `humidity` | int | No | 相對濕度（%） |
| `weather_code` | int | Yes | WMO 天氣代碼 |
| `weather_description` | str | Yes | 天氣描述（中文） |
| `wind_speed` | float | No | 風速（km/h） |
| `is_day` | bool | No | 是否為白天 |
| `queried_at` | datetime | Yes | 查詢時間 |

**Example**:

```python
WeatherData(
    city="台北",
    temperature=22.5,
    apparent_temperature=24.1,
    humidity=75,
    weather_code=3,
    weather_description="陰天",
    wind_speed=12.3,
    is_day=True,
    queried_at=datetime(2025, 12, 25, 14, 30, 0)
)
```

**Validation Rules**:
- `temperature` 範圍：-20.0 ~ 50.0（合理溫度範圍）
- `humidity` 範圍：0 ~ 100
- `weather_code` 範圍：0 ~ 99

---

### 4. WeatherQueryInput（查詢輸入）

**Description**: 天氣查詢工具的輸入參數，供 LLM Function Calling 使用。

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `city` | str | Yes | 城市名稱 |
| `include_details` | bool | No | 是否包含詳細資訊（濕度、風速等），預設 False |

**Example**:

```python
WeatherQueryInput(city="台北", include_details=True)
```

**JSON Schema（OpenAI tools 格式）**:

```json
{
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
```

---

### 5. WeatherResponse（查詢回應）

**Description**: 天氣查詢的結果，成功時包含天氣資料，失敗時包含錯誤資訊。

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | bool | Yes | 查詢是否成功 |
| `data` | WeatherData | No | 天氣資料（成功時） |
| `error` | str | No | 錯誤代碼（失敗時） |
| `message` | str | No | 錯誤訊息（失敗時） |

**Success Example**:

```python
WeatherResponse(
    success=True,
    data=WeatherData(...)
)
```

**Error Example**:

```python
WeatherResponse(
    success=False,
    error="unsupported_city",
    message="目前不支援該城市的天氣查詢，請提供台灣主要城市名稱"
)
```

---

## Error Codes

| Code | Description | User Message |
|------|-------------|--------------|
| `unsupported_city` | 城市不在支援列表中 | 目前僅支援台灣主要城市... |
| `api_timeout` | API 請求逾時 | 天氣服務暫時無法使用... |
| `api_error` | API 回傳錯誤 | 無法取得天氣資訊... |
| `network_error` | 網路連線問題 | 網路連線異常... |

---

## Relationships

```
┌──────────────────┐
│ WeatherQueryInput│  ─── 輸入 ───┐
└──────────────────┘              │
                                  ▼
┌──────────────────┐     ┌──────────────────┐
│      City        │ ──► │   WeatherTool    │
│ (static lookup)  │     │   (execute)      │
└──────────────────┘     └────────┬─────────┘
                                  │
                                  ▼
┌──────────────────┐     ┌──────────────────┐
│   WeatherCode    │ ◄── │   WeatherData    │
│ (code → desc)    │     │ (API response)   │
└──────────────────┘     └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ WeatherResponse  │
                         │ (ToolResult)     │
                         └──────────────────┘
```

---

## State Transitions

天氣查詢為無狀態操作，每次查詢獨立處理，無狀態轉移需求。

---

## Storage

無持久化需求：
- 城市座標為靜態常數
- 天氣代碼對照為靜態常數
- 查詢結果不需儲存
