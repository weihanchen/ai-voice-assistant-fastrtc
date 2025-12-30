# Implementation Plan: Stock Price Query

**Branch**: `004-stock-price-query` | **Date**: 2025-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-stock-price-query/spec.md`

## Summary

實作股票報價查詢工具，支援台股（台灣 50 成分股）與美股（S&P 500 前 30 大）的即時報價查詢。使用者可透過中文名稱、英文名稱或股票代碼查詢，系統透過 yfinance 取得報價並以自然語言回覆。

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: yfinance（股票資料）、httpx（HTTP 請求備選）
**Storage**: N/A（無狀態查詢）
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server / Windows 開發環境
**Project Type**: Single project（語音助理工具模組）
**Performance Goals**: 語音回應延遲 < 10 秒
**Constraints**: yfinance 報價延遲 15-20 分鐘（免費版限制）
**Scale/Scope**: 單一工具模組，台灣 50 + 美股前 30 = 約 80 支股票對照表

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 檢查項目 | 狀態 |
|------|----------|------|
| I. Tool-First Architecture | 股票查詢透過獨立 `StockPriceTool` 實現，繼承 `BaseTool` | ✅ PASS |
| II. LLM Auto-Routing | 意圖由 LLM Function Calling 自動判斷，工具透過 `ToolRegistry` 註冊 | ✅ PASS |
| III. Human-Friendly Response | 股價資料由 LLM 轉換為口語化中文回覆 | ✅ PASS |
| IV. Safe Boundary | 股價查詢屬於憲章明定功能範圍，失敗時誠實告知 | ✅ PASS |
| V. Extensible Design | 工具自動註冊，股票對照表可擴充 | ✅ PASS |
| Technical Stack | 使用 yfinance（憲章指定） | ✅ PASS |
| Quality Gates | 需有單元測試、mock 測試、逾時處理 | ✅ PASS |

**Gate Status**: ✅ ALL PASSED

## Project Structure

### Documentation (this feature)

```text
specs/004-stock-price-query/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── stock-price-tool.md
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code (repository root)

```text
src/voice_assistant/
├── tools/
│   ├── __init__.py          # 更新：匯出 StockPriceTool
│   ├── base.py              # 既有：BaseTool 基底類別
│   ├── registry.py          # 既有：ToolRegistry
│   ├── schemas.py           # 既有：ToolResult
│   ├── weather.py           # 既有：天氣工具
│   ├── exchange_rate.py     # 既有：匯率工具
│   └── stock_price.py       # 新增：股票報價工具
└── voice/
    └── pipeline.py          # 更新：SYSTEM_PROMPT 加入股票查詢說明

tests/
├── unit/
│   └── tools/
│       └── test_stock_price.py  # 新增：單元測試
└── fixtures/
    └── stock_responses/         # 新增：mock 回應資料
```

**Structure Decision**: 遵循既有 Tool-First 架構，新增單一工具檔案 `stock_price.py`，測試放置於 `tests/unit/tools/`。

## Complexity Tracking

> **無違反項目，不需追蹤**

本功能完全符合憲章規範，無需複雜度追蹤。
