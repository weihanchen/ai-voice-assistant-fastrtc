# 任務清單：AI Voice Assistant 核心架構

**輸入**：設計文件位於 `/specs/000-ai-voice-assistant/`
**前置條件**：plan.md、spec.md、data-model.md、contracts/

**測試**：包含單元測試任務（spec.md 成功標準要求）

**組織方式**：任務依用戶故事分組，以便獨立實作與測試。

## 格式：`[ID] [P?] [Story] 描述`

- **[P]**：可平行執行（不同檔案、無相依性）
- **[Story]**：所屬用戶故事（例如：US1、US2、US3）
- 描述中包含確切檔案路徑

---

## 階段 1：環境建置（共用基礎設施）

**目的**：專案初始化與基本結構

- [x] T001 依實作計畫建立專案結構（src/voice_assistant/、tests/）
- [x] T002 依 plan.md 建立 pyproject.toml 及相依套件
- [x] T003 [P] 建立 .env.example，包含 OPENAI_API_KEY 與 OPENAI_MODEL
- [x] T004 [P] 建立 Python 專案用 .gitignore
- [x] T005 [P] 建立 src/voice_assistant/__init__.py（空套件標記）
- [x] T006 [P] 建立 tests/__init__.py 與 tests/conftest.py

**檢查點**：專案骨架就緒，`uv sync` 應可正常執行

---

## 階段 2：基礎建設（阻塞性前置條件）

**目的**：所有用戶故事都依賴的核心資料結構與 Schema

**⚠️ 關鍵**：此階段完成前，不可開始任何用戶故事

- [x] T007 [P] 依 data-model.md 在 src/voice_assistant/tools/schemas.py 實作 ToolResult schema
- [x] T008 [P] 依 data-model.md 在 src/voice_assistant/llm/schemas.py 實作 ToolCall 與 ChatMessage schema
- [x] T009 [P] 依 plan.md 在 src/voice_assistant/config.py 實作 Settings 設定
- [x] T010 [P] 建立 src/voice_assistant/llm/__init__.py（匯出）
- [x] T011 [P] 建立 src/voice_assistant/tools/__init__.py（匯出）
- [x] T012 依 contracts/llm-client.md 在 src/voice_assistant/llm/errors.py 建立 LLM 錯誤類別（LLMError、LLMConnectionError、LLMAuthenticationError）

**檢查點**：基礎就緒 - 所有 schema 已定義，可開始用戶故事實作

---

## 階段 3：用戶故事 1 - 專案可啟動（優先級：P1）🎯 MVP

**目標**：開發者執行啟動指令後，專案能正常運行不報錯

**獨立測試**：執行 `uv run python -m voice_assistant.main` 不報錯

### 用戶故事 1 實作

- [x] T013 [US1] 依 plan.md 在 src/voice_assistant/main.py 實作進入點
- [x] T014 [US1] 在 main.py 新增環境變數驗證（若缺少 OPENAI_API_KEY 則顯示清楚錯誤）
- [x] T015 [US1] 驗證 `uv run python -m voice_assistant.main` 可正常執行

**檢查點**：用戶故事 1 完成 - 專案可啟動並驗證設定

---

## 階段 4：用戶故事 2 - LLM Client 可連線（優先級：P1）

**目標**：LLM Client 能成功連線 OpenAI API 並取得回應

**獨立測試**：呼叫 LLM Client 的 chat 方法，驗證回傳有效回應

### 用戶故事 2 測試

- [x] T016 [P] [US2] 在 tests/fixtures/mock_responses.py 建立 mock fixtures
- [x] T017 [P] [US2] 依 contracts/llm-client.md 在 tests/unit/test_llm_client.py 撰寫 LLMClient 單元測試

### 用戶故事 2 實作

- [x] T018 [US2] 依 contracts/llm-client.md 在 src/voice_assistant/llm/client.py 實作 LLMClient 類別
- [x] T019 [US2] 實作 chat() 方法與 OpenAI API 呼叫
- [x] T020 [US2] 在 chat() 方法實作 system_prompt 處理
- [x] T021 [US2] 實作 tools 參數支援 Function Calling
- [x] T022 [US2] 實作錯誤處理（將 OpenAI 例外轉換為 LLMError 子類別）
- [x] T023 [US2] 實作回應轉換為 ChatMessage 結構
- [x] T024 [US2] 執行測試：`uv run pytest tests/unit/test_llm_client.py -v`

**檢查點**：用戶故事 2 完成 - LLMClient 可連線 OpenAI API

---

## 階段 5：用戶故事 3 - Tool Registry 可註冊工具（優先級：P1）

**目標**：Tool Registry 能註冊工具並輸出 OpenAI tools 格式

**獨立測試**：註冊 Mock Tool，驗證 `get_openai_tools()` 輸出正確格式

