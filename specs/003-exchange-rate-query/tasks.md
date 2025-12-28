# Tasks: Exchange Rate Query Tool

**Input**: Design documents from `/specs/003-exchange-rate-query/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 專案相依套件確認

- [x] T001 確認 httpx 已在 pyproject.toml 中（002-weather-query 已新增）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 建立 ExchangeRateTool 核心常數與基礎結構

**⚠️ CRITICAL**: 所有 User Story 依賴此階段完成

- [x] T002 建立 CURRENCY_ALIASES 貨幣別名對照表於 src/voice_assistant/tools/exchange_rate.py
- [x] T003 建立 CURRENCY_NAMES 貨幣顯示名稱對照表於 src/voice_assistant/tools/exchange_rate.py
- [x] T004 建立 EXCHANGE_RATE_API_BASE_URL 和 API_TIMEOUT 常數於 src/voice_assistant/tools/exchange_rate.py

**Checkpoint**: 基礎常數建立完成，可開始實作 User Story

---

## Phase 3: User Story 1 - 查詢貨幣匯率 (Priority: P1) 🎯 MVP

**Goal**: 使用者可透過語音詢問貨幣匯率，系統回應即時匯率

**Independent Test**: 對著麥克風說「美金匯率多少」，系統在 5 秒內語音回應匯率

### Tests for User Story 1

- [x] T005 [P] [US1] 建立 Mock API 回應資料於 tests/fixtures/mock_exchange_rate.py
- [x] T006 [P] [US1] 建立 ExchangeRateTool 屬性測試於 tests/unit/test_exchange_rate_tool.py
- [x] T007 [P] [US1] 建立 _resolve_currency 方法測試於 tests/unit/test_exchange_rate_tool.py

### Implementation for User Story 1

- [x] T008 [US1] 實作 ExchangeRateTool 類別骨架（name, description, parameters）於 src/voice_assistant/tools/exchange_rate.py
- [x] T009 [US1] 實作 _resolve_currency 方法於 src/voice_assistant/tools/exchange_rate.py
- [x] T010 [US1] 實作 _fetch_exchange_rate 方法（呼叫 ExchangeRate-API）於 src/voice_assistant/tools/exchange_rate.py
- [x] T011 [US1] 實作 execute 方法基本匯率查詢（amount=1）於 src/voice_assistant/tools/exchange_rate.py
- [x] T012 [US1] 新增 ExchangeRateTool 匯出於 src/voice_assistant/tools/__init__.py
- [x] T013 [US1] 註冊 ExchangeRateTool 於 src/voice_assistant/voice/handlers/reply_on_pause.py
- [x] T014 [US1] 建立匯率查詢成功測試於 tests/unit/test_exchange_rate_tool.py

**Checkpoint**: User Story 1 完成，可獨立測試基本匯率查詢功能

---

## Phase 4: User Story 2 - 貨幣金額換算 (Priority: P2)

**Goal**: 使用者可指定金額進行貨幣換算

**Independent Test**: 對著麥克風說「100 美金換台幣」，系統回應換算結果

### Tests for User Story 2

- [x] T015 [P] [US2] 建立金額換算測試於 tests/unit/test_exchange_rate_tool.py
- [x] T016 [P] [US2] 建立雙向換算測試（TWD→USD）於 tests/unit/test_exchange_rate_tool.py

### Implementation for User Story 2

- [x] T017 [US2] 擴充 execute 方法支援 amount 參數於 src/voice_assistant/tools/exchange_rate.py
- [x] T018 [US2] 實作雙向換算邏輯（外幣→TWD、TWD→外幣）於 src/voice_assistant/tools/exchange_rate.py
- [x] T019 [US2] 新增無效金額驗證（≤0）於 src/voice_assistant/tools/exchange_rate.py
- [x] T020 [US2] 新增相同貨幣驗證於 src/voice_assistant/tools/exchange_rate.py

**Checkpoint**: User Story 2 完成，可獨立測試金額換算功能

---

## Phase 5: User Story 3 - 處理不支援的貨幣 (Priority: P3)

**Goal**: 友善處理不支援的貨幣查詢

**Independent Test**: 對著麥克風說「比特幣匯率」，系統回應不支援訊息

### Tests for User Story 3

- [x] T021 [P] [US3] 建立不支援貨幣錯誤處理測試於 tests/unit/test_exchange_rate_tool.py
- [x] T022 [P] [US3] 建立 API 錯誤處理測試（timeout, network error）於 tests/unit/test_exchange_rate_tool.py

### Implementation for User Story 3

- [x] T023 [US3] 實作不支援貨幣錯誤回應於 src/voice_assistant/tools/exchange_rate.py
- [x] T024 [US3] 實作 API 逾時錯誤處理於 src/voice_assistant/tools/exchange_rate.py
- [x] T025 [US3] 實作網路錯誤處理於 src/voice_assistant/tools/exchange_rate.py
- [x] T026 [US3] 實作 API 回應驗證（result, rates 欄位）於 src/voice_assistant/tools/exchange_rate.py

**Checkpoint**: User Story 3 完成，錯誤處理機制完整

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 程式碼品質與最終驗證

- [x] T027 執行 ruff check 並修復問題
- [x] T028 執行 ruff format 格式化程式碼
- [x] T029 執行 pytest 確認所有測試通過
- [x] T030 更新 AGENTS.md 新增 ExchangeRateTool 資訊

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - 確認相依套件
- **Foundational (Phase 2)**: Depends on Setup - 建立常數
- **User Stories (Phase 3-5)**: Depends on Foundational
- **Polish (Phase 6)**: Depends on all User Stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - 核心匯率查詢
- **User Story 2 (P2)**: Can start after Phase 2 - 金額換算（獨立於 US1）
- **User Story 3 (P3)**: Can start after Phase 2 - 錯誤處理（獨立於 US1, US2）

### Parallel Opportunities

**Phase 2 並行**:
- T002, T003, T004 可並行（同一檔案不同區塊）

**Phase 3 (US1) 並行**:
- T005, T006, T007 可並行（測試檔案）

**Phase 4 (US2) 並行**:
- T015, T016 可並行（測試）

**Phase 5 (US3) 並行**:
- T021, T022 可並行（測試）

---

## Parallel Example: User Story 1

```bash
# 並行建立測試檔案：
Task: "T005 [P] [US1] 建立 Mock API 回應資料於 tests/fixtures/mock_exchange_rate.py"
Task: "T006 [P] [US1] 建立 ExchangeRateTool 屬性測試於 tests/unit/test_exchange_rate_tool.py"
Task: "T007 [P] [US1] 建立 _resolve_currency 方法測試於 tests/unit/test_exchange_rate_tool.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: 測試「美金匯率多少」語音查詢
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → 基礎建立
2. User Story 1 → 基本匯率查詢 (MVP!)
3. User Story 2 → 金額換算
4. User Story 3 → 錯誤處理完善
5. Polish → 程式碼品質確認

---

## Notes

- [P] tasks = 不同檔案，無相依性
- [Story] label 對應 spec.md 中的 User Story
- 每個 User Story 可獨立完成和測試
- 遵循 WeatherTool 實作模式（參考 002-weather-query）
- API Base URL: `https://open.er-api.com/v6/latest`
