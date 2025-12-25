# Research: Weather Query Tool

**Feature**: 002-weather-query
**Date**: 2025-12-25

## Research Topics

### 1. Open-Meteo API 使用方式

**Decision**: 使用 Open-Meteo Forecast API 的 `current` 參數取得即時天氣

**Rationale**:
- 免費、無需 API Key、無速率限制（非商業用途）
- 支援全球經緯度查詢
- 回應時間 < 10ms（官方數據）
- 提供完整的即時天氣參數

**API 規格**:

| 項目 | 說明 |
|------|------|
| **Base URL** | `https://api.open-meteo.com/v1/forecast` |
| **Method** | GET |
| **認證** | 無需 |

**必要參數**:

| 參數 | 類型 | 說明 |
|------|------|------|
| `latitude` | float | 緯度（WGS84） |
| `longitude` | float | 經度（WGS84） |
| `current` | string | 欲查詢的即時天氣變數（逗號分隔） |

**可用的 current 變數**:

| 變數 | 說明 | 單位 |
|------|------|------|
| `temperature_2m` | 地表 2 公尺溫度 | °C |
| `relative_humidity_2m` | 相對濕度 | % |
| `apparent_temperature` | 體感溫度 | °C |
| `weather_code` | WMO 天氣代碼 | code |
| `wind_speed_10m` | 風速 | km/h |
| `wind_direction_10m` | 風向 | ° |
| `is_day` | 是否白天 | 0/1 |

**範例請求**:

```
GET https://api.open-meteo.com/v1/forecast?latitude=25.0330&longitude=121.5654&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m
```

**範例回應**:

```json
{
  "latitude": 25.03,
  "longitude": 121.5625,
  "current_units": {
    "temperature_2m": "°C",
    "relative_humidity_2m": "%",
    "apparent_temperature": "°C",
    "weather_code": "wmo code",
    "wind_speed_10m": "km/h"
  },
  "current": {
    "temperature_2m": 22.5,
    "relative_humidity_2m": 75,
    "apparent_temperature": 24.1,
    "weather_code": 3,
    "wind_speed_10m": 12.3
  }
}
```

**Alternatives Considered**:
- OpenWeatherMap：需要 API Key，有免費額度限制
- 中央氣象署 API：需申請、有使用限制
- AccuWeather：需要 API Key，商業授權

---

### 2. WMO Weather Code 對照表

**Decision**: 建立 WMO 代碼到繁體中文描述的對照表

**Rationale**:
- Open-Meteo 回傳 WMO 標準代碼
- 需轉換為口語化中文供 TTS 輸出

**對照表（常用代碼）**:

| Code | 英文描述 | 中文描述 |
|------|----------|----------|
| 0 | Clear sky | 晴朗 |
| 1 | Mainly clear | 晴時多雲 |
| 2 | Partly cloudy | 多雲 |
| 3 | Overcast | 陰天 |
| 45 | Fog | 霧 |
| 48 | Depositing rime fog | 濃霧 |
| 51 | Light drizzle | 小雨 |
| 53 | Moderate drizzle | 毛毛雨 |
| 55 | Dense drizzle | 細雨 |
| 61 | Slight rain | 小雨 |
| 63 | Moderate rain | 中雨 |
| 65 | Heavy rain | 大雨 |
| 71 | Slight snow | 小雪 |
| 73 | Moderate snow | 中雪 |
| 75 | Heavy snow | 大雪 |
| 80 | Slight rain showers | 陣雨 |
| 81 | Moderate rain showers | 陣雨 |
| 82 | Violent rain showers | 雷陣雨 |
| 95 | Thunderstorm | 雷雨 |
| 96 | Thunderstorm with slight hail | 雷雨伴隨冰雹 |
| 99 | Thunderstorm with heavy hail | 大雷雨伴隨冰雹 |

---

### 3. 台灣城市經緯度座標

**Decision**: 預建 13 個主要城市的經緯度對照表

**Rationale**:
- 避免動態地理編碼 API 呼叫
- 減少延遲與外部依賴
- 城市座標固定，適合靜態資料

**城市座標表**:

| 城市 | 緯度 | 經度 | 備註 |
|------|------|------|------|
| 台北 | 25.0330 | 121.5654 | 首都 |
| 新北 | 25.0120 | 121.4657 | 板橋區 |
| 桃園 | 24.9936 | 121.3010 | 桃園區 |
| 台中 | 24.1477 | 120.6736 | 西區 |
| 台南 | 22.9908 | 120.2133 | 中西區 |
| 高雄 | 22.6273 | 120.3014 | 前鎮區 |
| 基隆 | 25.1276 | 121.7392 | 中正區 |
| 新竹 | 24.8015 | 120.9718 | 北區 |
| 嘉義 | 23.4801 | 120.4491 | 東區 |
| 屏東 | 22.6690 | 120.4866 | 屏東市 |
| 宜蘭 | 24.7570 | 121.7533 | 宜蘭市 |
| 花蓮 | 23.9910 | 121.6114 | 花蓮市 |
| 台東 | 22.7583 | 121.1444 | 台東市 |

**城市別名支援**:

| 別名 | 對應城市 |
|------|----------|
| 台北市 | 台北 |
| 新北市 | 新北 |
| 桃園市 | 桃園 |
| 台中市 | 台中 |
| 台南市 | 台南 |
| 高雄市 | 高雄 |

---

### 4. HTTP Client 選擇

**Decision**: 使用 httpx 作為 HTTP 客戶端

**Rationale**:
- 原生支援 async/await，符合 `BaseTool.execute` 的 async 模式
- API 相容 requests，學習曲線低
- 內建逾時處理
- 已是 Python 社群主流選擇

**Alternatives Considered**:
- aiohttp：功能類似，但 API 較複雜
- requests：不支援 async
- urllib3：太底層，需額外封裝

---

### 5. 錯誤處理策略

**Decision**: 分層錯誤處理，回傳結構化錯誤訊息

**錯誤分類**:

| 錯誤類型 | 處理方式 | 回傳訊息 |
|----------|----------|----------|
| 城市不存在 | 工具層處理 | `{"error": "unsupported_city", "message": "目前不支援該城市..."}` |
| API 逾時 | httpx.TimeoutException | `{"error": "api_timeout", "message": "天氣服務暫時無法使用..."}` |
| API 錯誤 | HTTP status >= 400 | `{"error": "api_error", "message": "無法取得天氣資訊..."}` |
| 網路錯誤 | httpx.RequestError | `{"error": "network_error", "message": "網路連線異常..."}` |

**Rationale**:
- 結構化錯誤讓 LLM 可產生適當的口語化回應
- 不暴露技術細節給使用者
- 符合 Constitution IV. Safe Boundary 原則

---

## Summary

所有 NEEDS CLARIFICATION 已解決：

| 項目 | 決策 |
|------|------|
| Weather API | Open-Meteo Forecast API with `current` parameter |
| HTTP Client | httpx（async 支援） |
| 城市座標 | 靜態對照表（13 個主要城市） |
| 天氣描述 | WMO Code 對照繁體中文 |
| 錯誤處理 | 分層結構化回應 |

---

## Sources

- [Open-Meteo Documentation](https://open-meteo.com/en/docs)
- [Open-Meteo GitHub](https://github.com/open-meteo/open-meteo)
- [WMO Weather Codes](https://open-meteo.com/en/docs)
