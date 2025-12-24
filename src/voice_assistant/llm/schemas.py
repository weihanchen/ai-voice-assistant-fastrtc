"""LLM schemas for voice assistant."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class ToolCall(BaseModel):
    """LLM 請求的工具呼叫。"""

    id: str
    type: str = "function"
    function: dict[str, Any]  # {"name": str, "arguments": str}


class ChatMessage(BaseModel):
    """對話訊息結構。"""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None  # 僅 role="tool" 時使用

    def to_openai_format(self) -> dict[str, Any]:
        """轉換為 OpenAI API 格式。"""
        result: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls:
            result["tool_calls"] = [tc.model_dump() for tc in self.tool_calls]
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result
