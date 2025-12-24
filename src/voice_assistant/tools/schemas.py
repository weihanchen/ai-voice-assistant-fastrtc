"""Tool schemas for voice assistant."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """工具執行結果結構。"""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None

    @classmethod
    def ok(cls, data: dict[str, Any]) -> ToolResult:
        """建立成功結果。"""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> ToolResult:
        """建立失敗結果。"""
        return cls(success=False, error=error)

    def to_content(self) -> str:
        """轉換為 LLM 可讀的字串。"""
        if self.success:
            return json.dumps(self.data, ensure_ascii=False)
        return f"Error: {self.error}"
