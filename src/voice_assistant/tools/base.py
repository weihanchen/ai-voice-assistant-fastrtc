"""Base tool class for voice assistant."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from voice_assistant.tools.schemas import ToolResult


class BaseTool(ABC):
    """工具抽象基底類別。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名稱（用於 Function Calling）。"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述。"""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema 格式的參數定義。"""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """執行工具。"""
        ...

    def to_openai_tool(self) -> dict[str, Any]:
        """輸出 OpenAI Function Calling 格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
