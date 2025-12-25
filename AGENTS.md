# ai-voice-assistant-fastrtc Development Guidelines

Auto-generated from feature plans. Last updated: 2025-12-25

## Active Technologies

- Python 3.13 + OpenAI SDK + Pydantic (000-ai-voice-assistant)
- FastRTC + faster-whisper + Kokoro TTS (001-fastrtc-voice-pipeline)

## Project Structure

```text
src/
└── voice_assistant/
    ├── main.py              # 入口點（FastRTC Stream）
    ├── config.py            # 環境變數配置
    ├── llm/
    │   ├── client.py        # LLMClient
    │   └── schemas.py       # ChatMessage
    ├── tools/
    │   ├── base.py          # BaseTool
    │   ├── registry.py      # ToolRegistry
    │   └── schemas.py       # ToolResult
    └── voice/               # 語音管線模組 (001)
        ├── pipeline.py      # VoicePipeline
        ├── stt/             # 語音轉文字
        │   └── whisper.py   # faster-whisper 實作
        ├── tts/             # 文字轉語音
        │   └── kokoro.py    # Kokoro TTS 實作
        └── handlers/        # FastRTC 處理器

tests/
├── unit/
├── integration/
└── fixtures/
```

## Commands

```bash
# 啟動
uv run python -m voice_assistant.main

# 測試
uv run pytest

# Linting
uv run ruff check .
uv run ruff format .
```

## Code Style

- Python 3.13: 使用型別標註
- Ruff: 程式碼檢查與格式化
- Pydantic: 資料驗證

## Constitution Reference

所有開發必須遵循 [constitution.md](.specify/memory/constitution.md)：
- Tool-First Architecture
- LLM Auto-Routing
- Human-Friendly Response
- Safe Boundary
- Extensible Design

## Recent Changes

- 001-fastrtc-voice-pipeline: 語音管線（FastRTC + faster-whisper + Kokoro TTS）✅ 實作完成
- 000-ai-voice-assistant: 核心架構骨架（LLMClient, ToolRegistry）

## Implementation Status

| Feature | Status | Description |
|---------|--------|-------------|
| 001-fastrtc-voice-pipeline | ✅ Complete | 語音管線 MVP（中文 ASR/TTS、ReplyOnPause、中斷支援） |
| 000-ai-voice-assistant | 🔄 Pending | 核心架構（LLMClient, ToolRegistry）|

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
