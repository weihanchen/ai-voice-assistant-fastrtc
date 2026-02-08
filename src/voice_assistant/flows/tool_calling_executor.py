"""Tool Calling 流程執行器。

封裝直接 LLM Tool Calling 邏輯（原 VoicePipeline._process_with_legacy）。
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from voice_assistant.flows.base import BaseFlowExecutor
from voice_assistant.llm.schemas import ChatMessage
from voice_assistant.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient

logger = logging.getLogger(__name__)


class ToolCallingExecutor(BaseFlowExecutor):
    """Tool Calling 流程執行器。

    使用 LLM 的原生 Tool Calling 機制處理使用者輸入，
    對應 FlowMode.TOOLS。
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        system_prompt_provider: Callable[[], str],
    ) -> None:
        """初始化 Tool Calling 執行器。

        Args:
            llm_client: LLM 客戶端。
            tool_registry: 工具註冊表。
            system_prompt_provider: 提供當前系統提示詞的 callable。
        """
        self._llm_client = llm_client
        self._tool_registry = tool_registry
        self._system_prompt_provider = system_prompt_provider

    @property
    def flow_name(self) -> str:
        """流程名稱。"""
        return "tools"

    async def execute(self, user_input: str) -> str:
        """使用 Tool Calling 處理使用者輸入。

        Args:
            user_input: 使用者輸入文字。

        Returns:
            LLM 回應文字。
        """
        logger.info("[ToolCallingExecutor] 使用 Tool Calling 處理")
        user_message = ChatMessage(role="user", content=user_input)
        messages: list[ChatMessage] = [user_message]

        # 取得工具定義和當前 system_prompt
        tools = self._tool_registry.get_openai_tools()
        system_prompt = self._system_prompt_provider()

        # 第一次 LLM 呼叫
        llm_response = await self._llm_client.chat(
            messages, tools=tools, system_prompt=system_prompt
        )

        # 處理 Tool Calls（如果有）
        return await self._process_tool_calls(
            messages, llm_response, tools, system_prompt
        )

    async def _process_tool_calls(
        self,
        messages: list[ChatMessage],
        llm_response: ChatMessage,
        tools: list[dict],
        system_prompt: str,
    ) -> str:
        """處理 LLM 的 Tool Calls 回應。

        Args:
            messages: 目前的對話訊息列表。
            llm_response: LLM 回應（可能包含 tool_calls）。
            tools: 工具定義列表。
            system_prompt: 系統提示詞。

        Returns:
            最終的文字回應。
        """
        if not llm_response.tool_calls:
            return llm_response.content or ""

        logger.info(
            "[ToolCallingExecutor] LLM 要求呼叫工具: %s",
            [tc.function["name"] for tc in llm_response.tool_calls],
        )

        messages.append(llm_response)

        for tool_call in llm_response.tool_calls:
            tool_name = tool_call.function["name"]
            try:
                arguments = json.loads(tool_call.function["arguments"])
            except json.JSONDecodeError as e:
                logger.warning("[ToolCallingExecutor] 工具參數 JSON 解析失敗: %s", e)
                tool_message = ChatMessage(
                    role="tool",
                    content="Error: 無法解析工具參數",
                    tool_call_id=tool_call.id,
                )
                messages.append(tool_message)
                continue

            logger.info("[ToolCallingExecutor] 執行工具 %s", tool_name)
            result = await self._tool_registry.execute(tool_name, arguments)
            logger.info("[ToolCallingExecutor] 工具執行完成")

            tool_message = ChatMessage(
                role="tool",
                content=result.to_content(),
                tool_call_id=tool_call.id,
            )
            messages.append(tool_message)

        # 再次呼叫 LLM 產生最終回應
        final_response = await self._llm_client.chat(
            messages, tools=tools, system_prompt=system_prompt
        )

        return final_response.content or ""
