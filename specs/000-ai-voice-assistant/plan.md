# Implementation Plan: AI Voice Assistant 核心架構

**Branch**: `000-ai-voice-assistant` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Constitution**: [constitution.md](../../.specify/memory/constitution.md)

## Summary

建立 AI 語音助理的專案骨架與核心框架，包含：
- 專案目錄結構與 `pyproject.toml` 配置
- `LLMClient` 類別封裝 OpenAI API
- `BaseTool` 與 `ToolRegistry` 框架
- `ToolResult`、`ChatMessage` 資料結構
- 環境變數與配置管理

**此階段僅建立骨架，不含完整功能實作。**

---

## Technical Context

**Language/Version**: Python 3.14（依據 Constitution）
**Package Manager**: uv >=0.5.x
**Primary Dependencies**:
- openai >=1.58.x（LLM SDK）
- pydantic >=2.10.x（資料驗證）

**Testing**: pytest >=8.x
**Linting**: Ruff >=0.8.x
**Target Platform**: Linux/Windows/macOS（開發環境）
**Project Type**: Single project（src layout）

**Performance Goals**: 此階段無效能要求
**Constraints**: 程式碼必須通過 Ruff 檢查、關鍵類別需有型別標註

---

## Constitution Check

*GATE: 必須在開始前通過，Phase 1 設計後重新檢查*

| 原則 | 檢查項目 | 狀態 |
|------|----------|------|
| **I. Tool-First** | BaseTool 抽象基底、ToolRegistry 註冊機制 | ✅ 符合 |
| **II. LLM Auto-Routing** | LLMClient 支援 Function Calling | ✅ 符合 |
| **III. Human-Friendly** | 此階段不涉及回覆生成 | N/A |
| **IV. Safe Boundary** | 此階段不涉及意圖判斷 | N/A |
| **V. Extensible Design** | LLM Provider 可抽象、Tool 自動註冊 | ✅ 符合 |
| **Technical Stack** | Python 3.14, uv, openai, pydantic, ruff, pytest | ✅ 符合 |
| **Quality Gates** | Ruff 檢查、型別標註 | ✅ 符合 |

**結果**: 通過，無需 Complexity Tracking

---

## Project Structure

### Documentation (this feature)

```text
specs/000-ai-voice-assistant/
├── spec.md              # 功能規格
├── plan.md              # 本檔案
├── research.md          # 技術研究
├── data-model.md        # 資料模型
├── contracts/           # 介面契約
│   ├── llm-client.md
│   └── tool-registry.md
└── tasks.md             # 任務清單（由 /speckit.tasks 生成）
```

### Source Code (repository root)

```text
src/
└── voice_assistant/
    ├── __init__.py
    ├── main.py              # 入口點（啟動驗證用）
    ├── config.py            # 環境變數與配置
    ├── llm/
    │   ├── __init__.py
    │   ├── client.py        # LLMClient 類別
    │   └── schemas.py       # ChatMessage 資料結構
    └── tools/
        ├── __init__.py
        ├── base.py          # BaseTool 抽象基底
        ├── registry.py      # ToolRegistry 類別
        └── schemas.py       # ToolResult 資料結構

tests/
├── __init__.py
├── conftest.py              # pytest fixtures
├── unit/
│   ├── __init__.py
│   ├── test_llm_client.py
│   └── test_tool_registry.py
└── fixtures/
    └── mock_responses.py    # Mock 資料
```

**Structure Decision**: 使用 src layout，符合 Python 最佳實踐。模組依功能分為 `llm/` 和 `tools/`。

---

## Module Design

### 1. config.py - 環境變數管理

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
```

### 2. llm/schemas.py - ChatMessage

```python
from typing import Literal
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list | None = None
    tool_call_id: str | None = None
```

### 3. llm/client.py - LLMClient

```python
from openai import AsyncOpenAI

class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> ChatMessage:
        # 實作 OpenAI API 呼叫
        ...
```

### 4. tools/schemas.py - ToolResult

```python
from pydantic import BaseModel

class ToolResult(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None
```

### 5. tools/base.py - BaseTool

```python
from abc import ABC, abstractmethod

class BaseTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        ...

    def to_openai_tool(self) -> dict:
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

### 6. tools/registry.py - ToolRegistry

```python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_openai_tools(self) -> list[dict]:
        return [tool.to_openai_tool() for tool in self._tools.values()]

    async def execute(self, name: str, arguments: dict) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool '{name}' not found")
        return await tool.execute(**arguments)
```

### 7. main.py - 入口點

```python
from voice_assistant.config import Settings

def main():
    settings = Settings()
    print(f"AI Voice Assistant 已啟動")
    print(f"使用模型: {settings.openai_model}")

if __name__ == "__main__":
    main()
```

---

## Configuration Files

### pyproject.toml

```toml
[project]
name = "voice-assistant"
version = "0.1.0"
description = "AI Voice Assistant with FastRTC"
requires-python = ">=3.14"
dependencies = [
    "openai>=1.58.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
]

[tool.ruff]
line-length = 88
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### .env.example

```bash
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

---

## Complexity Tracking

> 無違反 Constitution，不需要記錄

---

## Next Steps

1. 執行 `/speckit.tasks` 生成任務清單
2. 依任務順序實作各模組
3. 確保所有測試通過
4. 執行 Ruff 檢查
