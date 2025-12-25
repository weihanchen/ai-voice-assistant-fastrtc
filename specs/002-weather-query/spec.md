# Feature Specification: Weather Query Tool

**Feature Branch**: `002-weather-query`
**Created**: 2025-12-25
**Status**: Draft
**Input**: User description: "天氣查詢工具 - 使用者可透過語音詢問天氣，系統查詢 Open-Meteo API 並回應當前天氣狀況。支援台灣主要城市的天氣查詢。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 查詢城市目前天氣 (Priority: P1)

使用者透過語音詢問特定城市的天氣，系統辨識城市名稱後查詢天氣 API，並以語音回報目前的天氣狀況（溫度、天氣描述）。

**Why this priority**: 這是天氣查詢的核心功能，沒有此功能整個工具無法運作。使用者最常見的需求就是「現在天氣如何」。

**Independent Test**: 對著麥克風說「台北現在天氣如何」，系統在 5 秒內語音回應「台北目前氣溫 25 度，天氣晴朗」。

**Acceptance Scenarios**:

1. **Given** 系統處於待命狀態, **When** 使用者說「台北天氣」, **Then** 系統語音回應台北目前的溫度與天氣描述
2. **Given** 系統處於待命狀態, **When** 使用者說「高雄現在天氣如何」, **Then** 系統語音回應高雄目前的溫度與天氣描述
3. **Given** 系統處於待命狀態, **When** 使用者說「新竹的天氣怎麼樣」, **Then** 系統語音回應新竹目前的溫度與天氣描述

---

### User Story 2 - 處理無法識別的城市 (Priority: P2)

當使用者詢問不支援的城市或系統無法辨識的地名時，系統友善地告知使用者，並提示可支援的城市範圍。

**Why this priority**: 錯誤處理是良好使用者體驗的關鍵，避免使用者在無回應的情況下感到困惑。

**Independent Test**: 對著麥克風說「東京天氣」，系統回應「抱歉，目前僅支援台灣主要城市的天氣查詢，例如台北、高雄、台中等」。

**Acceptance Scenarios**:

1. **Given** 系統處於待命狀態, **When** 使用者詢問非台灣城市（如「東京天氣」）, **Then** 系統友善告知目前僅支援台灣城市
2. **Given** 系統處於待命狀態, **When** 使用者說出無法辨識的地名（如「ABCD天氣」）, **Then** 系統回應無法識別該城市並提供範例

---

### User Story 3 - 查詢天氣詳細資訊 (Priority: P3)

使用者可詢問更詳細的天氣資訊，如體感溫度、濕度、風速等。

**Why this priority**: 進階功能，在基本功能完成後可提供更豐富的資訊。

**Independent Test**: 對著麥克風說「台北濕度多少」，系統回應「台北目前濕度為 75%」。

**Acceptance Scenarios**:

1. **Given** 系統處於待命狀態, **When** 使用者詢問「台北濕度」, **Then** 系統語音回應目前濕度百分比
2. **Given** 系統處於待命狀態, **When** 使用者詢問「高雄風速」, **Then** 系統語音回應目前風速

---

### Edge Cases

- 當 Open-Meteo API 無回應或逾時時，系統回應「抱歉，目前無法取得天氣資訊，請稍後再試」
- 當使用者只說「天氣」而未指定城市時，系統詢問「請問您想查詢哪個城市的天氣？」
- 當使用者使用城市別名（如「北部」、「南部」）時，系統回應「請提供具體城市名稱，例如台北、高雄」

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 支援辨識台灣主要城市名稱（至少包含：台北、新北、桃園、台中、台南、高雄、基隆、新竹、嘉義、屏東、宜蘭、花蓮、台東）
- **FR-002**: 系統 MUST 透過 Open-Meteo API 查詢指定城市的即時天氣資料
- **FR-003**: 系統 MUST 以口語化繁體中文回應天氣資訊
- **FR-004**: 系統 MUST 在 API 查詢失敗時提供友善的錯誤訊息
- **FR-005**: 系統 MUST 將天氣查詢實作為 Tool，供 LLM 自動調用
- **FR-006**: 系統 MUST 支援基本天氣資訊回報（溫度、天氣描述）
- **FR-007**: 系統 SHOULD 支援進階天氣資訊（濕度、風速、體感溫度）

### Key Entities

- **City**: 城市資訊，包含城市名稱、經緯度座標（用於 API 查詢）
- **WeatherData**: 天氣資料，包含溫度、天氣描述、濕度、風速、體感溫度等
- **WeatherResponse**: 回應格式，包含查詢結果或錯誤訊息

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 從使用者說出城市名稱到系統開始語音回應，延遲不超過 5 秒
- **SC-002**: 系統正確辨識台灣主要城市名稱的成功率達 95% 以上
- **SC-003**: API 查詢失敗時，100% 提供友善錯誤訊息而非靜默或技術性錯誤
- **SC-004**: 天氣資訊回應內容符合口語化中文，使用者可自然理解

## Assumptions

- 使用者會以繁體中文詢問天氣
- 網路連線穩定，Open-Meteo API 可正常存取
- 使用者詢問的是「當前」天氣，不包含天氣預報功能
- 城市座標資料可預先建表，不需動態查詢

## Dependencies

- 001-fastrtc-voice-pipeline（語音輸入輸出管線）
- LLMClient（對話處理與 Tool 調用）
- Open-Meteo API（天氣資料來源）

## Out of Scope

- 天氣預報（明天、未來一週）
- 非台灣地區的天氣查詢
- 天氣警報或災害通知
- 歷史天氣資料查詢
