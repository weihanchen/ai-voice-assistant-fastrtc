---

description: "Task list for feature implementation"
---

# Tasks: 角色切換面試官功能

**輸入**: 來自 `/specs/008-role-switching/` 的設計文件
**前置條件**: plan.md (必需), spec.md (使用者故事必需), research.md, data-model.md, contracts/

**測試**: 以下範例包含測試任務。測試為選項性 - 僅在功能規格中明確要求時包含。

**組織**: 任務按使用者故事分組，以實現獨立的實作和測試。

## 格式：`[ID] [P?] [Story] 描述`

- **[P]**：可並行執行（不同檔案，無依賴關係）
- **[Story]**：此任務屬於哪個使用者故事（例如：US1, US2, US3）
- 描述中包含確切檔案路徑

## 路徑慣例

- **單一專案**：`src/`、`tests/` 在倉儲根目錄
- **Web 應用**：`backend/src/`、`frontend/src/`
- **行動應用**：`api/src/`、`ios/src/` 或 `android/src/`
- 顯示的路徑假設為單一專案 - 根據 plan.md 結構調整

## 第 1 階段：設置（共享基礎架構）

**目的**：專案初始化和基本結構

- [X] T001 Create roles module directory structure in src/voice_assistant/roles/
- [X] T002 Create intent module directory structure in src/voice_assistant/intent/
- [X] T003 Create ui module directory structure in src/voice_assistant/ui/
- [X] T004 [P] Create test directory structure for roles in tests/unit/roles/
- [X] T005 [P] Create test directory structure for intent in tests/unit/intent/
- [X] T006 [P] Create test directory structure for ui in tests/unit/ui/

---

## 第 2 階段：基礎架構（阻塞性先決條件）

**目的**：核心基礎架構，必須在任何使用者故事開始前完成

**⚠️ 關鍵**：在完成此階段前，無法開始任何使用者故事工作

- [X] T007 [P] Create BaseRole abstract class in src/voice_assistant/roles/base.py
- [X] T008 [P] Create Role data models in src/voice_assistant/roles/schemas.py
- [X] T009 [P] Create Intent data models in src/voice_assistant/intent/schemas.py
- [X] T010 [P] Create error handling classes for role system
- [X] T011 Create RoleRegistry in src/voice_assistant/roles/registry.py
- [X] T012 Create RoleState in src/voice_assistant/roles/state.py
- [X] T013 Create IntentRecognizer base structure in src/voice_assistant/intent/recognizer.py
- [X] T014 [P] Extend LLMClient to support dynamic system_prompt updates
- [X] T015 Configure logging for role system operations

**檢查點**：基礎架構就緒 - 使用者故事實作現在可以並行開始

[狀態更新] 截至目前，Setup（T001-T006）與基礎結構（T007-T015）全數完成，請進入下一階段「User Story 1」。

---

## Phase 3: User Story 1 - 基礎角色切換機制 (Priority: P1) 🎯 MVP

**Goal**: 實現角色註冊和切換的核心機制，為所有其他功能提供基礎

**Independent Test**: 可以透過程式化方式測試角色註冊和切換邏輯，無需依賴 UI 或語音功能

### Implementation for User Story 1

- [X] T016 [US1] 在 src/voice_assistant/roles/predefined/base.py 建立預設角色基礎類別
- [X] T017 [P] [US1] 在 src/voice_assistant/roles/predefined/assistant.py 建立助理角色
- [X] T018 [P] [US1] 在 src/voice_assistant/roles/predefined/coach.py 建立教練角色
- [X] T019 [US1] 在 RoleRegistry 中實作角色註冊邏輯
- [X] T020 [US1] 在 RoleState 中實作角色切換邏輯
- [X] T021 [US1] 將角色切換與 LLMClient system_prompt 更新整合
- [X] T022 [US1] 將角色切換新增到 FastRTC Stream 處理器（reply_on_pause.py/UI glue 已完成，含 sidebar role selector）
- [X] T023 [US1] 在 tests/unit/roles/test_registry.py 建立角色註冊的單元測試
- [X] T024 [US1] 在 tests/unit/roles/test_state.py 建立角色狀態管理的單元測試
- [X] T025 [US1] 在 tests/unit/test_voice_pipeline.py 補全角色切換關鍵單元測試（覆蓋 pipeline.switch_role 狀態與 prompt，同步 glue 行為）

**檢查點**: 此時使用者故事 1 應該完全功能化且可獨立測試

---

## Phase 4: User Story 2 - 面試官角色實作 (Priority: P1) 🎯 MVP

**目標**: 實作面試官角色的深度追問能力，展示 Prompt Engineering 價值

**獨立測試**: 可以透過文字輸入測試面試官角色的回應品質和追問邏輯，驗證角色配置正確性

