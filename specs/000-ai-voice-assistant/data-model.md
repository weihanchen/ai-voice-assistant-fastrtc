# Data Model: AI Voice Assistant 核心架構

**Date**: 2025-12-23
**Spec**: [spec.md](./spec.md)

## Entities

### 1. ChatMessage

對話訊息結構，用於維護對話歷史與 LLM 互動。

```python
from typing import Literal, Any
from pydantic import BaseModel

class ToolCall(BaseModel):
    """LLM 請求的工具呼叫"""
    id: str
    type: str = "function"
    function: dict[str, Any]  # {"name": str, "arguments": str}

class ChatMessage(BaseModel):
    """對話訊息"""
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None  # 僅 role="tool" 時使用

    def to_openai_format(self) -> dict:
        """轉換為 OpenAI API 格式"""
        result = {"role": self.role}
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls:
            result["tool_calls"] = [tc.model_dump() for tc in self.tool_calls]
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result
```

**欄位說明**:

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| role | Literal | ✅ | system/user/assistant/tool |
| content | str \| None | ❌ | 訊息內容 |
| tool_calls | list[ToolCall] \| None | ❌ | LLM 請求的工具呼叫（assistant） |
| tool_call_id | str \| None | ❌ | 工具呼叫 ID（tool） |

---

### 2. ToolResult

工具執行結果結構。

```python
from typing import Any
from pydantic import BaseModel

class ToolResult(BaseModel):
    """工具執行結果"""
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None

    @classmethod
    def ok(cls, data: dict[str, Any]) -> "ToolResult":
        """建立成功結果"""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        """建立失敗結果"""
        return cls(success=False, error=error)

    def to_content(self) -> str:
        """轉換為 LLM 可讀的字串"""
        if self.success:
            import json
            return json.dumps(self.data, ensure_ascii=False)
        return f"Error: {self.error}"
```

**欄位說明**:

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| success | bool | ✅ | 是否執行成功 |
| data | dict \| None | ❌ | 成功時的資料 |
| error | str \| None | ❌ | 失敗時的錯誤訊息 |

**驗證規則**:
- `success=True` 時，`data` 應有值
- `success=False` 時，`error` 應有值

---

### 3. BaseTool

工具抽象基底類別。

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    """工具抽象基底"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名稱（用於 Function Calling）"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema 格式的參數定義"""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """執行工具"""
        ...

    def to_openai_tool(self) -> dict[str, Any]:
        """輸出 OpenAI Function Calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }
```

**屬性說明**:

| 屬性/方法 | 型別 | 說明 |
|----------|------|------|
| name | str (property) | 工具唯一識別名稱 |
| description | str (property) | 工具功能描述 |
| parameters | dict (property) | JSON Schema 參數定義 |
| execute() | async method | 執行工具邏輯 |
| to_openai_tool() | method | 轉換為 OpenAI 格式 |

---

### 4. Settings

應用程式配置。

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """應用程式配置"""
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # 未來擴充
    # log_level: str = "INFO"
    # api_timeout: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**欄位說明**:

| 欄位 | 型別 | 必填 | 預設值 | 環境變數 |
|------|------|------|--------|----------|
| openai_api_key | str | ✅ | - | OPENAI_API_KEY |
| openai_model | str | ❌ | gpt-4o-mini | OPENAI_MODEL |

---

## Relationships

```
┌─────────────┐
│  Settings   │
└──────┬──────┘
       │ uses
       ▼
┌─────────────┐         ┌─────────────┐
│  LLMClient  │◄────────│ ChatMessage │
└──────┬──────┘  sends  └─────────────┘
       │
       │ calls
       ▼
┌─────────────┐         ┌─────────────┐
│ToolRegistry │────────►│  BaseTool   │
└──────┬──────┘ manages └──────┬──────┘
       │                       │
       │ returns               │ returns
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│ ToolResult  │◄────────│ (concrete)  │
└─────────────┘         └─────────────┘
```

---

## State Transitions

### ToolResult States

```
┌─────────┐
│ Created │
└────┬────┘
     │
     ├─────────────────┐
     │                 │
     ▼                 ▼
┌─────────┐      ┌─────────┐
│ Success │      │ Failure │
│ (data)  │      │ (error) │
└─────────┘      └─────────┘
```

### ChatMessage Flow

```
User Input ──► ChatMessage(role="user")
                     │
                     ▼
              LLM Processing
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
Direct Reply    Tool Call      Out of Scope
(assistant)     (assistant     (assistant)
                tool_calls)
                     │
                     ▼
              Tool Execution
                     │
                     ▼
              ChatMessage(role="tool")
                     │
                     ▼
              Final Reply
              (assistant)
```
