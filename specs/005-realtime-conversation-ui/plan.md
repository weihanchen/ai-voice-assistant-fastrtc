# Implementation Plan: Realtime Conversation UI

**Branch**: `005-realtime-conversation-ui` | **Date**: 2025-12-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-realtime-conversation-ui/spec.md`

## Summary

在現有語音助理介面上增加即時對話顯示功能，讓使用者可以在瀏覽器中直接看到 ASR 語音辨識結果和 AI 回應文字，無需查看後台 LOG。透過 FastRTC 的 `AdditionalOutputs` 機制和自定義 Gradio Blocks UI 實現即時文字同步。

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastRTC >=0.0.33, Gradio >=5.x, Pydantic >=2.10.x
**Storage**: N/A（記憶體內對話歷史，不持久化）
**Testing**: pytest >=8.x
**Target Platform**: Web Browser (WebRTC-enabled)
**Project Type**: Single project
**Performance Goals**: ASR 文字顯示 <1 秒、狀態更新 <0.3 秒
**Constraints**: 與現有 WebRTC 音訊串流整合、不影響語音延遲
**Scale/Scope**: 單一使用者、保留 20 輪對話記錄

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| **I. Tool-First Architecture** | ✅ Pass | 本功能為 UI 層增強，不涉及外部 API 呼叫 |
| **II. LLM Auto-Routing** | ✅ Pass | 不影響現有 LLM 路由機制 |
| **III. Human-Friendly Response** | ✅ Pass | 顯示已經過 LLM 處理的自然語言回應 |
| **IV. Safe Boundary** | ✅ Pass | 僅顯示既有資料，不新增資料來源 |
| **V. Extensible Design** | ✅ Pass | 透過 Gradio Blocks 組件化設計 |
| **Technical Stack** | ✅ Pass | 使用 Gradio 5.x（FastRTC 內建） |
| **Quality Gates** | ✅ Pass | 將新增 UI 元件測試 |

## Project Structure

### Documentation (this feature)

```text
specs/005-realtime-conversation-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── ui-components.md
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/voice_assistant/
├── main.py                      # 入口點（修改：使用自定義 UI）
├── voice/
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── reply_on_pause.py    # 修改：回傳 AdditionalOutputs
│   ├── pipeline.py              # 修改：yield 對話資料
│   ├── schemas.py               # 修改：新增 ConversationMessage
│   └── ui/                      # 新增：UI 模組
│       ├── __init__.py
│       └── blocks.py            # 新增：Gradio Blocks UI 定義

tests/
├── unit/
│   └── test_ui_components.py    # 新增：UI 元件測試
```

**Structure Decision**: 新增 `voice/ui/` 模組封裝 Gradio UI 邏輯，保持與現有語音管線的分離。

## Complexity Tracking

> 無違規情況，本功能為現有架構的 UI 增強層。