### User Story 2 實作

- [X] T026 [US2] 在 src/voice_assistant/roles/predefined/interviewer.py 建立專業語氣的面試官角色
- [X] T027 [US2] 實作面試官角色的深度提問提示詞
- [X] T028 [US2] 新增追問問題生成邏輯（以 Prompt 形式植入 system_prompt）
- [X] T029 [US2] 為技術面試配置面試官角色系統提示詞
- [X] T030 [US2] 新增面試官情境的範例回應
- [X] T031 [US2] 在 RoleRegistry 中註冊面試官角色（UI 下拉同步顯示，已驗證）
- [X] T032 [US2] 在 tests/unit/roles/test_interviewer.py 建立面試官角色的單元測試（已整合入 pipeline 類測）
- [X] T033 [US2] 在 tests/integration/test_interviewer.py 建立面試官互動的整合測試（涵蓋角色切換、回應 prompt 檢查）

> 2026-01-27 實作及測試全數通過，面試官角色支援角色註冊、切換、prompt 自動同步，所有預設角色皆經單元/整合測試覆蓋。


**檢查點**: 此時使用者故事 1 和 2 都應該獨立運作

---

## Phase 5: User Story 3 - 語音指令角色切換 (Priority: P2)

**Goal**: 實現基於 LLM Function Calling 的語音指令識別和角色切換

**Independent Test**: 可以透過模擬語音輸入或直接文字指令測試意圖識別和角色切換邏輯

### Implementation for User Story 3

- [X] T034 [US3] 在 IntentRecognizer 中實作用於意圖識別的 LLM Function Calling
- [X] T035 [US3] 建立角色切換意圖模式和提示詞
- [X] T036 [US3] 將語音指令處理新增到 FastRTC Stream
- [X] T037 [US3] 實作意圖信心分數評分和驗證
- [X] T038 [US3] 新增未識別指令的錯誤處理
- [X] T039 [US3] 新增成功切換的確認訊息
- [X] T040 [US3] 在 tests/unit/intent/test_recognizer.py 建立意圖識別的單元測試
- [ ] T041 [US3] 在 tests/integration/test_voice_commands.py 建立語音指令切換的整合測試（尚未建立，單元測試已覆蓋關鍵場景）

**檢查點**: 此時使用者故事 1、2 和 3 都應該獨立功能化

---

## Phase 6: User Story 4 - Gradio UI 角色選擇器 (Priority: P2)

**目標**: 提供視覺化的角色管理介面，讓使用者查看當前狀態並手動選擇角色

**獨立測試**: 可以透過 UI 自動化測試角色選擇器的互動邏輯和狀態顯示

### User Story 4 實作

- [X] T042 [US4] 在 src/voice_assistant/ui/role_selector.py 建立 Gradio 角色選擇器組件
- [X] T043 [US4] 實作角色狀態顯示功能
- [X] T044 [US4] 新增角色選擇下拉/選擇介面
- [X] T045 [US4] 將角色選擇器與主要 Gradio 介面整合
- [X] T046 [US4] 新增 UI 即時狀態更新
- [X] T047 [US4] 新增角色切換的視覺回饋

> 2026-01-28 全部 UI glue/code 已驗證，已於主程式組裝、side-bar、Glue/狀態雙向綁定，手動及自動測試通過。
- [X] T048 [US4] 在 tests/unit/ui/test_role_selector.py 建立角色選擇器的單元測試
- [X] T049 [US4] 在 tests/integration/test_ui_role_switch.py 建立 UI 角色切換的整合測試

> 2026-01-28 已通過單元測試與整合測試，角色選擇 UI glue/狀態同步皆正確

**檢查點**: 所有使用者故事現在都應該獨立功能化

---

## Phase 7: 完善 & 跨領域關注

**目的**: 影響多個使用者故事的改進

- [X] T050 [P] 為所有角色操作新增完整日誌記錄
- [X] T051 [P] 新增角色切換時間的效能監控
- [X] T052 [P] 新增錯誤處理和優雅降級
- [X] T053 [P] 新增輸入驗證和清理（已於 switch_role 參數、狀態管理等邏輯補齊）
- [ ] T054 更新 main.py 以初始化角色系統
- [ ] T055 新增預設角色的配置選項
- [ ] T056 新增角色切換指標收集
- [ ] T057 [P] 用實際實作範例更新 quickstart.md
- [X] T058 [P] 為所有新模組新增 docstring 和型別提示
- [X] T059 [P] 用 ruff 執行 linting 和格式檢查
- [ ] T060 新增完整工作流程的端對端整合測試
- [ ] T061 新增角色切換延遲的效能測試
- [ ] T062 新增角色狀態管理的記憶體使用測試

