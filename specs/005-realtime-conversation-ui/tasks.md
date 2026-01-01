# 任務清單：即時對話顯示 UI

**輸入來源**：`/specs/005-realtime-conversation-ui/` 設計文件
**先決條件**：plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**測試**：未明確要求測試，本任務清單不包含測試任務。

**組織方式**：任務依 User Story 分組，確保每個 Story 可獨立實作與測試。

## 格式說明：`[ID] [P?] [Story] 描述`

- **[P]**：可並行執行（不同檔案、無相依性）
- **[Story]**：所屬 User Story（如 US1, US2, US3）
- 描述中包含完整檔案路徑

## 路徑慣例

- **單一專案**：`src/voice_assistant/`、`tests/` 位於專案根目錄

---

## 階段 1：基礎建置（共用基礎設施）✅

**目的**：專案初始化與 UI 模組結構

- [x] T001 建立 UI 模組目錄結構於 src/voice_assistant/voice/ui/
- [x] T002 [P] 建立 src/voice_assistant/voice/ui/__init__.py 並匯出模組
- [x] T003 [P] 確認 pyproject.toml 中有 gradio-webrtc 依賴（若無則新增）

---

## 階段 2：基礎元件（阻塞性前置條件）✅

**目的**：所有 User Story 依賴的核心資料模型

**⚠️ 重要**：此階段完成前，不可開始任何 User Story 實作

- [x] T004 在 src/voice_assistant/voice/schemas.py 建立 ConversationMessage 模型
- [x] T005 在 src/voice_assistant/voice/schemas.py 建立 ConversationHistory 模型（含 add/to_gradio 方法）
- [x] T006 在 src/voice_assistant/voice/schemas.py 建立 UIState 模型（含 from_voice_state 方法）
- [x] T007 在 src/voice_assistant/voice/schemas.py 擴展 ConversationState 加入 history 欄位
- [x] T008 在 src/voice_assistant/voice/ui/blocks.py 建立 UIComponents 資料類別

**檢查點**：基礎元件就緒，可開始 User Story 實作 ✅

---

## 階段 3：User Story 1 & 2 - 即時文字顯示（優先級：P1）🎯 MVP ✅

**目標**：使用者可即時看到 ASR 辨識文字和 AI 回應文字，不需查看後台 LOG

**獨立測試**：說一段話後，ASR 文字和 AI 回應文字都即時顯示在介面上

### User Story 1 & 2 實作

- [x] T009 [P] [US1] 在 src/voice_assistant/voice/ui/blocks.py 實作 create_conversation_ui()
- [x] T010 [P] [US1] 在 src/voice_assistant/voice/ui/blocks.py 實作 update_ui() 回呼函式
- [x] T011 [US1] 在 src/voice_assistant/voice/pipeline.py 實作 process_audio_with_outputs()
- [x] T012 [US1] 在 src/voice_assistant/voice/pipeline.py 匯入 AdditionalOutputs 並 yield
- [x] T013 [US1] 在 src/voice_assistant/voice/pipeline.py STT 完成後更新 history
- [x] T014 [US2] 在 src/voice_assistant/voice/pipeline.py LLM 回應後更新 history
- [x] T015 [US1] 在 src/voice_assistant/voice/handlers/reply_on_pause.py 修改 create_voice_stream() 使用自定義 UI
- [x] T016 [US1] 在 src/voice_assistant/voice/handlers/reply_on_pause.py 設定 on_additional_outputs 事件綁定
- [x] T017 [US1] 在 src/voice_assistant/voice/ui/__init__.py 匯出新 UI 函式

**檢查點**：ASR 文字和 AI 回應文字即時顯示功能完成 ✅

---

## 階段 4：User Story 3 - 對話歷史記錄（優先級：P2）✅

**目標**：使用者可查看多輪對話的完整歷史記錄

**獨立測試**：進行 3 輪對話後，所有對話記錄都保留在介面上並可捲動瀏覽

### User Story 3 實作

- [x] T018 [US3] 在 src/voice_assistant/voice/schemas.py ConversationHistory 實作 max_messages 限制
- [x] T019 [US3] 在 src/voice_assistant/voice/schemas.py ConversationHistory 實作 clear() 方法
- [x] T020 [US3] 在 src/voice_assistant/voice/ui/blocks.py 設定 Chatbot 高度與捲動行為
- [x] T021 [US3] 在 src/voice_assistant/voice/schemas.py 驗證訊息順序保持（時間順序）

**檢查點**：對話歷史記錄功能完成，可保留 20 輪對話並捲動瀏覽 ✅

---

## 階段 5：User Story 4 - 系統狀態指示（優先級：P2）✅

**目標**：使用者可即時看到系統狀態（待命/聆聽/處理/回應）

**獨立測試**：觀察不同操作階段的狀態指示變化

### User Story 4 實作

- [x] T022 [US4] 在 src/voice_assistant/voice/schemas.py UIState.from_voice_state() 實作狀態文字對應
- [x] T023 [US4] 在 src/voice_assistant/voice/ui/blocks.py create_conversation_ui() 加入狀態顯示樣式
- [x] T024 [US4] 在 src/voice_assistant/voice/pipeline.py 每次狀態轉換時 yield 狀態更新
- [x] T025 [US4] 在 src/voice_assistant/voice/ui/blocks.py 處理 INTERRUPTED 狀態顯示

**檢查點**：系統狀態指示功能完成 ✅

---

## 階段 6：音訊檔案測試模式 ✅

**目的**：支援上傳音訊檔案替代麥克風輸入，方便在無法使用麥克風的環境下驗證功能

