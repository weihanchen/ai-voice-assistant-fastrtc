# ai-voice-assistant-fastrtc Development Guidelines

Auto-generated from feature plans. Last updated: 2025-12-25

## Active Technologies

- Python 3.13 + OpenAI SDK + Pydantic (000-ai-voice-assistant)
- FastRTC + faster-whisper + Kokoro TTS (001-fastrtc-voice-pipeline)
- httpx + Open-Meteo API (002-weather-query)

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
    │   ├── schemas.py       # ToolResult
    │   └── weather.py       # WeatherTool (002)
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

## Spec-Kit Workflow

新功能開發必須依照以下流程進行：

```
/speckit.specify <功能描述>  → specs/NNN-feature/spec.md（規格文件）
/speckit.clarify             → 釐清規格疑問（可選）
/speckit.plan                → specs/NNN-feature/plan.md（實作計畫）
/speckit.tasks               → specs/NNN-feature/tasks.md（任務清單）
/speckit.implement           → 執行實作
```

**重要規則**：
- 不可直接建立功能分支（如 `git checkout -b NNN-feature`），必須透過 `/speckit.specify` 建立
- 每個 spec 目錄包含：spec.md, plan.md, tasks.md, checklists/
- 遵循 User Story 優先順序（P1 → P2 → P3）進行實作

## Constitution Reference

所有開發必須遵循 [constitution.md](.specify/memory/constitution.md)：
- Tool-First Architecture
- LLM Auto-Routing
- Human-Friendly Response
- Safe Boundary
- Extensible Design

## Recent Changes

- 002-weather-query: 天氣查詢工具（httpx + Open-Meteo API）✅ 實作完成
- 001-fastrtc-voice-pipeline: 語音管線（FastRTC + faster-whisper + Kokoro TTS）✅ 實作完成
- 000-ai-voice-assistant: 核心架構骨架（LLMClient, ToolRegistry）

## Implementation Status

| Feature | Status | Description |
|---------|--------|-------------|
| 002-weather-query | ✅ Complete | 天氣查詢工具（WeatherTool, Open-Meteo API, 24 tests passed） |
| 001-fastrtc-voice-pipeline | ✅ Complete | 語音管線 MVP（中文 ASR/TTS、ReplyOnPause、中斷支援） |
| 000-ai-voice-assistant | 🔄 Pending | 核心架構（LLMClient, ToolRegistry）|

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
