# Implementation Plan: FastRTC Voice Pipeline

**Branch**: `001-fastrtc-voice-pipeline` | **Date**: 2025-12-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-fastrtc-voice-pipeline/spec.md`

## Summary

實作 FastRTC 語音管線，整合 faster-whisper（中文 ASR）與 Kokoro TTS（中文語音合成），透過 ReplyOnPause 機制自動偵測使用者停頓並觸發回應。系統透過 Gradio WebRTC UI 提供瀏覽器介面，並與現有 LLMClient 整合處理對話邏輯。

**技術方案重點**：
- ASR：使用 faster-whisper tiny 模型（成本最小化，支援中文）
- TTS：使用 Kokoro-82M-v1.1-zh 中文模型
- 停頓閾值：0.5 秒
- 語言：繁體中文輸入/輸出

## Technical Context

**Language/Version**: Python 3.13（依據 Constitution，kokoro-onnx 相容性）
**Primary Dependencies**: FastRTC >=0.0.33, faster-whisper, kokoro, openai >=1.58.x, Pydantic >=2.10.x
**Storage**: N/A（無持久化需求，對話歷史在記憶體中）
**Testing**: pytest >=8.x, mock 測試
**Target Platform**: Linux server / Docker container, 瀏覽器（Chrome/Firefox/Edge）
**Project Type**: single（擴展現有專案結構）
**Performance Goals**: 語音回應延遲 < 3 秒，中斷反應 < 0.5 秒
**Constraints**: CPU 本地推理（ASR/TTS），記憶體 < 500MB（tiny 模型約 39MB）
**Scale/Scope**: 單一使用者 Demo 專案

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| **I. Tool-First Architecture** | ✅ 符合 | 語音管線不涉及外部資料查詢，ASR/TTS 為獨立模組 |
| **II. LLM Auto-Routing** | ✅ 符合 | 語音輸入透過 FastRTC Stream 入口處理，意圖識別由 LLM 決定 |
| **III. Human-Friendly Response** | ✅ 符合 | TTS 輸出口語化繁體中文 |
| **IV. Safe Boundary** | ✅ 符合 | 語音管線僅負責 I/O，不涉及資料查詢邏輯 |
| **V. Extensible Design** | ✅ 符合 | ASR/TTS 模組抽象化，可替換 |

### Constitution 差異說明

| 項目 | Constitution 規範 | 本規格選擇 | 理由 |
|------|-------------------|------------|------|
| **ASR** | Moonshine（FastRTC 內建） | faster-whisper tiny | Moonshine 不支援中文，faster-whisper 支援且有 FastRTC STTModel Protocol 整合方案 |
| **TTS** | Kokoro（FastRTC 內建） | Kokoro-82M-v1.1-zh | 需使用中文專用模型，非預設英文模型 |

> ✅ **Constitution 已更新**（v1.1.0）：Python 3.13、ASR 改用 faster-whisper、TTS 改用 kokoro-onnx

## Project Structure

### Documentation (this feature)

```text
specs/001-fastrtc-voice-pipeline/
├── spec.md              # 規格文件
├── plan.md              # 本文件
├── research.md          # Phase 0 研究結果
├── data-model.md        # Phase 1 資料模型
├── contracts/           # Phase 1 介面契約
│   ├── stt-adapter.md   # STT 轉接器契約
│   └── tts-adapter.md   # TTS 轉接器契約
└── tasks.md             # Phase 2 任務清單
```

### Source Code (repository root)

```text
src/
└── voice_assistant/
    ├── main.py              # 入口點（擴展為 FastRTC Stream）
    ├── config.py            # 環境變數配置（新增 ASR/TTS 設定）
    ├── llm/                 # 現有 LLM 模組
    │   ├── client.py
    │   └── schemas.py
    ├── tools/               # 現有工具模組
    │   ├── base.py
    │   ├── registry.py
    │   └── schemas.py
    └── voice/               # 新增：語音管線模組
        ├── __init__.py
        ├── pipeline.py      # VoicePipeline 主類別
        ├── stt/             # 語音轉文字
        │   ├── __init__.py
        │   ├── base.py      # STTModel Protocol
        │   └── whisper.py   # faster-whisper 實作
        ├── tts/             # 文字轉語音
        │   ├── __init__.py
        │   ├── base.py      # TTSModel Protocol
        │   └── kokoro.py    # Kokoro 實作
        └── handlers/        # FastRTC 處理器
            ├── __init__.py
            └── reply_on_pause.py  # ReplyOnPause 整合

tests/
├── unit/
│   ├── test_llm_client.py       # 現有
│   ├── test_tool_registry.py    # 現有
│   ├── test_stt_whisper.py      # 新增
│   ├── test_tts_kokoro.py       # 新增
│   └── test_voice_pipeline.py   # 新增
├── integration/
│   └── test_voice_e2e.py        # 新增：端對端語音測試
└── fixtures/
    ├── mock_responses.py        # 現有
    ├── mock_tool.py             # 現有
    └── audio_samples/           # 新增：測試用音訊檔案
        └── hello_zh.wav
```

**Structure Decision**: 採用 Single Project 結構，在現有 `src/voice_assistant/` 下新增 `voice/` 模組，保持與 LLM/Tools 模組的一致性。

## Complexity Tracking

> 無違規需要說明，技術選擇符合 Constitution 精神（僅 ASR 因語言需求調整）。

| 調整項目 | 理由 | 替代方案被拒絕原因 |
|----------|------|---------------------|
| ASR 改用 faster-whisper | 中文支援需求（Moonshine 僅英文） | 無其他成本更低的中文 ASR 方案 |
