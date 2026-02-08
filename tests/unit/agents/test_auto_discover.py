"""discover_agents() 單元測試。"""

from __future__ import annotations

from unittest.mock import MagicMock

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.graph import discover_agents
from voice_assistant.agents.state import AgentType
from voice_assistant.agents.supervisor import SupervisorAgent


class TestDiscoverAgents:
    """測試 discover_agents() 自動發現機制。"""

    def _make_deps(self):
        """建立 mock 依賴。"""
        llm_client = MagicMock()
        tool_registry = MagicMock()
        return llm_client, tool_registry

    def test_discovers_four_agents(self) -> None:
        """discover_agents 能發現 4 個 Agent（Weather, Finance, Travel, General）。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(llm_client, tool_registry)

        assert AgentType.WEATHER in agents
        assert AgentType.FINANCE in agents
        assert AgentType.TRAVEL in agents
        assert AgentType.GENERAL in agents
        assert len(agents) == 4

    def test_does_not_register_base_agent(self) -> None:
        """discover_agents 不會註冊 BaseAgent 本身。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(llm_client, tool_registry)

        for agent in agents.values():
            assert type(agent) is not BaseAgent

    def test_does_not_register_supervisor_agent(self) -> None:
        """discover_agents 不會註冊 SupervisorAgent。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(llm_client, tool_registry)

        for agent in agents.values():
            assert not isinstance(agent, SupervisorAgent)

    def test_agents_are_correct_types(self) -> None:
        """發現的 Agent 都是 BaseAgent 的子類別。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(llm_client, tool_registry)

        for agent in agents.values():
            assert isinstance(agent, BaseAgent)

    def test_agent_types_match_instances(self) -> None:
        """每個 Agent 的 agent_type 與 dict key 一致。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(llm_client, tool_registry)

        for agent_type, agent in agents.items():
            assert agent.agent_type == agent_type

    def test_nonexistent_package_returns_empty(self) -> None:
        """傳入不存在的套件名稱回傳空 dict。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(
            llm_client, tool_registry, package_name="nonexistent.package"
        )
        assert agents == {}

    def test_weather_agent_receives_tool_registry(self) -> None:
        """WeatherAgent 應收到 tool_registry。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(llm_client, tool_registry)

        weather = agents[AgentType.WEATHER]
        assert hasattr(weather, "_tool_registry")
        assert weather._tool_registry is tool_registry

    def test_general_agent_receives_llm_client(self) -> None:
        """GeneralAgent 應收到 llm_client。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(llm_client, tool_registry)

        general = agents[AgentType.GENERAL]
        assert hasattr(general, "_llm_client")
        assert general._llm_client is llm_client

    def test_travel_agent_receives_both(self) -> None:
        """TravelAgent 應同時收到 tool_registry 和 llm_client。"""
        llm_client, tool_registry = self._make_deps()
        agents = discover_agents(llm_client, tool_registry)

        travel = agents[AgentType.TRAVEL]
        assert hasattr(travel, "_tool_registry")
        assert travel._tool_registry is tool_registry
        assert hasattr(travel, "_llm_client")
        assert travel._llm_client is llm_client
