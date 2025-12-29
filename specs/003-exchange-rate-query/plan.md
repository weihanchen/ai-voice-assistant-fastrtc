# Implementation Plan: Exchange Rate Query Tool

**Branch**: `003-exchange-rate-query` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-exchange-rate-query/spec.md`

## Summary

實作匯率查詢工具，讓使用者可透過語音詢問貨幣匯率並進行金額換算。採用 ExchangeRate-API（免費、無需 API Key、支援 TWD）查詢即時匯率，以新台幣（TWD）為基準貨幣，支援 8 種常用國際貨幣的雙向換算。

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: httpx（HTTP 客戶端）, openai（LLM SDK）
**Storage**: N/A（無持久化需求，匯率資料即時查詢）
**Testing**: pytest + pytest-asyncio + pytest-mock
**Target Platform**: Linux/Windows 伺服器
**Project Type**: Single project
**Performance Goals**: 語音回應延遲 < 5 秒
**Constraints**: API 呼叫需有逾時處理（10 秒），支援優雅降級
**Scale/Scope**: 單機運行，支援 8 種貨幣

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 檢查項目 | 狀態 |
|------|----------|------|
| **Tool-First Architecture** | 匯率查詢透過獨立 ExchangeRateTool 實作，繼承 BaseTool | ✅ 符合 |
| **LLM Auto-Routing** | Tool 透過 OpenAI Function Calling 自動選擇 | ✅ 符合 |
| **Human-Friendly Response** | 匯率回應經 LLM 轉換為口語化繁體中文 | ✅ 符合 |
| **Safe Boundary** | 匯率換算在定義範圍內，失敗時誠實告知 | ✅ 符合 |
| **Extensible Design** | 遵循 ToolRegistry 機制，新增工具無需修改核心 | ✅ 符合 |
| **技術規範** | 使用 ExchangeRate-API（支援 TWD） | ✅ 符合 |

## Project Structure

### Documentation (this feature)

```text
specs/003-exchange-rate-query/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── exchange-rate-tool.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/voice_assistant/
├── tools/
│   ├── __init__.py          # 匯出 ExchangeRateTool
│   ├── base.py              # BaseTool 基底類別
│   ├── registry.py          # ToolRegistry
│   ├── schemas.py           # ToolResult
│   ├── weather.py           # WeatherTool（既有）
│   └── exchange_rate.py     # ExchangeRateTool（新增）
└── voice/
    └── handlers/
        └── reply_on_pause.py  # 註冊 ExchangeRateTool

tests/
├── fixtures/
│   └── mock_exchange_rate.py  # Mock API 回應
└── unit/
    └── test_exchange_rate_tool.py  # 單元測試
```

**Structure Decision**: 延續 002-weather-query 的結構，新增 `exchange_rate.py` 於 `tools/` 目錄，遵循既有的 Tool 模式。

## Complexity Tracking

> 無違規項目，無需填寫
