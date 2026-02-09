"""FlowRegistry 單元測試。"""

from __future__ import annotations

import pytest

from voice_assistant.flows.base import BaseFlowExecutor
from voice_assistant.flows.exceptions import FlowNotFoundError
from voice_assistant.flows.registry import FlowRegistry


class _StubExecutor(BaseFlowExecutor):
    """測試用的簡易執行器。"""

    def __init__(self, name: str = "stub") -> None:
        self._name = name

    @property
    def flow_name(self) -> str:
        return self._name

    async def execute(self, user_input: str) -> str:
        return f"stub: {user_input}"


class TestFlowRegistry:
    """測試 FlowRegistry 的註冊、查詢、列舉功能。"""

    def test_register_and_get(self) -> None:
        """註冊後可以透過 get 取得。"""
        registry = FlowRegistry()
        executor = _StubExecutor("test_flow")
        registry.register(executor)
        assert registry.get("test_flow") is executor

    def test_register_duplicate_raises_value_error(self) -> None:
        """重複註冊同名流程拋出 ValueError。"""
        registry = FlowRegistry()
        registry.register(_StubExecutor("dup"))
        with pytest.raises(ValueError, match="已註冊"):
            registry.register(_StubExecutor("dup"))

    def test_get_nonexistent_raises_flow_not_found_error(self) -> None:
        """取得不存在的流程拋出 FlowNotFoundError。"""
        registry = FlowRegistry()
        with pytest.raises(FlowNotFoundError, match="not_exist"):
            registry.get("not_exist")

    def test_list_flows_empty(self) -> None:
        """空的 registry 回傳空列表。"""
        registry = FlowRegistry()
        assert registry.list_flows() == []

    def test_list_flows_returns_registered_names(self) -> None:
        """list_flows 回傳所有已註冊的流程名稱。"""
        registry = FlowRegistry()
        registry.register(_StubExecutor("alpha"))
        registry.register(_StubExecutor("beta"))
        registry.register(_StubExecutor("gamma"))
        assert sorted(registry.list_flows()) == ["alpha", "beta", "gamma"]

    def test_has_returns_true_for_registered(self) -> None:
        """has 對已註冊流程回傳 True。"""
        registry = FlowRegistry()
        registry.register(_StubExecutor("exists"))
        assert registry.has("exists") is True

    def test_has_returns_false_for_unregistered(self) -> None:
        """has 對未註冊流程回傳 False。"""
        registry = FlowRegistry()
        assert registry.has("missing") is False

    def test_flow_not_found_error_contains_flow_name(self) -> None:
        """FlowNotFoundError 包含流程名稱。"""
        error = FlowNotFoundError("my_flow")
        assert error.flow_name == "my_flow"
        assert "my_flow" in str(error)

    def test_register_multiple_executors(self) -> None:
        """可以註冊多個不同名稱的執行器。"""
        registry = FlowRegistry()
        executors = [_StubExecutor(f"flow_{i}") for i in range(5)]
        for executor in executors:
            registry.register(executor)
        assert len(registry.list_flows()) == 5
        for executor in executors:
            assert registry.get(executor.flow_name) is executor


class TestFlowRegistryIntegration:
    """FlowRegistry 整合測試：模擬實際三種流程模式的完整場景。"""

    def test_register_all_three_flow_modes(self) -> None:
        """建立 FlowRegistry → 註冊 tools / langgraph / multi_agent → get/list 正確。"""
        registry = FlowRegistry()
        tools_exec = _StubExecutor("tools")
        langgraph_exec = _StubExecutor("langgraph")
        multi_agent_exec = _StubExecutor("multi_agent")

        registry.register(tools_exec)
        registry.register(langgraph_exec)
        registry.register(multi_agent_exec)

        assert registry.get("tools") is tools_exec
        assert registry.get("langgraph") is langgraph_exec
        assert registry.get("multi_agent") is multi_agent_exec
        assert sorted(registry.list_flows()) == ["langgraph", "multi_agent", "tools"]

    def test_fallback_when_preferred_flow_not_found(self) -> None:
        """preferred_flow_mode 指向不存在流程時，has() 回傳 False 供呼叫端 fallback。"""
        registry = FlowRegistry()
        registry.register(_StubExecutor("tools"))

        # 角色偏好 multi_agent，但未註冊
        assert registry.has("multi_agent") is False
        # 呼叫端應 fallback 到已註冊的流程
        assert registry.has("tools") is True

    @pytest.mark.asyncio
    async def test_registered_executor_can_execute(self) -> None:
        """透過 FlowRegistry 取得的執行器可正確執行。"""
        registry = FlowRegistry()
        registry.register(_StubExecutor("tools"))

        executor = registry.get("tools")
        result = await executor.execute("你好")
        assert result == "stub: 你好"
