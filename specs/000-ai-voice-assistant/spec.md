# Feature Specification: AI Voice Assistant 核心架構

**Feature Branch**: `000-ai-voice-assistant`
**Created**: 2025-12-23
**Status**: Draft
**Constitution**: [constitution.md](../../.specify/memory/constitution.md)

## Overview

建立 AI 語音助理的專案骨架與核心框架。此階段目標是讓專案能夠「站起來」，包含基本目錄結構、LLM Client 封裝、Tool Registry 框架設計，為後續功能模組奠定基礎。

**此階段不包含完整功能實作**，僅建立可運行的骨架。

---

## User Scenarios & Testing

### User Story 1 - 專案可啟動 (Priority: P1)

開發者執行啟動指令後，專案能正常運行不報錯。

**Why this priority**: 專案必須能啟動才能進行後續開發。

**Independent Test**: 執行 `uv run python -m voice_assistant.main` 不報錯。

**Acceptance Scenarios**:

1. **Given** 專案已安裝依賴，**When** 執行主程式，**Then** 程式正常啟動無錯誤
2. **Given** 環境變數未設定，**When** 執行主程式，**Then** 顯示明確的設定提示

---

### User Story 2 - LLM Client 可連線 (Priority: P1)

LLM Client 能成功連線 OpenAI API 並取得回應。

**Why this priority**: LLM 是核心功能，必須確認連線正常。

**Independent Test**: 呼叫 LLM Client 的 chat 方法，驗證回傳有效回應。

**Acceptance Scenarios**:

1. **Given** OPENAI_API_KEY 已設定，**When** 呼叫 LLM Client，**Then** 回傳 LLM 回應
2. **Given** API Key 無效，**When** 呼叫 LLM Client，**Then** 回傳標準化錯誤訊息

---

### User Story 3 - Tool Registry 可註冊工具 (Priority: P1)

Tool Registry 能註冊工具並輸出 OpenAI tools 格式。

**Why this priority**: 這是 Function Calling 的基礎架構。

**Independent Test**: 註冊 Mock Tool，驗證 `get_openai_tools()` 輸出正確格式。

**Acceptance Scenarios**:

1. **Given** 已定義 MockTool，**When** 註冊到 Registry，**Then** `get_openai_tools()` 回傳正確 schema
2. **Given** Registry 有多個工具，**When** 呼叫 `execute(name, args)`，**Then** 正確執行對應工具

---

### Edge Cases

- 環境變數缺失？→ 啟動時明確提示
- LLM API 連線失敗？→ 回傳標準化錯誤
- 工具名稱不存在？→ Registry 回傳 None 或拋出明確例外

---

## Requirements

### Functional Requirements

#### 專案結構

- **FR-001**: 專案 MUST 使用 `src/voice_assistant/` 作為主要程式碼目錄
- **FR-002**: 專案 MUST 提供 `pyproject.toml` 定義依賴與專案設定
- **FR-003**: 專案 MUST 提供 `.env.example` 作為環境變數範本

#### LLM Client

- **FR-004**: 系統 MUST 封裝 OpenAI API 呼叫為獨立的 `LLMClient` 類別
- **FR-005**: LLMClient MUST 支援 Function Calling（tools 參數）
- **FR-006**: LLMClient MUST 支援 System Prompt 配置
- **FR-007**: LLMClient MUST 處理 API 錯誤並回傳標準化結構

#### Tool Registry

- **FR-008**: 系統 MUST 提供 `BaseTool` 抽象基底類別
- **FR-009**: 系統 MUST 提供 `ToolRegistry` 類別管理工具註冊
- **FR-010**: BaseTool MUST 定義 `name`、`description`、`parameters` 屬性
- **FR-011**: BaseTool MUST 定義 `execute()` 抽象方法
- **FR-012**: ToolRegistry MUST 提供 `get_openai_tools()` 輸出 OpenAI 格式

#### 資料結構

- **FR-013**: 系統 MUST 定義 `ToolResult` 資料結構（success, data, error）
- **FR-014**: 系統 MUST 定義 `ChatMessage` 資料結構（role, content, tool_calls）

### Non-Functional Requirements

- **NFR-001**: 程式碼 MUST 通過 Ruff 檢查
- **NFR-002**: 關鍵類別 MUST 有型別標註
- **NFR-003**: 系統 MUST 透過環境變數配置 API Key

---

## Key Entities

### ToolResult

工具執行結果結構。

```python
class ToolResult(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None
```

### ChatMessage

對話訊息結構。

```python
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list | None = None
    tool_call_id: str | None = None
```

### BaseTool

工具抽象基底類別。

```python
class BaseTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult: ...
```

### ToolRegistry

工具註冊中心。

```python
class ToolRegistry:
    def register(self, tool: BaseTool) -> None: ...
    def get(self, name: str) -> BaseTool | None: ...
    def get_openai_tools(self) -> list[dict]: ...
    async def execute(self, name: str, arguments: dict) -> ToolResult: ...
```

### LLMClient

LLM 客戶端。

```python
class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"): ...
    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> ChatMessage: ...
```

---

## Success Criteria

- **SC-001**: `uv run python -m voice_assistant.main` 可正常執行
- **SC-002**: LLMClient 單元測試通過（含 mock）
- **SC-003**: ToolRegistry 單元測試通過
- **SC-004**: 所有程式碼通過 Ruff 檢查
- **SC-005**: 核心類別有完整型別標註

---

## Out of Scope

本規格 **不包含**：

- 語音輸入/輸出（見 001-fastrtc-voice-pipeline）
- 具體查詢工具實作（見 002/003/004）
- 完整對話流程整合
- Web UI
- Docker 部署配置

---

## Dependencies

- **Constitution**: [constitution.md](../../.specify/memory/constitution.md)
- **External**: OpenAI API（OPENAI_API_KEY）