**使用情境**：在嘈雜環境（如咖啡廳）或無麥克風設備時，可透過上傳預錄音訊檔案來測試完整流程

- [x] T026 在 src/voice_assistant/voice/ui/blocks.py 新增 create_audio_input() 建立音訊上傳元件
- [x] T027 在 src/voice_assistant/voice/handlers/reply_on_pause.py 建立自訂 UI 整合音訊上傳與 WebRTC
- [x] T028 在 src/voice_assistant/voice/ui/blocks.py 實作 audio_input_handler() 處理上傳音訊
- [x] T029 在 src/voice_assistant/voice/ui/__init__.py 匯出新函式

**檢查點**：可透過上傳音訊檔案觸發完整對話流程（STT → LLM → TTS → UI 更新） ✅

---

## 階段 7：收尾與跨領域處理 ✅

**目的**：影響多個 User Story 的改進項目

- [x] T030 [P] 在 src/voice_assistant/voice/pipeline.py 新增空白 ASR 結果的錯誤處理
- [x] T031 [P] 在 src/voice_assistant/voice/ui/blocks.py 新增 UI 更新事件的 logging
- [x] T032 確認新檔案通過 Ruff linting 檢查
- [x] T033 執行 quickstart.md 驗證（手動測試）
- [x] T034 若有新模式建立，更新 CLAUDE.md（已有 commit skill）

---

## 相依性與執行順序

### 階段相依性

- **基礎建置（階段 1）**：無相依性，可立即開始
- **基礎元件（階段 2）**：依賴階段 1 完成，**阻塞所有 User Story**
- **User Story（階段 3+）**：依賴階段 2 完成
  - US1 & US2（階段 3）：可在階段 2 後開始
  - US3（階段 4）：可在階段 3 後或並行進行
  - US4（階段 5）：可在階段 3 後或並行進行
- **收尾（階段 6）**：依賴所有 User Story 完成

### User Story 相依性

- **User Story 1 & 2（P1）**：階段 2 後可開始，核心功能
- **User Story 3（P2）**：擴展 US1/2，但可獨立測試，歷史記錄管理
- **User Story 4（P2）**：擴展 US1/2，但可獨立測試，狀態顯示

### 各 User Story 內部順序

- 模型先於服務/UI
- create_conversation_ui() 先於事件綁定
- pipeline 修改先於 handler 整合
- 核心實作先於收尾

### 並行機會

**階段 1（基礎建置）**：
```
T002 [P] + T003 [P] 可並行
```

**階段 2（基礎元件）**：
```
T004, T005, T006 為順序執行（同一檔案）
T008 可與 T004-T007 並行
```

**階段 3（US1 & US2）**：
```
T009 [P] + T010 [P] 可並行（同檔案但不同函式）
```

**階段 4 & 5 可整體並行**（不同 User Story）

---

## 並行執行範例：階段 3（User Story 1 & 2）

```bash
# 並行建立 UI 元件：
任務："T009 [P] [US1] 在 src/voice_assistant/voice/ui/blocks.py 實作 create_conversation_ui()"
任務："T010 [P] [US1] 在 src/voice_assistant/voice/ui/blocks.py 實作 update_ui() 回呼函式"

# 接著順序執行：
任務："T011 [US1] 在 src/voice_assistant/voice/pipeline.py 實作 process_audio_with_outputs()"
# ... 階段 3 其餘任務
```

---

## 實作策略

### MVP 優先（僅 User Story 1 & 2）

1. 完成階段 1：基礎建置（T001-T003）
2. 完成階段 2：基礎元件（T004-T008）
3. 完成階段 3：User Story 1 & 2（T009-T017）
4. **停下驗證**：測試 ASR 文字和 AI 回應即時顯示
5. 若可用，部署/展示，使用者已不需查看後台 LOG

### 漸進式交付

1. 完成基礎建置 + 基礎元件 → 基礎就緒
2. 加入 US1 & US2 → 獨立測試 → 部署/展示（MVP！）
3. 加入 US3（對話歷史）→ 獨立測試 → 部署/展示
4. 加入 US4（狀態指示）→ 獨立測試 → 部署/展示
5. 每個 Story 增加價值且不破壞既有功能

### 單人開發策略

依優先順序順序執行：
1. 階段 1 → 階段 2 → 階段 3（MVP 完成）
2. 接著 階段 4 → 階段 5 → 階段 6 → 階段 7

---

## 檔案摘要

| 檔案 | 動作 | 任務 |
|------|------|------|
| src/voice_assistant/voice/ui/__init__.py | 新增 | T002, T017, T029 |
| src/voice_assistant/voice/ui/blocks.py | 新增 | T008, T009, T010, T020, T023, T025, T026, T028, T031 |
| src/voice_assistant/voice/schemas.py | 修改 | T004, T005, T006, T007, T018, T019, T021, T022 |
| src/voice_assistant/voice/pipeline.py | 修改 | T011, T012, T013, T014, T024, T030 |
| src/voice_assistant/voice/handlers/reply_on_pause.py | 修改 | T015, T016, T027 |
| pyproject.toml | 確認 | T003 |

---

## 備註

- [P] 任務 = 不同檔案或獨立函式，無相依性
- [Story] 標籤將任務對應至特定 User Story 以便追蹤
- US1 & US2 合併，因共用 AdditionalOutputs 機制
- 若後續新增測試，需先確認測試失敗再實作
- 每完成一個任務或邏輯群組後提交
- 可在任何檢查點停下，獨立驗證該 Story
