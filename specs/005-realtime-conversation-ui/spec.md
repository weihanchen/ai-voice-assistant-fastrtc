# Feature Specification: Realtime Conversation UI

**Feature Branch**: `005-realtime-conversation-ui`
**Created**: 2025-12-31
**Status**: Draft
**Input**: User description: "新增 Gradio UI 即時對話顯示功能：在現有的語音助理介面上增加文字顯示區域，讓使用者可以即時看到 ASR 語音辨識結果和 TTS 回應文字，不需要查看後台 LOG。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 即時查看語音辨識結果 (Priority: P1)

使用者透過麥克風說話後，希望能在介面上即時看到系統辨識出的文字內容，確認系統正確理解了自己說的話。

**Why this priority**: 這是最核心的需求，使用者需要知道系統「聽到了什麼」，這是所有後續互動的基礎。沒有這個功能，使用者無法確認語音輸入是否正確。

**Independent Test**: 可透過說一段話後，確認 ASR 文字即時顯示在介面上來獨立測試。

**Acceptance Scenarios**:

1. **Given** 使用者正在使用語音助理, **When** 使用者對麥克風說「今天台北天氣如何」, **Then** 介面上即時顯示「今天台北天氣如何」的辨識文字
2. **Given** 使用者已說完一段話, **When** 系統完成語音辨識, **Then** 完整的辨識文字在 1 秒內顯示於介面

---

### User Story 2 - 即時查看 AI 回應文字 (Priority: P1)

使用者希望在 AI 回應語音播放的同時，能看到對應的文字內容，方便閱讀和確認資訊。

**Why this priority**: 與 P1-1 同等重要，語音可能聽不清楚或環境嘈雜時，文字顯示可作為輔助理解。

**Independent Test**: 可透過發送一個查詢後，確認 AI 回應文字即時顯示在介面上來獨立測試。

**Acceptance Scenarios**:

1. **Given** 使用者已發送語音查詢, **When** AI 開始回應, **Then** 回應文字同步顯示在介面上
2. **Given** AI 正在播放語音回應, **When** 回應內容較長, **Then** 文字隨語音進度逐步顯示

---

### User Story 3 - 查看對話歷史記錄 (Priority: P2)

使用者希望能看到之前的對話記錄，方便回顧先前詢問過的內容和 AI 的回應。

**Why this priority**: 對話歷史是良好使用者體驗的重要組成，但不是核心功能。

**Independent Test**: 可透過進行多輪對話後，確認所有對話記錄都保留在介面上來獨立測試。

**Acceptance Scenarios**:

1. **Given** 使用者已進行 3 輪對話, **When** 查看對話區域, **Then** 可看到所有 3 輪的完整對話記錄
2. **Given** 對話記錄超過可視區域, **When** 使用者捲動, **Then** 可瀏覽所有歷史對話

---

### User Story 4 - 查看當前系統狀態 (Priority: P2)

使用者希望知道系統目前的狀態（閒置中、聆聽中、處理中、回應中），以便了解何時可以開始說話。

**Why this priority**: 狀態指示改善使用者體驗，但沒有它系統仍可正常運作。

**Independent Test**: 可透過觀察不同操作階段的狀態指示變化來獨立測試。

**Acceptance Scenarios**:

1. **Given** 系統啟動完成, **When** 使用者查看狀態, **Then** 顯示「閒置」或「待命」狀態
2. **Given** 使用者開始說話, **When** 系統偵測到語音, **Then** 狀態切換為「聆聽中」
3. **Given** 使用者說完話, **When** 系統正在處理, **Then** 狀態切換為「處理中」
4. **Given** AI 開始回應, **When** 語音正在播放, **Then** 狀態切換為「回應中」

---

### User Story 5 - 音訊檔案測試模式 (Priority: P2)

使用者希望在無法使用麥克風的環境（如嘈雜的咖啡廳或無麥克風設備）下，能透過上傳預錄的音訊檔案來測試完整的對話流程。

**Why this priority**: 這是開發與測試的輔助功能，讓使用者可以在任何環境下驗證系統功能，但不是核心使用情境。

**Independent Test**: 可透過上傳一個 .wav 音訊檔案，確認觸發完整流程（STT → LLM → TTS → UI 更新）來獨立測試。

**Acceptance Scenarios**:

1. **Given** 使用者在無麥克風環境, **When** 上傳一個包含「今天天氣如何」的音訊檔案, **Then** 系統辨識音訊並顯示 ASR 結果於介面
2. **Given** 使用者上傳音訊檔案, **When** 系統完成處理, **Then** 完整對話流程執行（STT → LLM → TTS → UI 更新）
3. **Given** 使用者上傳音訊檔案, **When** 處理過程中, **Then** 狀態指示正確顯示（處理中 → 回應中 → 待命）

---

### Edge Cases

- 當 ASR 辨識失敗或回傳空白時，介面應顯示適當的提示訊息
- 當網路延遲導致回應緩慢時，狀態應正確反映「處理中」
- 當使用者快速連續發送多個語音輸入時，對話記錄應按時間順序正確排列
- 當對話記錄過長時，應有適當的捲動機制，不影響效能
- 當上傳的音訊檔案格式不支援時，應顯示適當的錯誤訊息
- 當上傳的音訊檔案過大或過長時，應有適當的處理機制

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統必須在語音辨識完成後 1 秒內將 ASR 文字顯示於介面
- **FR-002**: 系統必須在 AI 回應時同步顯示對應的文字內容
- **FR-003**: 系統必須保留當前對話的完整歷史記錄
- **FR-004**: 系統必須以對話氣泡形式區分使用者輸入與 AI 回應
- **FR-005**: 系統必須顯示當前狀態（閒置/聆聽/處理/回應）
- **FR-006**: 系統必須在狀態變更時即時更新狀態顯示
- **FR-007**: 對話歷史區域必須支援捲動瀏覽
- **FR-008**: 新對話必須自動捲動至最新訊息
- **FR-009**: 系統必須支援上傳音訊檔案作為輸入來源
- **FR-010**: 上傳的音訊檔案必須觸發與麥克風輸入相同的處理流程

### Key Entities

- **ConversationMessage**: 單一對話訊息，包含角色（使用者/助理）、內容、時間戳記
- **ConversationState**: 當前對話狀態，包含狀態類型、最後更新時間
- **ConversationHistory**: 對話歷史集合，包含所有訊息的有序列表

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ASR 辨識文字在語音結束後 1 秒內顯示於介面
- **SC-002**: AI 回應文字與語音播放同步顯示，延遲不超過 0.5 秒
- **SC-003**: 使用者不需查看後台 LOG 即可完成所有對話互動
- **SC-004**: 狀態指示在狀態變更後 0.3 秒內更新
- **SC-005**: 對話歷史正確保留至少 20 輪對話記錄
- **SC-006**: 介面捲動流暢，無明顯卡頓

## Assumptions

- 現有的 `ConversationState` 類別已追蹤 `last_user_text` 和 `last_assistant_text`
- FastRTC 的 Gradio 整合支援自定義 UI 元件
- 使用者使用現代瀏覽器（支援 WebRTC）
- 單一使用者使用情境，無需多使用者對話隔離

## Dependencies

- 依賴 001-fastrtc-voice-pipeline 的語音管線基礎架構
- 依賴現有的 `VoiceState` 狀態機制
- 依賴 Gradio 框架的 UI 元件
