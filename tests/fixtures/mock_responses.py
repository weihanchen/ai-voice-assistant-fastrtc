"""Mock responses for testing LLM client."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock


def create_mock_chat_response(
    content: str | None = "Hello! How can I help you?",
    tool_calls: list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Create a mock OpenAI chat completion response."""
    mock_response = MagicMock()
    mock_message = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = content

    if tool_calls:
        mock_tool_calls = []
        for tc in tool_calls:
            mock_tc = MagicMock()
            mock_tc.id = tc.get("id", "call_123")
            mock_tc.type = tc.get("type", "function")
            mock_tc.function = MagicMock()
            mock_tc.function.name = tc["function"]["name"]
            mock_tc.function.arguments = tc["function"]["arguments"]
            mock_tool_calls.append(mock_tc)
        mock_message.tool_calls = mock_tool_calls
    else:
        mock_message.tool_calls = None

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response.choices = [mock_choice]
    return mock_response


MOCK_SIMPLE_RESPONSE = create_mock_chat_response(
    content="你好！有什麼我可以幫助你的嗎？"
)

MOCK_TOOL_CALL_RESPONSE = create_mock_chat_response(
    content=None,
    tool_calls=[
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"city": "台北"}',
            },
        }
    ],
)