### 用戶故事 3 測試

- [x] T025 [P] [US3] 在 tests/fixtures/mock_tool.py 建立 MockTool fixture
- [x] T026 [P] [US3] 在 tests/unit/test_tool_registry.py 撰寫 BaseTool 單元測試
- [x] T027 [P] [US3] 依 contracts/tool-registry.md 在 tests/unit/test_tool_registry.py 撰寫 ToolRegistry 單元測試

### 用戶故事 3 實作

- [x] T028 [US3] 依 data-model.md 在 src/voice_assistant/tools/base.py 實作 BaseTool 抽象類別
- [x] T029 [US3] 在 BaseTool 實作 to_openai_tool() 方法
- [x] T030 [US3] 依 contracts/tool-registry.md 在 src/voice_assistant/tools/registry.py 實作 ToolRegistry 類別
- [x] T031 [US3] 實作 register() 方法與重複名稱檢查
- [x] T032 [US3] 實作 get() 與 list_tools() 方法
- [x] T033 [US3] 實作 get_openai_tools() 方法
- [x] T034 [US3] 實作 execute() 方法與錯誤處理
- [x] T035 [US3] 執行測試：`uv run pytest tests/unit/test_tool_registry.py -v`

**檢查點**：用戶故事 3 完成 - ToolRegistry 功能完整

---

## 階段 6：收尾與跨領域關注點

**目的**：程式碼品質與最終驗證

- [x] T036 [P] 執行 Ruff 檢查：`uv run ruff check src/ tests/`
- [x] T037 [P] 執行 Ruff 格式化：`uv run ruff format src/ tests/`
- [x] T038 執行所有測試：`uv run pytest -v`
- [x] T039 驗證所有公開類別/方法的型別標註
- [x] T040 更新 src/voice_assistant/__init__.py 的匯出
- [x] T041 最終驗證：`uv run python -m voice_assistant.main`

---

## 相依性與執行順序

### 階段相依性

```
階段 1（環境建置）
    ↓
階段 2（基礎建設）← 阻塞所有用戶故事
    ↓
┌───────────────────────────────────────┐
│  用戶故事可依序進行：                    │
│  階段 3 (US1) → 階段 4 (US2) → 階段 5 (US3) │
└───────────────────────────────────────┘
    ↓
階段 6（收尾）
```

### 用戶故事相依性

- **用戶故事 1（P1）**：僅依賴階段 2 - 不依賴其他故事
- **用戶故事 2（P1）**：依賴階段 2 + 基礎建設的 schema
- **用戶故事 3（P1）**：依賴階段 2 + ToolResult schema

### 各用戶故事內部

- 先寫測試 → 實作前測試應失敗
- Schema/Models → 在服務之前
- 核心實作 → 在整合之前
- 執行測試 → 驗證通過

### 平行執行機會（同階段，標記 [P]）

**階段 1**：
```
T003、T004、T005、T006 → 全部可平行（不同檔案）
```

**階段 2**：
```
T007、T008、T009、T010、T011 → 全部可平行（不同檔案）
```

**階段 4（US2）測試**：
```
T016、T017 → 可平行（不同測試檔案）
```

**階段 5（US3）測試**：
```
T025、T026、T027 → 可平行（不同測試檔案）
```

---

## 實作策略

### MVP 優先（用戶故事 1-3）

1. 完成階段 1：環境建置
2. 完成階段 2：基礎建設（關鍵）
3. 完成階段 3：US1 - 專案可啟動
4. 完成階段 4：US2 - LLM Client
5. 完成階段 5：US3 - Tool Registry
6. 完成階段 6：收尾
7. **驗證**：所有測試通過、Ruff 檢查乾淨

### 建議執行流程

```bash
# 階段 1
uv init
uv sync

# 階段 2 - 平行執行
# T007-T012

# 階段 3 - 循序執行
# T013-T015

# 階段 4 - 先測試，再實作
# T016-T024

# 階段 5 - 先測試，再實作
# T025-T035

# 階段 6 - 最終檢查
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest -v
```

---

## 摘要

| 指標 | 數值 |
|------|------|
| **總任務數** | 41 |
| **階段 1（環境建置）** | 6 個任務 |
| **階段 2（基礎建設）** | 6 個任務 |
| **階段 3（US1）** | 3 個任務 |
| **階段 4（US2）** | 9 個任務 |
| **階段 5（US3）** | 11 個任務 |
| **階段 6（收尾）** | 6 個任務 |
| **平行執行機會** | 15 個任務標記 [P] |

---

## 備註

- [P] 任務 = 不同檔案、無相依性
- [Story] 標籤對應特定用戶故事
- 每個用戶故事可獨立測試
- 每個任務或邏輯群組完成後提交
- 此規格中所有 3 個用戶故事皆為 P1 優先級
