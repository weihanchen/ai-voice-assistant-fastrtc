"""ToolCallingExecutor 單元測試。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from voice_assistant.flows.tool_calling_executor import ToolCallingExecutor
from voice_assistant.flows.visualization import NodeStatus
from voice_assistant.llm.schemas import ChatMessage, ToolCall


class TestToolCallingExecutor:
    """測試 ToolCallingExecutor 的基本行為。"""

    def _create_executor(
        self,
        llm_client: MagicMock | None = None,
        tool_registry: MagicMock | None = None,
        system_prompt: str = "test prompt",
    ) -> ToolCallingExecutor:
        """建立測試用的 ToolCallingExecutor。"""
        client = llm_client or MagicMock()
        registry = tool_registry or MagicMock()
        return ToolCallingExecutor(
            llm_client=client,
            tool_registry=registry,
            system_prompt_provider=lambda: system_prompt,
        )

    def test_flow_name(self) -> None:
        """flow_name 回傳 'tools'。"""
        executor = self._create_executor()
        assert executor.flow_name == "tools"

    def test_get_visualization_returns_mermaid(self) -> None:
        """get_visualization() 回傳 Mermaid 格式的流程圖。"""
        executor = self._create_executor()
        result = executor.get_visualization()
        assert isinstance(result, str)
        assert "graph TD" in result
        assert "llm_call" in result
        assert "tool_execute" in result
        assert "response_generate" in result

    @pytest.mark.asyncio
    async def test_execute_no_tool_calls(self) -> None:
        """無 tool_calls 時直接回傳 LLM 回應。"""
        llm_client = MagicMock()
        llm_response = ChatMessage(role="assistant", content="直接回答")
        llm_client.chat = AsyncMock(return_value=llm_response)

        tool_registry = MagicMock()
        tool_registry.get_openai_tools.return_value = []

        executor = self._create_executor(
            llm_client=llm_client,
            tool_registry=tool_registry,
        )

        result = await executor.execute("你好")
        assert result == "直接回答"
        llm_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_tool_calls(self) -> None:
        """有 tool_calls 時執行工具並再次呼叫 LLM。"""
        # 使用 ToolCall Pydantic 模型
        tool_call = ToolCall(
            id="call_123",
            function={
                "name": "get_weather",
                "arguments": '{"city": "台北"}',
            },
        )

        # 第一次 LLM 回傳帶 tool_calls
        first_response = ChatMessage(
            role="assistant",
            content=None,
            tool_calls=[tool_call],
        )

        # 第二次 LLM 回傳最終結果
        final_response = ChatMessage(
            role="assistant",
            content="台北今天天氣晴朗",
        )

        llm_client = MagicMock()
        llm_client.chat = AsyncMock(side_effect=[first_response, final_response])

        # 設定 tool registry
        tool_result = MagicMock()
        tool_result.to_content.return_value = '{"temperature": 25}'

        tool_registry = MagicMock()
        tool_registry.get_openai_tools.return_value = [{"type": "function"}]
        tool_registry.execute = AsyncMock(return_value=tool_result)

        executor = self._create_executor(
            llm_client=llm_client,
            tool_registry=tool_registry,
        )

        result = await executor.execute("台北天氣如何")
        assert result == "台北今天天氣晴朗"
        assert llm_client.chat.call_count == 2
        tool_registry.execute.assert_called_once_with("get_weather", {"city": "台北"})

    @pytest.mark.asyncio
    async def test_execute_with_invalid_json_arguments(self) -> None:
        """工具參數 JSON 解析失敗時繼續處理。"""
        tool_call = ToolCall(
            id="call_456",
            function={
                "name": "bad_tool",
                "arguments": "invalid json",
            },
        )

        first_response = ChatMessage(
            role="assistant",
            content=None,
            tool_calls=[tool_call],
        )

        final_response = ChatMessage(
            role="assistant",
            content="發生了一些問題",
        )

        llm_client = MagicMock()
        llm_client.chat = AsyncMock(side_effect=[first_response, final_response])

        tool_registry = MagicMock()
        tool_registry.get_openai_tools.return_value = []
        tool_registry.execute = AsyncMock()

        executor = self._create_executor(
            llm_client=llm_client,
            tool_registry=tool_registry,
        )

        result = await executor.execute("test")
        assert result == "發生了一些問題"
        # 工具不應被呼叫（JSON 解析失敗）
        tool_registry.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_uses_system_prompt_provider(self) -> None:
        """execute 使用 system_prompt_provider 提供的提示詞。"""
        llm_client = MagicMock()
        llm_response = ChatMessage(role="assistant", content="回應")
        llm_client.chat = AsyncMock(return_value=llm_response)

        tool_registry = MagicMock()
        tool_registry.get_openai_tools.return_value = []

        custom_prompt = "自訂系統提示詞"
        executor = self._create_executor(
            llm_client=llm_client,
            tool_registry=tool_registry,
            system_prompt=custom_prompt,
        )

        await executor.execute("test")

        # 驗證系統提示詞被傳入 LLM
        call_kwargs = llm_client.chat.call_args
        assert call_kwargs.kwargs.get("system_prompt") == custom_prompt


class TestToolCallingExecutorCallback:
    """測試 ToolCallingExecutor 的 on_node_change callback 行為。"""

    def _create_executor(
        self,
        llm_client: MagicMock | None = None,
        tool_registry: MagicMock | None = None,
    ) -> ToolCallingExecutor:
        """建立測試用 executor。"""
        client = llm_client or MagicMock()
        registry = tool_registry or MagicMock()
        return ToolCallingExecutor(
            llm_client=client,
            tool_registry=registry,
            system_prompt_provider=lambda: "test",
        )

    @pytest.mark.asyncio
    async def test_callback_no_tool_calls(self) -> None:
        """無 tool_calls 時 callback 追蹤 llm_call 完整流程。"""
        llm_client = MagicMock()
        llm_client.chat = AsyncMock(
            return_value=ChatMessage(role="assistant", content="回應")
        )
        tool_registry = MagicMock()
        tool_registry.get_openai_tools.return_value = []

        executor = self._create_executor(llm_client, tool_registry)

        changes: list[tuple[str, NodeStatus]] = []
        await executor.execute(
            "test", on_node_change=lambda n, s: changes.append((n, s))
        )

        # llm_call 應該 RUNNING → COMPLETED
        assert ("llm_call", NodeStatus.RUNNING) in changes
        assert ("llm_call", NodeStatus.COMPLETED) in changes
        # 無 tool_calls 時，tool_execute 和 response_generate 直接 COMPLETED
        assert ("tool_execute", NodeStatus.COMPLETED) in changes
        assert ("response_generate", NodeStatus.COMPLETED) in changes

    @pytest.mark.asyncio
    async def test_callback_with_tool_calls(self) -> None:
        """有 tool_calls 時 callback 追蹤完整 3 階段流程。"""
        tool_call = ToolCall(
            id="call_1",
            function={"name": "get_weather", "arguments": '{"city": "台北"}'},
        )
        first_response = ChatMessage(
            role="assistant", content=None, tool_calls=[tool_call]
        )
        final_response = ChatMessage(role="assistant", content="結果")

        llm_client = MagicMock()
        llm_client.chat = AsyncMock(side_effect=[first_response, final_response])

        tool_result = MagicMock()
        tool_result.to_content.return_value = "{}"
        tool_registry = MagicMock()
        tool_registry.get_openai_tools.return_value = []
        tool_registry.execute = AsyncMock(return_value=tool_result)

        executor = self._create_executor(llm_client, tool_registry)

        changes: list[tuple[str, NodeStatus]] = []
        await executor.execute(
            "test", on_node_change=lambda n, s: changes.append((n, s))
        )

        # 驗證完整的 3 階段 callback 順序
        expected = [
            ("llm_call", NodeStatus.RUNNING),
            ("llm_call", NodeStatus.COMPLETED),
            ("tool_execute", NodeStatus.RUNNING),
            ("tool_execute", NodeStatus.COMPLETED),
            ("response_generate", NodeStatus.RUNNING),
            ("response_generate", NodeStatus.COMPLETED),
        ]
        assert changes == expected

    @pytest.mark.asyncio
    async def test_no_callback_does_not_error(self) -> None:
        """不傳 callback 時不應報錯。"""
        llm_client = MagicMock()
        llm_client.chat = AsyncMock(
            return_value=ChatMessage(role="assistant", content="ok")
        )
        tool_registry = MagicMock()
        tool_registry.get_openai_tools.return_value = []

        executor = self._create_executor(llm_client, tool_registry)
        result = await executor.execute("test")
        assert result == "ok"
