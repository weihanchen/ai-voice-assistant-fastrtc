# Tasks: FastRTC Voice Pipeline

**Input**: Design documents from `/specs/001-fastrtc-voice-pipeline/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: 包含單元測試任務（spec.md 品質標準要求）

**Organization**: 任務依 User Story 分組，支援獨立實作與測試

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可平行執行（不同檔案，無相依性）
- **[Story]**: 所屬 User Story (US1, US2, US3)
- 所有路徑基於 `src/voice_assistant/`

---

## Phase 1: Setup (環境設定)

**Purpose**: 專案初始化與相依套件設定

- [x] T001 更新 pyproject.toml 新增 FastRTC、faster-whisper、kokoro + misaki[zh] 相依套件
- [x] T002 執行 uv lock 並驗證相依套件解析成功
- [x] T003 [P] 建立 models/ 目錄並新增 .gitkeep 與 README 說明模型下載方式
- [x] T004 [P] 更新 .env.example 新增語音管線相關環境變數

---

## Phase 2: Foundational (基礎架構)

**Purpose**: 核心基礎設施，**必須**在任何 User Story 前完成

**⚠️ CRITICAL**: 此階段未完成前，不可開始 User Story 實作

- [x] T005 建立 src/voice_assistant/voice/ 模組目錄結構（含 `__init__.py`）
- [x] T006 [P] 建立 src/voice_assistant/voice/schemas.py 資料模型（AudioFrame, TranscribedText, TTSConfig, VoiceState, ConversationState, VoicePipelineConfig）
- [x] T007 [P] 建立 src/voice_assistant/voice/stt/__init__.py 與 base.py（STTModel Protocol）
- [x] T008 [P] 建立 src/voice_assistant/voice/tts/__init__.py 與 base.py（TTSModel Protocol）
- [x] T009 更新 src/voice_assistant/config.py 新增 VoiceSettings（ASR/TTS/VAD 配置）

**Checkpoint**: 基礎架構完成 - 可開始 User Story 實作

---

## Phase 3: User Story 1 - 基本語音對話 (Priority: P1) 🎯 MVP

**Goal**: 使用者透過瀏覽器說中文，系統自動偵測停頓、語音轉文字、LLM 處理、語音回應

**Independent Test**: 開啟網頁，對著麥克風說「你好」，系統 3 秒內開始播放語音回應

### Tests for User Story 1

- [x] T010 [P] [US1] 建立 tests/unit/test_stt_whisper.py 測試 WhisperSTT（Protocol 實作、空音訊處理）
- [x] T011 [P] [US1] 建立 tests/unit/test_tts_kokoro.py 測試 KokoroTTS（Protocol 實作、串流輸出）
- [x] T012 [P] [US1] 建立 tests/unit/test_voice_pipeline.py 測試 VoicePipeline（狀態轉移、STT→LLM→TTS 流程）

### Implementation for User Story 1

- [x] T013 [P] [US1] 實作 src/voice_assistant/voice/stt/whisper.py（WhisperSTT 類別，faster-whisper 整合）
- [x] T014 [P] [US1] 實作 src/voice_assistant/voice/tts/kokoro.py（KokoroTTS 類別，kokoro + misaki[zh] 整合）
- [x] T015 [US1] 實作 src/voice_assistant/voice/pipeline.py（VoicePipeline 主類別，整合 STT/LLM/TTS）
- [x] T016 [US1] 建立 src/voice_assistant/voice/handlers/__init__.py 與 reply_on_pause.py（FastRTC ReplyOnPause 處理器整合）
- [x] T017 [US1] 更新 src/voice_assistant/main.py 整合 FastRTC Stream 與 Gradio UI
- [x] T018 [US1] 更新 src/voice_assistant/voice/__init__.py 匯出 VoicePipeline 與 create_voice_stream

**Checkpoint**: User Story 1 完成 - 基本語音對話功能可獨立測試

---

## Phase 4: User Story 2 - 對話中斷與接續 (Priority: P2)

**Goal**: 使用者可隨時打斷助理回應，系統停止播放並處理新輸入

**Independent Test**: 當系統正在語音回應時，使用者開口說話，系統 0.5 秒內停止回應

### Tests for User Story 2

- [x] T019 [P] [US2] 擴充 tests/unit/test_voice_pipeline.py 測試中斷狀態轉移（SPEAKING → INTERRUPTED）

### Implementation for User Story 2

- [x] T020 [US2] 擴充 src/voice_assistant/voice/pipeline.py 新增 on_interrupt() 方法
- [x] T021 [US2] 更新 src/voice_assistant/voice/handlers/reply_on_pause.py 配置 can_interrupt=True

**Checkpoint**: User Story 2 完成 - 中斷功能可獨立測試

---

## Phase 5: User Story 3 - 無語音輸入時的靜默處理 (Priority: P3)

**Goal**: 環境噪音或靜默時，系統不誤觸發回應

**Independent Test**: 開啟助理後保持沉默 30 秒，系統不應有任何回應

### Tests for User Story 3

- [x] T022 [P] [US3] 擴充 tests/unit/test_voice_pipeline.py 測試空輸入處理

### Implementation for User Story 3

- [x] T023 [US3] 更新 src/voice_assistant/voice/handlers/reply_on_pause.py 配置 Silero VAD 參數（speech_threshold, min_speech_duration_ms）
- [x] T024 [US3] 更新 src/voice_assistant/voice/pipeline.py 空輸入時保持 IDLE 狀態

**Checkpoint**: User Story 3 完成 - 靜默處理可獨立測試

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨 User Story 的改善與整合

- [x] T025 [P] 建立 tests/fixtures/audio_samples/ 目錄與測試用音訊檔案說明
- [x] T026 [P] 更新 AGENTS.md 反映 001 實作完成狀態
- [x] T027 執行完整測試套件驗證所有功能（uv run pytest -v）
- [x] T028 執行 Ruff 檢查並修正程式碼風格（uv run ruff check src/ tests/）

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (BLOCKS all user stories)
    ↓
    ├── Phase 3: US1 基本語音對話 (MVP)
    │       ↓
    ├── Phase 4: US2 對話中斷（可與 US1 平行，但建議 US1 先完成）
    │       ↓
    └── Phase 5: US3 靜默處理（可與 US1/US2 平行）
            ↓
        Phase 6: Polish
```

