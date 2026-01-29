"""LLM client for voice assistant."""

from __future__ import annotations

from typing import Any

from openai import (
    APIConnectionError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from voice_assistant.llm.errors import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
)
from voice_assistant.llm.schemas import ChatMessage, ToolCall


class LLMClient:
    """OpenAI LLM 客戶端。"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
        system_prompt: str | None = None,
    ) -> None:
        """
        初始化 LLM 客戶端。

        Args:
            api_key: OpenAI API Key
            model: 使用的模型名稱
            timeout: API 呼叫逾時秒數
            system_prompt: 預設系統提示詞（可為 None）
        """
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self._system_prompt = system_prompt

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
    ) -> ChatMessage:
        """
        發送對話請求。

        Args:
            messages: 對話歷史
            tools: OpenAI Function Calling 工具定義
            system_prompt: 系統提示詞（會插入到 messages 開頭，
                優先於預設 system_prompt）

        Returns:
            LLM 回應的 ChatMessage

        Raises:
            LLMError: API 呼叫失敗時
        """
        # 準備訊息列表
        openai_messages: list[dict[str, Any]] = []

        # 插入 system prompt，優先外部參數，其次實例層
        prompt = system_prompt if system_prompt is not None else self._system_prompt
        if prompt:
            openai_messages.append({"role": "system", "content": prompt})

        # 轉換訊息格式
        for msg in messages:
            openai_messages.append(msg.to_openai_format())

        # 準備 API 參數
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
        }

        # 只有在有 tools 時才加入參數
        if tools:
            kwargs["tools"] = tools

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except AuthenticationError as e:
            raise LLMAuthenticationError(str(e)) from e
        except APIConnectionError as e:
            raise LLMConnectionError(str(e)) from e
        except RateLimitError as e:
            raise LLMRateLimitError(str(e)) from e
        except Exception as e:
            raise LLMError(str(e)) from e

        # 轉換回應
        return self._convert_response(response)

    def set_system_prompt(self, prompt: str | None) -> None:
        """
        設定預設系統提示詞。
        Args:
            prompt: 系統提示詞（None 則清空）
        """
        self._system_prompt = prompt

    def _convert_response(self, response: Any) -> ChatMessage:
        """將 OpenAI 回應轉換為 ChatMessage。"""
        message = response.choices[0].message

        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    type=tc.type,
                    function={
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                )
                for tc in message.tool_calls
            ]

        return ChatMessage(
            role=message.role,
            content=message.content,
            tool_calls=tool_calls,
        )
