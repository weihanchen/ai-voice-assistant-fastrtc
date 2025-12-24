"""AI Voice Assistant with FastRTC."""

from voice_assistant.config import Settings
from voice_assistant.llm import (
    ChatMessage,
    LLMAuthenticationError,
    LLMClient,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    ToolCall,
)
from voice_assistant.tools import BaseTool, ToolRegistry, ToolResult

__version__ = "0.1.0"

__all__ = [
    "BaseTool",
    "ChatMessage",
    "LLMAuthenticationError",
    "LLMClient",
    "LLMConnectionError",
    "LLMError",
    "LLMRateLimitError",
    "Settings",
    "ToolCall",
    "ToolRegistry",
    "ToolResult",
]
