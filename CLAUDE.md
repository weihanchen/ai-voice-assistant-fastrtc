# ai-voice-assistant-fastrtc Development Guidelines

Auto-generated from feature plans. Last updated: 2025-12-24

## Active Technologies

- Python 3.14 + OpenAI SDK + Pydantic (000-ai-voice-assistant)

## Project Structure

```text
src/
└── voice_assistant/
    ├── main.py              # 入口點
    ├── config.py            # 環境變數配置
    ├── llm/
    │   ├── client.py        # LLMClient
    │   └── schemas.py       # ChatMessage
    └── tools/
        ├── base.py          # BaseTool
        ├── registry.py      # ToolRegistry
        └── schemas.py       # ToolResult

tests/
├── unit/
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

- Python 3.14: 使用型別標註
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

- 000-ai-voice-assistant: 核心架構骨架（LLMClient, ToolRegistry）

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
