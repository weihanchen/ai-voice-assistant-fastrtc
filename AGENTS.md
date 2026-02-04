# ai-voice-assistant-fastrtc Development Guidelines

Auto-generated from feature plans. Last updated: 2025-12-25

## Active Technologies
- Python 3.13 + FastRTC >=0.0.33, openai >=1.58.x, Gradio >=5.x, Pydantic >=2.10.x (008-role-switching)
- 記憶體內存儲（無持久化需求） (008-role-switching)

- Python 3.13 + OpenAI SDK + Pydantic (000-ai-voice-assistant)
- FastRTC + faster-whisper + Kokoro TTS (001-fastrtc-voice-pipeline)
- httpx + Open-Meteo API (002-weather-query)
- httpx + ExchangeRate-API (003-exchange-rate-query)

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
    │   ├── weather.py       # WeatherTool (002)
    │   └── exchange_rate.py # ExchangeRateTool (003)
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
- **繁體中文優先**：所有文件、註解、commit message、spec 文件皆以繁體中文撰寫

## Software Quality Principles

- **KISS & YAGNI**: 追求極致簡潔。拒絕過度設計，只為當前明確的需求編寫程式碼。
- **SOLID 原則**: 嚴格遵守 SOLID 原則，尤其是 `SRP`（單一職責）和 `ISP`（介面隔離）。
- **Clean Code & DRY**: 消除重複邏輯。注重程式碼的自解釋性和**防禦性程式設計**（Null Check, Exception Handling）。
- **效能敏感**: 即時關注系統開銷、資源佔用（記憶體、連線池、磁碟 I/O）及演算法複雜度。

## Protected Files

**禁止修改以下檔案**（由開發者手動維護）：
- `CLAUDE.md` - Claude Code 專案指引入口
- `AGENTS.md` - 開發規範與工作流程

若需更新這些檔案，請通知開發者手動處理。

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
- 008-role-switching: Added Python 3.13 + FastRTC >=0.0.33, openai >=1.58.x, Gradio >=5.x, Pydantic >=2.10.x

- 003-exchange-rate-query: 匯率查詢工具（httpx + ExchangeRate-API）✅ 實作完成
- 002-weather-query: 天氣查詢工具（httpx + Open-Meteo API）✅ 實作完成

## Implementation Status

| Feature | Status | Description |
|---------|--------|-------------|
| 003-exchange-rate-query | ✅ Complete | 匯率查詢工具（ExchangeRateTool, ExchangeRate-API, 31 tests passed） |
| 002-weather-query | ✅ Complete | 天氣查詢工具（WeatherTool, Open-Meteo API, 24 tests passed） |
| 001-fastrtc-voice-pipeline | ✅ Complete | 語音管線 MVP（中文 ASR/TTS、ReplyOnPause、中斷支援） |
| 000-ai-voice-assistant | 🔄 Pending | 核心架構（LLMClient, ToolRegistry）|

## Development Workflow

### Commit 前流程
1. **Code Review** - AI 審查邏輯、安全性、最佳實踐
2. **修正問題** - 根據審查建議調整程式碼
3. **Lint + Format** - `uv run ruff check --fix . && uv run ruff format .`
4. **Commit** - 提交變更

### Review 標準

#### 程式碼品質
- 函式保持單一職責，過長時考慮拆解
- 使用 Pydantic 驗證外部輸入資料
- 遵循現有 OOP 架構（BaseTool 繼承模式）

#### 命名規範
- Boolean: `is_*` / `has_*` / `can_*`
- 函式: 動詞開頭 `get_*` / `create_*` / `handle_*`

#### 錯誤處理
- 外部 API 呼叫需處理異常（httpx 請求等）
- 內部邏輯讓異常自然冒泡，由上層統一處理

#### 安全性
- 禁止硬編碼密鑰或敏感資訊
- 檢查注入風險（SQL、Command Injection）

### Commit Message 格式
```
<type>: <簡述>

type: feat | fix | refactor | docs | test | chore
```

<!-- MANUAL ADDITIONS START -->

## AI Agent 行為準則

### 禁止事項

1. **不要擅自修改版本號**：不要修改 `pyproject.toml` 等檔案中的版本要求，除非使用者明確要求
2. **不要直接安裝套件**：不要使用 `pip install`直接安裝套件，應使用專案管理工具

### 必須遵守

1. **使用 uv 執行 Python**：所有 Python 相關指令必須透過 `uv run` 執行（如 `uv run pytest`）
2. **遵循專案既有設定**：不要擅自變更專案的 linter、formatter、測試框架等設定

<!-- MANUAL ADDITIONS END -->
