# Tasks: Stock Price Query

**Input**: Design documents from `/specs/004-stock-price-query/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 依據 constitution.md 品質要求，本功能需有單元測試與 mock 測試。

**Organization**: 任務依 User Story 分組，支援獨立實作與測試。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可平行執行（不同檔案、無依賴）
- **[Story]**: 所屬 User Story（US1, US2）
- 描述包含確切檔案路徑

---

## Phase 1: Setup（環境設置）

**Purpose**: 安裝依賴套件

- [x] T001 安裝 yfinance 依賴套件（執行 `uv add yfinance`）

---

## Phase 2: Foundational（基礎建設）

**Purpose**: 建立股票對照表與工具基礎結構

**⚠️ 重要**: 此階段必須完成後才能進行 User Story 實作

- [x] T002 建立台股對照表（台灣 50 成分股）於 src/voice_assistant/tools/stock_price.py
- [x] T003 [P] 建立美股對照表（S&P 500 前 30 大）於 src/voice_assistant/tools/stock_price.py
- [x] T004 [P] 建立股票顯示名稱對照表於 src/voice_assistant/tools/stock_price.py

**Checkpoint**: 對照表完成，可開始 User Story 實作

---

## Phase 3: User Story 1 - 查詢單一股票即時報價 (Priority: P1) 🎯 MVP

**Goal**: 使用者透過語音查詢股票價格，系統回覆即時報價

**Independent Test**: 語音詢問「台積電現在多少錢」或「Apple 股價」，系統正確回報股價

### Tests for User Story 1

- [x] T005 [P] [US1] 建立股票工具單元測試檔案 tests/unit/tools/test_stock_price.py
- [x] T006 [P] [US1] 撰寫 _resolve_stock 方法測試（台股中文、台股代碼、美股英文、美股中文）
- [x] T007 [P] [US1] 撰寫 execute 成功情境測試（mock yfinance 回應）

### Implementation for User Story 1

- [x] T008 [US1] 實作 StockPriceTool 類別基礎結構於 src/voice_assistant/tools/stock_price.py
- [x] T009 [US1] 實作 _resolve_stock 方法（股票名稱解析為代碼）於 src/voice_assistant/tools/stock_price.py
- [x] T010 [US1] 實作 _fetch_price 方法（呼叫 yfinance API）於 src/voice_assistant/tools/stock_price.py
- [x] T011 [US1] 實作 execute 方法（整合解析與查詢）於 src/voice_assistant/tools/stock_price.py
- [x] T012 [US1] 在 src/voice_assistant/tools/__init__.py 匯出 StockPriceTool 並註冊至 ToolRegistry
- [x] T013 [US1] 更新 src/voice_assistant/voice/pipeline.py 的 SYSTEM_PROMPT 加入股票查詢說明

**Checkpoint**: 此時應可成功查詢台股與美股價格，並透過語音回覆

---

## Phase 4: User Story 2 - 處理無法識別的股票 (Priority: P2)

**Goal**: 查詢失敗時提供友善的錯誤訊息

**Independent Test**: 語音詢問「小明公司股價」，系統回覆「抱歉，找不到這支股票」

### Tests for User Story 2

- [x] T014 [P] [US2] 撰寫不支援股票測試（unsupported_stock 錯誤）於 tests/unit/tools/test_stock_price.py
- [x] T015 [P] [US2] 撰寫 API 錯誤測試（api_error、timeout）於 tests/unit/tools/test_stock_price.py
- [x] T016 [P] [US2] 撰寫無報價資料測試（no_data 錯誤）於 tests/unit/tools/test_stock_price.py

### Implementation for User Story 2

- [x] T017 [US2] 實作 unsupported_stock 錯誤處理於 src/voice_assistant/tools/stock_price.py
- [x] T018 [US2] 實作 API 逾時處理（asyncio.TimeoutError）於 src/voice_assistant/tools/stock_price.py
- [x] T019 [US2] 實作 API 錯誤處理（一般 Exception）於 src/voice_assistant/tools/stock_price.py
- [x] T020 [US2] 實作無報價資料處理（price is None）於 src/voice_assistant/tools/stock_price.py

**Checkpoint**: 此時所有錯誤情境皆有友善的中文錯誤訊息

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 最終驗證與整合

- [x] T021 執行所有單元測試確認通過（`uv run pytest tests/unit/tools/test_stock_price.py -v`）
- [x] T022 [P] 執行 Ruff 檢查與格式化（`uv run ruff check --fix && uv run ruff format`）
- [x] T023 [P] 執行 Pyright 型別檢查（`uv run pyright src/voice_assistant/tools/stock_price.py`）
- [x] T024 整合測試：啟動服務並實際語音測試股票查詢

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 無依賴，可立即開始
- **Foundational (Phase 2)**: 依賴 Setup 完成，阻擋所有 User Story
- **User Story 1 (Phase 3)**: 依賴 Foundational 完成
- **User Story 2 (Phase 4)**: 依賴 Foundational 完成，可與 US1 平行（但建議先完成 US1）
- **Polish (Phase 5)**: 依賴所有 User Story 完成

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完成後可開始，無依賴其他 Story
- **User Story 2 (P2)**: Foundational 完成後可開始，建議 US1 完成後再進行（共用 execute 方法）

### Within Each User Story

- 測試需先撰寫並確認失敗
- 實作順序：解析方法 → API 呼叫 → execute 整合 → 註冊與 PROMPT
- 每完成一個任務即可 commit

### Parallel Opportunities

- T003, T004 可與 T002 平行執行（不同對照表）
- T005, T006, T007 可平行執行（獨立測試案例）
- T014, T015, T016 可平行執行（獨立測試案例）
- T022, T023 可平行執行（不同檢查工具）

---

## Parallel Example: User Story 1

```bash
# 平行執行所有 US1 測試任務：
Task: "T005 [P] [US1] 建立股票工具單元測試檔案"
Task: "T006 [P] [US1] 撰寫 _resolve_stock 方法測試"
Task: "T007 [P] [US1] 撰寫 execute 成功情境測試"

# 平行執行對照表任務：
Task: "T002 建立台股對照表"
Task: "T003 [P] 建立美股對照表"
Task: "T004 [P] 建立股票顯示名稱對照表"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup（安裝 yfinance）
2. 完成 Phase 2: Foundational（對照表）
3. 完成 Phase 3: User Story 1（核心查詢功能）
4. **驗證**: 語音測試「台積電股價」
5. 可部署/展示 MVP

### Incremental Delivery

1. Setup + Foundational → 基礎完成
2. User Story 1 → 獨立測試 → 部署/展示（MVP!）
3. User Story 2 → 獨立測試 → 部署/展示
4. 每個 Story 都能獨立增加價值

---

## Notes

- [P] 標記 = 不同檔案、無依賴
- [Story] 標籤對應 spec.md 中的 User Story
- 每個 User Story 應可獨立完成與測試
- 測試需確認失敗後再實作
- 每完成一個任務或邏輯群組即 commit
- yfinance 是同步套件，需用 `asyncio.to_thread()` 包裝為非同步
