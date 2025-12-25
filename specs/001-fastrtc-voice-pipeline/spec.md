# Feature Specification: FastRTC Voice Pipeline

**Feature Branch**: `001-fastrtc-voice-pipeline`
**Created**: 2025-12-24
**Status**: Draft
**Input**: FastRTC 語音管線，整合 Whisper (faster-whisper) ASR 與 Kokoro TTS，實作 ReplyOnPause 行為定義，Gradio UI 整合需求

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 基本語音對話 (Priority: P1)

使用者透過瀏覽器開啟語音助理介面，對著麥克風說中文。系統自動偵測使用者何時停止說話，將語音轉換為文字，送給 LLM 處理後，將回應轉換為語音播放給使用者聽。

**Why this priority**: 這是語音助理的核心功能，沒有這個基本對話能力，其他功能都無法運作。

**Independent Test**: 可透過開啟網頁、對著麥克風說「你好」，系統回應語音來驗證。

**Acceptance Scenarios**:

1. **Given** 使用者已開啟語音助理網頁並授權麥克風, **When** 使用者說「你好」後停止說話, **Then** 系統在 3 秒內開始播放語音回應
2. **Given** 語音助理正在運作, **When** 使用者用中文說出一個問題, **Then** 系統正確辨識語音內容並給予相關回應
3. **Given** 網路連線正常, **When** 使用者開始對話, **Then** 整個對話過程（語音輸入→處理→語音輸出）在 5 秒內完成

---

### User Story 2 - 對話中斷與接續 (Priority: P2)

使用者在助理回應的過程中可以隨時插話打斷，系統會停止目前的回應並開始處理新的輸入。這讓對話更自然，使用者不必等待完整回應。

**Why this priority**: 自然的對話體驗需要支援中斷，但這是在基本對話功能完成後的增強功能。

**Independent Test**: 當系統正在語音回應時，使用者開口說話，系統應停止回應並處理新輸入。

**Acceptance Scenarios**:

1. **Given** 系統正在播放語音回應, **When** 使用者開始說話, **Then** 系統在 0.5 秒內停止播放並開始接收新的語音輸入
2. **Given** 使用者打斷了系統回應, **When** 使用者說完新的問題, **Then** 系統正常處理並回應新問題

---

### User Story 3 - 無語音輸入時的靜默處理 (Priority: P3)

使用者開啟語音助理後保持沉默或環境噪音，系統不應誤判為語音輸入，保持待命狀態直到偵測到真正的人聲。

**Why this priority**: 避免誤觸發是良好使用體驗的一部分，但優先級低於核心對話功能。

**Independent Test**: 開啟助理後保持沉默 30 秒，系統不應有任何回應。

**Acceptance Scenarios**:

1. **Given** 語音助理處於待命狀態, **When** 環境有背景噪音但無人聲, **Then** 系統不觸發任何回應
2. **Given** 使用者開啟麥克風但保持沉默, **When** 經過 30 秒, **Then** 系統保持待命狀態，不產生任何回應

---

### Edge Cases

- 當使用者的麥克風權限被拒絕時，系統顯示清楚的錯誤訊息並引導使用者授權
- 當網路連線中斷時，系統通知使用者並在恢復後自動重新連線
- 當使用者說話太小聲或太模糊時，系統請求使用者重複一次
- 當 LLM 回應時間過長時，系統播放等待提示音或訊息
- 當多人同時說話時，系統嘗試辨識主要說話者或請求一次一人發言

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 透過網頁瀏覽器提供語音輸入介面
- **FR-002**: 系統 MUST 自動偵測使用者停止說話的時機（ReplyOnPause，停頓閾值 0.5 秒）
- **FR-003**: 系統 MUST 將使用者語音轉換為文字（語音辨識）
- **FR-004**: 系統 MUST 將 LLM 回應轉換為語音播放（語音合成）
- **FR-005**: 系統 MUST 支援使用者在回應播放中打斷並接受新輸入
- **FR-006**: 系統 MUST 支援中文語音輸入（透過 faster-whisper tiny 模型實現）
- **FR-011**: 系統 MUST 使用中文語音輸出（透過 Kokoro TTS 實現）
- **FR-007**: 系統 MUST 與現有 LLMClient 整合以處理對話邏輯
- **FR-008**: 系統 MUST 提供視覺化狀態指示（待命、聆聽中、處理中、回應中）
- **FR-009**: 系統 MUST 在麥克風權限被拒時顯示友善錯誤訊息
- **FR-010**: 系統 MUST 過濾背景噪音，避免誤觸發回應

### Key Entities

- **AudioStream**: 即時音訊串流，包含來源（麥克風/系統）、音訊格式、時間戳記
- **TranscribedText**: 語音辨識結果，包含文字內容、信心分數、語言代碼、時間戳記
- **SynthesizedAudio**: 語音合成結果，包含音訊資料、對應文字、語音參數
- **ConversationState**: 對話狀態，包含目前狀態（idle/listening/processing/speaking）、對話歷史參考

## Clarifications

### Session 2025-12-25

- Q: TTS 語音輸出應使用什麼語言？ → A: 中文（zh）
- Q: Whisper 模型應使用哪個大小？ → A: tiny（成本最小化，Demo 專案優先）
- Q: ReplyOnPause 停頓閾值應設為多少？ → A: 0.5 秒（平衡反應速度與誤觸發風險）

## Assumptions

- 使用者使用現代瀏覽器（Chrome、Firefox、Edge）存取語音助理
- 使用者設備具有麥克風和喇叭/耳機
- 語音辨識支援中文（透過 faster-whisper tiny 模型，優先成本最小化）
- 系統運行在具備足夠 CPU 資源的環境（本地推理需求）
- LLMClient 已在 000 規格中實作完成
- ASR 使用 faster-whisper 實作 FastRTC 的 STTModel Protocol 進行整合

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 使用者從說話結束到開始聽到回應的時間在 3 秒內
- **SC-002**: 中文語音辨識準確率達到 90% 以上（標準中文發音環境）
- **SC-003**: 使用者打斷系統回應後，系統在 0.5 秒內停止播放
- **SC-004**: 系統在安靜環境中誤觸發率低於 5%
- **SC-005**: 使用者可在開啟網頁後 10 秒內開始第一次對話
- **SC-006**: 連續對話 10 輪內系統保持穩定回應，無明顯延遲增加
