"""BaseFlowExecutor 單元測試。"""

from __future__ import annotations

import pytest

from voice_assistant.flows.base import BaseFlowExecutor


class TestBaseFlowExecutorABC:
    """測試 BaseFlowExecutor 作為抽象基底類別的行為。"""

    def test_cannot_instantiate_directly(self) -> None:
        """無法直接實例化 ABC。"""
        with pytest.raises(TypeError, match="abstract"):
            BaseFlowExecutor()  # type: ignore[abstract]

    def test_subclass_must_implement_flow_name(self) -> None:
        """子類別必須實作 flow_name property。"""

        class IncompleteExecutor(BaseFlowExecutor):
            async def execute(self, user_input: str) -> str:
                return ""

        with pytest.raises(TypeError, match="abstract"):
            IncompleteExecutor()  # type: ignore[abstract]

    def test_subclass_must_implement_execute(self) -> None:
        """子類別必須實作 execute 方法。"""

        class IncompleteExecutor(BaseFlowExecutor):
            @property
            def flow_name(self) -> str:
                return "test"

        with pytest.raises(TypeError, match="abstract"):
            IncompleteExecutor()  # type: ignore[abstract]

    def test_get_visualization_default_returns_none(self) -> None:
        """get_visualization() 預設回傳 None。"""

        class ConcreteExecutor(BaseFlowExecutor):
            @property
            def flow_name(self) -> str:
                return "test"

            async def execute(self, user_input: str) -> str:
                return "response"

        executor = ConcreteExecutor()
        assert executor.get_visualization() is None

    def test_complete_subclass_can_be_instantiated(self) -> None:
        """完整實作所有抽象方法的子類別可以實例化。"""

        class ConcreteExecutor(BaseFlowExecutor):
            @property
            def flow_name(self) -> str:
                return "concrete"

            async def execute(self, user_input: str) -> str:
                return f"echo: {user_input}"

        executor = ConcreteExecutor()
        assert executor.flow_name == "concrete"

    def test_subclass_can_override_get_visualization(self) -> None:
        """子類別可以覆寫 get_visualization 提供視覺化。"""

        class VisualExecutor(BaseFlowExecutor):
            @property
            def flow_name(self) -> str:
                return "visual"

            async def execute(self, user_input: str) -> str:
                return ""

            def get_visualization(self) -> str | None:
                return "graph TD; A-->B;"

        executor = VisualExecutor()
        assert executor.get_visualization() == "graph TD; A-->B;"

    @pytest.mark.asyncio
    async def test_execute_returns_string(self) -> None:
        """execute() 應回傳字串。"""

        class EchoExecutor(BaseFlowExecutor):
            @property
            def flow_name(self) -> str:
                return "echo"

            async def execute(self, user_input: str) -> str:
                return f"echo: {user_input}"

        executor = EchoExecutor()
        result = await executor.execute("hello")
        assert result == "echo: hello"
