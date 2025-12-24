# Contract: ToolRegistry

**Date**: 2025-12-23
**Module**: `src/voice_assistant/tools/registry.py`

## Overview

工具註冊中心，管理所有 BaseTool 實例並提供 OpenAI Function Calling 格式輸出。

---

## Interface

```python
class ToolRegistry:
    """工具註冊中心"""

    def __init__(self) -> None:
        """初始化空的工具註冊表"""
        ...

    def register(self, tool: BaseTool) -> None:
        """
        註冊工具。

        Args:
            tool: BaseTool 實例

        Raises:
            ValueError: 工具名稱已存在時
        """
        ...

    def get(self, name: str) -> BaseTool | None:
        """
        依名稱取得工具。

        Args:
            name: 工具名稱

        Returns:
            BaseTool 實例，不存在時回傳 None
        """
        ...

    def get_openai_tools(self) -> list[dict]:
        """
        取得所有工具的 OpenAI Function Calling 格式。

        Returns:
            工具定義列表，格式符合 OpenAI tools 參數
        """
        ...

    async def execute(
        self,
        name: str,
        arguments: dict,
    ) -> ToolResult:
        """
        執行指定工具。

        Args:
            name: 工具名稱
            arguments: 工具參數

        Returns:
            ToolResult 執行結果
        """
        ...

    def list_tools(self) -> list[str]:
        """
        列出所有已註冊的工具名稱。

        Returns:
            工具名稱列表
        """
        ...
```

---

## Usage Example

```python
from voice_assistant.tools.registry import ToolRegistry
from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult

# 定義 Mock 工具
class MockTool(BaseTool):
    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "測試用工具"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            },
            "required": ["message"]
        }

    async def execute(self, message: str) -> ToolResult:
        return ToolResult.ok({"echo": message})

# 使用 Registry
registry = ToolRegistry()
registry.register(MockTool())

# 取得 OpenAI 格式
tools = registry.get_openai_tools()
# [{"type": "function", "function": {"name": "mock_tool", ...}}]

# 執行工具
result = await registry.execute("mock_tool", {"message": "hello"})
print(result.data)  # {"echo": "hello"}
```

---

## Behavior Specifications

### B-001: 重複註冊

當嘗試註冊已存在名稱的工具時，Registry MUST 拋出 `ValueError`。

```python
registry.register(tool1)  # name="weather"
registry.register(tool2)  # name="weather" → raises ValueError
```

### B-002: 不存在的工具

當 `get()` 查詢不存在的工具時，MUST 回傳 `None`（不拋出例外）。

當 `execute()` 執行不存在的工具時，MUST 回傳 `ToolResult.fail("Tool 'xxx' not found")`。

### B-003: 空 Registry

當 Registry 沒有任何工具時：
- `get_openai_tools()` MUST 回傳空列表 `[]`
- `list_tools()` MUST 回傳空列表 `[]`

### B-004: 執行錯誤處理

當工具執行過程中拋出例外時，Registry MUST 捕獲例外並回傳 `ToolResult.fail(str(exception))`。

```python
# 假設 tool.execute() 拋出 ValueError("invalid input")
result = await registry.execute("tool", {})
assert result.success is False
assert "invalid input" in result.error
```

### B-005: OpenAI 格式輸出

`get_openai_tools()` 輸出的每個工具 MUST 符合以下格式：

```python
{
    "type": "function",
    "function": {
        "name": str,        # 工具名稱
        "description": str,  # 工具描述
        "parameters": dict   # JSON Schema
    }
}
```
