# Implementation Plan: 角色切換面試官功能

**Branch**: `008-role-switching` | **Date**: 2025-01-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-role-switching/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

實現動態角色切換功能，以面試官為 MVP 展示 Prompt Engineering 應用。系統將提供基於 LLMClient.system_prompt 的角色管理機制，支援語音指令切換、Gradio UI 介面和面試官角色的深度追問能力。遵循 Tool-First 架構，通過 BaseRole 繼承模式實現可擴展的角色系統。

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: FastRTC >=0.0.33, openai >=1.58.x, Gradio >=5.x, Pydantic >=2.10.x  
**Storage**: 記憶體內存儲（無持久化需求）  
**Testing**: pytest >=8.x, pytest-asyncio  
**Target Platform**: Linux server (WebRTC)  
**Project Type**: single project (語音助理)  
**Performance Goals**: 角色切換 <3秒，語音回應延遲 <5秒  
**Constraints**: <200ms p95 LLM 回應，<100MB memory footprint  
**Scale/Scope**: 單用戶會話，支援3個預設角色  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✓ Compliant Areas

- **Tool-First Architecture**: 將實作 BaseRole 繼承模式，類似 BaseTool
- **LLM Auto-Routing**: 角色切換透過 LLM Function Calling 自動識別
- **Human-Friendly Response**: 角色回應經 LLM 轉換為自然語言
- **Safe Boundary**: 明確定義角色切換範圍，拒絕範圍外指令
- **Extensible Design**: 角色註冊機制支援未來擴展

### ⚠️ Needs Justification

- **新增 Role 模組**: 不屬於現有 Tool/Agent 架構，但符合擴展性原則
- **UI 組件新增**: Gradio UI 需要新增角色選擇器組件，符合最小侵入性

## Project Structure

### Documentation (this feature)

```text
specs/008-role-switching/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/voice_assistant/
├── main.py              # 入口點（FastRTC Stream）
├── config.py            # 環境變數配置
├── llm/
│   ├── client.py        # LLMClient (現有，需修改支援 system_prompt)
│   └── schemas.py       # ChatMessage (現有)
├── tools/
│   ├── base.py          # BaseTool (現有)
│   ├── registry.py      # ToolRegistry (現有)
│   └── schemas.py       # ToolResult (現有)
├── roles/               # [新增] 角色系統模組
│   ├── base.py          # BaseRole 抽象類別
│   ├── registry.py      # RoleRegistry 註冊管理器
│   ├── state.py         # RoleState 狀態管理
│   ├── schemas.py       # Role 相關資料模型
│   └── predefined/
│       ├── base.py      # 預設角色基類
│       ├── interviewer.py # 面試官角色實作
│       ├── assistant.py  # 助理角色實作
│       └── coach.py      # 教練角色實作
├── intent/              # [新增] 意圖識別模組
│   ├── recognizer.py    # IntentRecognizer
│   └── schemas.py       # 意圖識別資料模型
└── ui/                  # [新增] UI 模組
    └── role_selector.py # Gradio 角色選擇器組件

tests/
├── unit/
│   ├── roles/           # 角色系統單元測試
│   ├── intent/          # 意圖識別單元測試
│   └── ui/              # UI 組件單元測試
├── integration/         # 整合測試
└── fixtures/            # 測試資料
```

**Structure Decision**: 選擇單專案結構，在現有 `src/voice_assistant/` 架構下新增 `roles/`、`intent/` 和 `ui/` 模組。遵循最小侵入性原則，重用現有 `llm/client.py` 的 `system_prompt` 參數。

## Phase 0 Research Summary

✅ **已完成** - research.md 已生成，解決所有技術未知數：

- **角色管理架構**: 採用 BaseRole 繼承模式，與現有 BaseTool 保持一致
- **意圖識別方案**: 基於 LLM Function Calling，符合 LLM Auto-Routing 原則  
- **狀態管理**: 記憶體內存儲，符合無持久化需求
- **UI 整合**: Gradio 介面擴展，最小化變更

## Phase 1 Design Artifacts

✅ **已完成** - 所有設計文件已生成：

1. **data-model.md**: 完整的資料模型定義，包含 Role、RoleState、Intent 等核心實體
2. **contracts/**: API 契約規範，包含 API 文件和 OpenAPI 3.0 規範
3. **quickstart.md**: 完整的開發者指南，包含使用範例和故障排除

## Post-Design Constitution Check

### ✓ Confirmed Compliance

- **Tool-First Architecture**: BaseRole 繼承模式遵循相同設計原則
- **LLM Auto-Routing**: 意圖識別完全依賴 LLM Function Calling
- **Human-Friendly Response**: 所有角色回應經 LLM 自然語言轉換
- **Safe Boundary**: 明確定義角色範圍，拒絕越界請求
- **Extensible Design**: 角色註冊機制支援未來擴展，無需修改核心邏輯

### ✓ Technology Stack Alignment

- **Python 3.13**: ✅ 符合規範
- **FastRTC >=0.0.33**: ✅ 重用現有框架
- **OpenAI >=1.58.x**: ✅ 用於 LLM 整合
- **Pydantic >=2.10.x**: ✅ 用於資料驗證
- **Gradio >=5.x**: ✅ 擴展現有 UI

### ✓ Complexity Justified

新增模組都有明確業務需求，符合 KISS 原則：
- `roles/`: 核心業務邏輯，無法避免
- `intent/`: 意圖識別需要獨立模組，保持職責分離
- `ui/`: UI 組件最小化變更，符合擴展性要求

## Next Steps

使用 `/speckit.tasks` 生成具體的實作任務清單，然後使用 `/speckit.implement` 開始實作。

## Complexity Tracking

| Change | Justification | Constitution Alignment |
|--------|---------------|------------------------|
| 新增 Role 模組 | 實現角色切換核心功能 | 符合 Extensible Design 原則 |
| 新增 Intent 模組 | 意圖識別邏輯分離 | 符合 LLM Auto-Routing 原則 |
| 新增 UI 模組 | 最小化 Gradio 變更 | 符合 Tool-First Architecture 原則 |
