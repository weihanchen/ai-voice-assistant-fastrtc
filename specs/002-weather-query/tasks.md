# Tasks: Weather Query Tool

**Input**: Design documents from `/specs/002-weather-query/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/weather-tool.md

**Tests**: Constitution 要求每個 Tool 必須有單元測試（Quality Gates），因此包含測試任務。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/voice_assistant/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 新增相依套件與基礎設定

- [x] T001 新增 httpx 相依套件至 pyproject.toml
- [x] T002 [P] 建立天氣 API mock fixtures 目錄結構 tests/fixtures/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立所有 User Story 共用的基礎元件

**⚠️ CRITICAL**: 城市座標對照表、WMO 代碼對照表必須先完成，所有 User Story 都依賴這些資料

- [x] T003 建立台灣城市經緯度對照表常數 in src/voice_assistant/tools/weather.py（TAIWAN_CITIES dict）
- [x] T004 [P] 建立 WMO 天氣代碼中文對照表常數 in src/voice_assistant/tools/weather.py（WEATHER_CODES dict）
- [x] T005 [P] 建立城市別名對照表常數 in src/voice_assistant/tools/weather.py（CITY_ALIASES dict）

**Checkpoint**: 基礎資料結構完成 - User Story 實作可以開始

---

## Phase 3: User Story 1 - 查詢城市目前天氣 (Priority: P1) 🎯 MVP

**Goal**: 使用者說「台北天氣」，系統語音回應台北目前的溫度與天氣描述

**Independent Test**: 對著麥克風說「台北現在天氣如何」，系統在 5 秒內語音回應「台北目前氣溫 25 度，天氣晴朗」

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T006 [P] [US1] 建立 WeatherTool 單元測試骨架 in tests/unit/test_weather_tool.py
- [x] T007 [P] [US1] 建立 Open-Meteo API mock 資料 in tests/fixtures/mock_weather.py

### Implementation for User Story 1

- [x] T008 [US1] 建立 WeatherTool 類別骨架 in src/voice_assistant/tools/weather.py（name, description, parameters properties）
- [x] T009 [US1] 實作城市名稱解析邏輯 in src/voice_assistant/tools/weather.py（_resolve_city method）
- [x] T010 [US1] 實作 Open-Meteo API 呼叫邏輯 in src/voice_assistant/tools/weather.py（_fetch_weather method）
- [x] T011 [US1] 實作 WMO 代碼轉換邏輯 in src/voice_assistant/tools/weather.py（_get_weather_description method）
- [x] T012 [US1] 實作 execute() 方法（基本天氣查詢）in src/voice_assistant/tools/weather.py
- [x] T013 [US1] 更新 tools/__init__.py 匯出 WeatherTool
- [x] T014 [US1] 在 VoicePipeline 註冊 WeatherTool 到 ToolRegistry（更新 pipeline.py）

**Checkpoint**: User Story 1 完成 - 可獨立測試基本天氣查詢功能

---

## Phase 4: User Story 2 - 處理無法識別的城市 (Priority: P2)

**Goal**: 當使用者詢問不支援的城市時，系統友善告知並提示可支援的城市範圍

**Independent Test**: 對著麥克風說「東京天氣」，系統回應「抱歉，目前僅支援台灣主要城市的天氣查詢，例如台北、高雄、台中等」

### Tests for User Story 2

- [x] T015 [P] [US2] 新增不支援城市測試案例 in tests/unit/test_weather_tool.py（test_execute_unsupported_city）
- [x] T016 [P] [US2] 新增無法辨識城市測試案例 in tests/unit/test_weather_tool.py（test_execute_unrecognized_city）

### Implementation for User Story 2

- [x] T017 [US2] 增強 _resolve_city 方法處理不支援城市 in src/voice_assistant/tools/weather.py
- [x] T018 [US2] 實作友善錯誤訊息格式 in src/voice_assistant/tools/weather.py（unsupported_city error）

**Checkpoint**: User Story 2 完成 - 錯誤處理功能可獨立測試

---

## Phase 5: User Story 3 - 查詢天氣詳細資訊 (Priority: P3)

**Goal**: 使用者可詢問濕度、風速、體感溫度等詳細資訊

**Independent Test**: 對著麥克風說「台北濕度多少」，系統回應「台北目前濕度為 75%」

### Tests for User Story 3

- [x] T019 [P] [US3] 新增詳細資訊查詢測試案例 in tests/unit/test_weather_tool.py（test_execute_with_details）

### Implementation for User Story 3

- [x] T020 [US3] 擴展 _fetch_weather 方法取得詳細資訊 in src/voice_assistant/tools/weather.py（humidity, wind_speed, apparent_temperature）
- [x] T021 [US3] 更新 execute() 方法支援 include_details 參數 in src/voice_assistant/tools/weather.py
- [x] T022 [US3] 更新回應格式包含詳細資訊 in src/voice_assistant/tools/weather.py

**Checkpoint**: User Story 3 完成 - 詳細天氣查詢功能可獨立測試

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 整合驗證與品質確保

- [x] T023 新增 API 逾時與網路錯誤處理測試 in tests/unit/test_weather_tool.py
- [x] T024 [P] 實作 API 逾時處理 in src/voice_assistant/tools/weather.py（httpx.TimeoutException）
- [x] T025 [P] 實作網路錯誤處理 in src/voice_assistant/tools/weather.py（httpx.RequestError）
- [x] T026 執行 ruff check 與 ruff format 確保程式碼品質
- [x] T027 執行完整測試套件 uv run pytest（24 passed）
- [x] T028 執行 quickstart.md 驗證流程（實作完成，待實際語音測試）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 error handling path
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Extends US1 with additional data

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T001 (httpx) ─┬─► Phase 2
T002 (fixtures) ─┘
```

**Phase 2 (Foundational)**:
```
T003 (cities) ────┬─► Phase 3
T004 (weather codes) ─┤
T005 (aliases) ───────┘
```

**Phase 3 (US1 Tests)**:
```
T006 (test skeleton) ─┬─► T008 (implementation)
T007 (mock data) ─────┘
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T005)
3. Complete Phase 3: User Story 1 (T006-T014)
4. **STOP and VALIDATE**: 測試「台北天氣」語音查詢
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP 完成！**
3. Add User Story 2 → Test error handling → 錯誤處理完善
4. Add User Story 3 → Test detailed queries → 完整功能
5. Polish → 品質確保

---

## Summary

| 項目 | 數量 |
|------|------|
| **Total Tasks** | 28 |
| **Setup Phase** | 2 |
| **Foundational Phase** | 3 |
| **User Story 1 (P1)** | 9 |
| **User Story 2 (P2)** | 4 |
| **User Story 3 (P3)** | 4 |
| **Polish Phase** | 6 |

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1) = 14 tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