### User Story Dependencies

| User Story | 依賴 | 說明 |
|------------|------|------|
| **US1 基本語音對話** | Phase 2 完成 | 無其他 Story 依賴，可獨立實作 |
| **US2 對話中斷** | Phase 2 完成 | 擴充 US1 的 pipeline，建議 US1 先完成 |
| **US3 靜默處理** | Phase 2 完成 | 調整 VAD 參數，可與 US1 平行 |

### Within Each User Story

1. Tests 先寫並確認 FAIL
2. 實作 STT/TTS 元件（可平行）
3. 整合 VoicePipeline
4. 整合 FastRTC Handler
5. 更新 main.py 入口
6. 確認 Tests PASS

### Parallel Opportunities

**Phase 1 平行任務**:
```
T003 建立 models/ 目錄
T004 更新 .env.example
```

**Phase 2 平行任務**:
```
T006 建立 schemas.py
T007 建立 stt/base.py
T008 建立 tts/base.py
```

**Phase 3 (US1) 平行任務**:
```
Tests:
  T010 test_stt_whisper.py
  T011 test_tts_kokoro.py
  T012 test_voice_pipeline.py

Implementation:
  T013 whisper.py
  T014 kokoro.py
```

---

## Parallel Example: User Story 1

```bash
# 同時啟動所有 US1 測試任務:
Task: "T010 建立 tests/unit/test_stt_whisper.py"
Task: "T011 建立 tests/unit/test_tts_kokoro.py"
Task: "T012 建立 tests/unit/test_voice_pipeline.py"

# 同時啟動 STT/TTS 實作:
Task: "T013 實作 whisper.py"
Task: "T014 實作 kokoro.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. ✅ Complete Phase 1: Setup
2. ✅ Complete Phase 2: Foundational
3. ✅ Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: 開啟網頁測試語音對話
5. Deploy/Demo（MVP 完成）

### Incremental Delivery

| 階段 | 產出 | 可展示功能 |
|------|------|------------|
| Setup + Foundational | 專案骨架 | - |
| + US1 | **MVP** | 基本語音對話 |
| + US2 | 增強版 | 支援打斷 |
| + US3 | 完整版 | 噪音過濾 |

---

## Summary

| 項目 | 數量 |
|------|------|
| **總任務數** | 28 |
| Phase 1 Setup | 4 |
| Phase 2 Foundational | 5 |
| Phase 3 US1 (MVP) | 9 |
| Phase 4 US2 | 3 |
| Phase 5 US3 | 3 |
| Phase 6 Polish | 4 |
| **可平行任務** | 15 |
| **MVP 範圍** | T001-T018 (18 tasks) |

---

## Notes

- [P] 任務 = 不同檔案，無相依性
- [Story] 標籤對應 spec.md User Story
- 每個 User Story 可獨立完成與測試
- 先寫測試，確認 FAIL 後再實作
- 每個任務或邏輯群組完成後 commit
- 任何 Checkpoint 都可停下來驗證功能