> 2026-01-28 已完成 T050-T053, T058, T059（見 pipeline.py、roles/state.py）；角色操作、切換流程全面增強 log、異常降級與效能監控，降級提示已自動同步至 UI 和語音串流回覆。後續可進行 main.py 初始化及 e2e 測試優化。

---

## 依賴關係 & 執行順序

### 階段依賴關係

- **Setup (Phase 1)**: 無依賴 - 可立即開始
- **Foundational (Phase 2)**: 依賴 Setup 完成 - 阻塞所有使用者故事
- **User Stories (Phase 3-6)**: 全部依賴 Foundational 階段完成
  - 使用者故事然後可以並行進行（如果有人力）
  - 或依優先序順序進行（P1 → P2）
- **Polish (Final Phase)**: 依賴所有期望的使用者故事完成

### 使用者故事依賴關係

- **User Story 1 (P1)**: Foundational (Phase 2) 後可開始 - 不依賴其他故事
- **User Story 2 (P1)**: Foundational (Phase 2) 後可開始 - 依賴 User Story 1 的角色系統基礎
- **User Story 3 (P2)**: Foundational (Phase 2) 後可開始 - 依賴 User Story 1 的角色切換機制
- **User Story 4 (P2)**: Foundational (Phase 2) 後可開始 - 依賴 User Story 1 的角色狀態管理

### 每個使用者故事內部

- 模型在服務之前
- 服務在端點之前
- 核心實作在整合之前
- 故事完成後再移至下一個優先級

### 並行機會

- 所有標記 [P] 的 Setup 任務可並行執行
- 所有標記 [P] 的 Foundational 任務可並行執行（在 Phase 2 內）
- Foundational 階段完成後，User Stories 1 和 2（都是 P1）可並行開始
- User Stories 3 和 4（都是 P2）可在 P1 故事後並行開始
- 使用者故事的所有標記 [P] 的測試可並行執行
- 故事內標記 [P] 的模型可並行執行
- 不同使用者故事可由不同團隊成員並行進行

---

## 並行範例：User Story 1

```bash
# 為 User Story 1 一起啟動所有預設角色：
Task: "在 src/voice_assistant/roles/predefined/assistant.py 建立助理角色"
Task: "在 src/voice_assistant/roles/predefined/coach.py 建立教練角色"

# 為 User Story 1 一起啟動所有單元測試：
Task: "在 tests/unit/roles/test_registry.py 建立角色註冊的單元測試"
Task: "在 tests/unit/roles/test_state.py 建立角色狀態管理的單元測試"
```

---

## 多個使用者故事並行範例

```bash
# Foundational 階段後的多位開發者：
開發者 A: User Story 1 (T016-T025)
開發者 B: User Story 2 (T026-T033)
# 兩者可並行工作，因為依賴相同的基礎
```

---

## 實作策略

### MVP 優先（僅 User Stories 1 & 2）

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（關鍵 - 阻塞所有故事）
3. 完成 Phase 3: User Story 1（角色註冊和切換）
4. 完成 Phase 4: User Story 2（面試官角色）
5. **停止並驗證**: 獨立測試 User Stories 1 & 2
6. 部署/展示核心角色切換功能

### 增量交付

1. 完成 Setup + Foundational → 基礎就緒
2. 新增 User Story 1 → 獨立測試 → 部署/展示（核心角色切換）
3. 新增 User Story 2 → 獨立測試 → 部署/展示（包含面試官的 MVP）
4. 新增 User Story 3 → 獨立測試 → 部署/展示（語音指令）
5. 新增 User Story 4 → 獨立測試 → 部署/展示（UI 整合）
6. 每個故事都增加價值而不破壞之前的故事

### 並行團隊策略

多位開發者情況下：

1. 團隊一起完成 Setup + Foundational
2. Foundational 完成後：
   - 開發者 A: User Story 1（核心角色系統）
   - 開發者 B: User Story 2（面試官角色）- 等待 US1 基礎
3. P1 故事完成後：
   - 開發者 A: User Story 3（語音指令）
   - 開發者 B: User Story 4（UI 整合）
4. 故事獨立完成和整合

---

## 注意事項

- [P] 任務 = 不同檔案，無依賴關係
- [Story] 標籤將任務對應到特定使用者故事以供追蹤
- 每個使用者故事應該獨立可完成和可測試
- User Stories 1 & 2 是 P1 並形成 MVP
- User Stories 3 & 4 是 P2 並新增增強功能
- 在 User Story 2 檢查點停止以進行核心 MVP 交付
- 所有任務遵循既有的 Python 專案結構和慣例
- 實作前驗證測試失敗
- 每個任務或邏輯群組後提交
- 在任何檢查點停止以獨立驗證故事