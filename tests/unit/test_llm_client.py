"""Unit tests for LLM client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.fixtures.mock_responses import (
    MOCK_SIMPLE_RESPONSE,
    MOCK_TOOL_CALL_RESPONSE,
)
from voice_assistant.llm.client import LLMClient
from voice_assistant.llm.errors import LLMAuthenticationError, LLMConnectionError
from voice_assistant.llm.schemas import ChatMessage


class TestLLMClient:
    """Tests for LLMClient class."""

    def test_init(self, mock_api_key: str) -> None:
        """Test client initialization."""
        client = LLMClient(api_key=mock_api_key)
        assert client.model == "gpt-4o-mini"

    def test_init_custom_model(self, mock_api_key: str) -> None:
        """Test client initialization with custom model."""
        client = LLMClient(api_key=mock_api_key, model="gpt-4")
        assert client.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_chat_simple_response(self, mock_api_key: str) -> None:
        """Test chat with simple text response."""
        client = LLMClient(api_key=mock_api_key)

        with patch.object(
            client.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=MOCK_SIMPLE_RESPONSE,
        ):
            messages = [ChatMessage(role="user", content="你好")]
            response = await client.chat(messages)

            assert response.role == "assistant"
            assert response.content == "你好！有什麼我可以幫助你的嗎？"
            assert response.tool_calls is None

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self, mock_api_key: str) -> None:
        """Test chat with system prompt."""
        client = LLMClient(api_key=mock_api_key)

        with patch.object(
            client.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=MOCK_SIMPLE_RESPONSE,
        ) as mock_create:
            messages = [ChatMessage(role="user", content="你好")]
            await client.chat(messages, system_prompt="你是一個助理")

            # Verify system prompt was prepended
            call_args = mock_create.call_args
            sent_messages = call_args.kwargs["messages"]
            assert sent_messages[0]["role"] == "system"
            assert sent_messages[0]["content"] == "你是一個助理"

    @pytest.mark.asyncio
    async def test_chat_with_tool_call_response(self, mock_api_key: str) -> None:
        """Test chat response with tool calls."""
        client = LLMClient(api_key=mock_api_key)

        with patch.object(
            client.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=MOCK_TOOL_CALL_RESPONSE,
        ):
            messages = [ChatMessage(role="user", content="台北天氣如何")]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "查詢天氣",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ]
            response = await client.chat(messages, tools=tools)

            assert response.role == "assistant"
            assert response.content is None
            assert response.tool_calls is not None
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].function["name"] == "get_weather"

    @pytest.mark.asyncio
    async def test_chat_authentication_error(self, mock_api_key: str) -> None:
        """Test authentication error handling."""
        from openai import AuthenticationError

        client = LLMClient(api_key=mock_api_key)

        mock_error = AuthenticationError(
            message="Invalid API key",
            response=MagicMock(status_code=401),
            body=None,
        )

        with patch.object(
            client.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=mock_error,
        ):
            messages = [ChatMessage(role="user", content="test")]

            with pytest.raises(LLMAuthenticationError):
                await client.chat(messages)

    @pytest.mark.asyncio
    async def test_chat_connection_error(self, mock_api_key: str) -> None:
        """Test connection error handling."""
        from openai import APIConnectionError

        client = LLMClient(api_key=mock_api_key)

        mock_error = APIConnectionError(request=MagicMock())

        with patch.object(
            client.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=mock_error,
        ):
            messages = [ChatMessage(role="user", content="test")]

            with pytest.raises(LLMConnectionError):
                await client.chat(messages)
