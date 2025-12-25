# Implementation Plan: Weather Query Tool

**Branch**: `002-weather-query` | **Date**: 2025-12-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-weather-query/spec.md`

## Summary

實作天氣查詢工具，讓使用者透過語音詢問台灣主要城市的即時天氣。系統將天氣查詢實作為 `BaseTool` 子類別，透過 Open-Meteo API 取得天氣資料，LLM 自動路由決定何時調用工具，並以口語化繁體中文回應使用者。

**技術方案重點**：
- 工具：繼承 `BaseTool`，實作 `WeatherTool` 類別
- API：Open-Meteo（免費、無需 API Key）
- 城市對照：預建台灣城市經緯度對照表
- 整合：透過 `ToolRegistry` 註冊，LLM Function Calling 自動調用

## Technical Context

**Language/Version**: Python 3.13（依據 Constitution）
**Primary Dependencies**: openai >=1.58.x, httpx（HTTP 客戶端）, Pydantic >=2.10.x
**Storage**: N/A（無持久化需求，城市座標為靜態資料）
**Testing**: pytest >=8.x, pytest-asyncio, respx（HTTP mock）
**Target Platform**: Linux server / Docker container
**Project Type**: single（擴展現有 `src/voice_assistant/tools/` 模組）
**Performance Goals**: API 查詢延遲 < 2 秒（含網路），整體回應 < 5 秒
**Constraints**: 無外部 API Key 需求，僅依賴免費 API
**Scale/Scope**: 單一使用者 Demo 專案

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| **I. Tool-First Architecture** | ✅ 符合 | 天氣查詢透過 `WeatherTool` 實作，繼承 `BaseTool` |
| **II. LLM Auto-Routing** | ✅ 符合 | 透過 OpenAI Function Calling 自動調用，語音層不做意圖判斷 |
| **III. Human-Friendly Response** | ✅ 符合 | 工具回傳結構化資料，LLM 轉換為口語化中文 |
| **IV. Safe Boundary** | ✅ 符合 | 僅處理天氣查詢，不支援的城市回傳明確錯誤 |
| **V. Extensible Design** | ✅ 符合 | 透過 `ToolRegistry` 自動註冊，新增工具無需修改核心邏輯 |

### 技術選擇說明

| 項目 | 選擇 | 理由 |
|------|------|------|
| **HTTP Client** | httpx | 支援 async，符合 Tool 的 async execute pattern |
| **Weather API** | Open-Meteo | Constitution 指定，免費無需 API Key |

## Project Structure

### Documentation (this feature)

```text
specs/002-weather-query/
├── spec.md              # 規格文件
├── plan.md              # 本文件
├── research.md          # Phase 0 研究結果
├── data-model.md        # Phase 1 資料模型
├── quickstart.md        # Phase 1 快速入門
├── contracts/           # Phase 1 介面契約
│   └── weather-tool.md  # WeatherTool 契約
└── tasks.md             # Phase 2 任務清單
```

### Source Code (repository root)

```text
src/
└── voice_assistant/
    ├── main.py              # 入口點（更新：註冊 WeatherTool）
    ├── config.py            # 環境變數配置（更新：新增天氣設定）
    ├── llm/                 # 現有 LLM 模組
    │   ├── client.py
    │   └── schemas.py
    ├── tools/               # 工具模組
    │   ├── __init__.py      # 更新：匯出 WeatherTool
    │   ├── base.py          # 現有 BaseTool
    │   ├── registry.py      # 現有 ToolRegistry
    │   ├── schemas.py       # 現有 ToolResult
    │   └── weather.py       # 新增：WeatherTool 實作
    └── voice/               # 現有語音管線模組

tests/
├── unit/
│   ├── test_weather_tool.py  # 新增：WeatherTool 單元測試
│   └── ...
├── integration/
│   └── test_weather_e2e.py   # 新增：端對端測試（可選）
└── fixtures/
    └── mock_weather.py       # 新增：天氣 API mock 資料
```

**Structure Decision**: 在現有 `src/voice_assistant/tools/` 目錄下新增 `weather.py`，保持與 `BaseTool` 的一致性。

## Complexity Tracking

> 無違規需要說明，技術選擇完全符合 Constitution 規範。

| 調整項目 | 理由 | 替代方案被拒絕原因 |
|----------|------|---------------------|
| 無 | - | - |
