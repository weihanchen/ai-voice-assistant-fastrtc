"""美食推薦流程測試。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from voice_assistant.flows.state import FlowState, FoodRecommendInfo


class TestExtractCityNode:
    """extract_city 節點測試。"""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """模擬 LLM 客戶端。"""
        client = MagicMock()
        client.chat = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_extract_city_正常情境(self, mock_llm_client: MagicMock) -> None:
        """測試 extract_city 節點的正常執行。"""
        from voice_assistant.flows.nodes.food.extract_city import (
            create_extract_city_node,
        )
        from voice_assistant.llm.schemas import ChatMessage

        # 設定 mock 回傳值
        mock_response = ChatMessage(role="assistant", content='{"city": "台北"}')
        mock_llm_client.chat.return_value = mock_response

        # 建立節點並執行
        node_fn = create_extract_city_node(mock_llm_client)
        state: FlowState = {"user_input": "台北有什麼好吃的"}
        result = await node_fn(state)

        # 驗證
        assert "food_state" in result
        assert result["food_state"]["city"] == "台北"

    @pytest.mark.asyncio
    async def test_extract_city_無法識別(self, mock_llm_client: MagicMock) -> None:
        """測試 extract_city 節點無法識別城市。"""
        from voice_assistant.flows.nodes.food.extract_city import (
            create_extract_city_node,
        )
        from voice_assistant.llm.schemas import ChatMessage

        # 設定 mock 回傳值
        mock_response = ChatMessage(role="assistant", content='{"city": null}')
        mock_llm_client.chat.return_value = mock_response

        node_fn = create_extract_city_node(mock_llm_client)
        state: FlowState = {"user_input": "推薦美食"}
        result = await node_fn(state)

        # 驗證錯誤處理
        assert "error" in result

    @pytest.mark.asyncio
    async def test_extract_city_異常情境(self, mock_llm_client: MagicMock) -> None:
        """測試 extract_city 節點的錯誤處理。"""
        from voice_assistant.flows.nodes.food.extract_city import (
            create_extract_city_node,
        )

        # 設定 mock 拋出例外
        mock_llm_client.chat.side_effect = Exception("LLM 呼叫失敗")

        node_fn = create_extract_city_node(mock_llm_client)
        state: FlowState = {"user_input": "台北美食"}
        result = await node_fn(state)

        # 驗證錯誤處理
        assert "error" in result


class TestQueryWeatherNode:
    """query_weather 節點測試。"""

    @pytest.fixture
    def mock_tool_registry(self) -> MagicMock:
        """模擬工具註冊表。"""
        registry = MagicMock()
        return registry

    @pytest.mark.asyncio
    async def test_query_weather_正常情境(self, mock_tool_registry: MagicMock) -> None:
        """測試 query_weather 節點的正常執行。"""
        from voice_assistant.flows.nodes.food.query_weather import (
            create_query_weather_node,
        )
        from voice_assistant.tools.schemas import ToolResult

        # 設定 mock tool_registry.execute
        mock_tool_registry.execute = AsyncMock(
            return_value=ToolResult(
                success=True,
                data={
                    "temperature": 22.5,
                    "weather": "晴天",
                },
            )
        )

        # 建立節點並執行
        node_fn = create_query_weather_node(mock_tool_registry)
        state: FlowState = {"food_state": {"city": "台北"}}
        result = await node_fn(state)

        # 驗證
        assert "food_state" in result
        food_state = result["food_state"]
        assert "weather_info" in food_state
        assert food_state["weather_info"].city == "台北"
        assert food_state["weather_info"].temperature == 22.5

    @pytest.mark.asyncio
    async def test_query_weather_缺少城市(self, mock_tool_registry: MagicMock) -> None:
        """測試 query_weather 節點缺少城市參數。"""
        from voice_assistant.flows.nodes.food.query_weather import (
            create_query_weather_node,
        )

        node_fn = create_query_weather_node(mock_tool_registry)
        state: FlowState = {"food_state": {}}
        result = await node_fn(state)

        # 驗證錯誤處理
        assert "error" in result


class TestDecideVenueTypeNode:
    """decide_venue_type 節點測試。"""

    @pytest.mark.asyncio
    async def test_decide_venue_type_戶外(self) -> None:
        """測試適合戶外的天氣。"""
        from voice_assistant.flows.nodes.food.venue_decision import decide_venue_type

        weather_info = FoodRecommendInfo(
            city="台北",
            temperature=22.0,
            weather="晴天",
            is_outdoor_friendly=False,
        )
        state: FlowState = {"food_state": {"weather_info": weather_info}}
        result = await decide_venue_type(state)

        # 驗證
        assert "food_state" in result
        assert result["food_state"]["venue_type"] == "outdoor"
        assert result["food_state"]["weather_info"].is_outdoor_friendly is True

    @pytest.mark.asyncio
    async def test_decide_venue_type_室內(self) -> None:
        """測試適合室內的天氣。"""
        from voice_assistant.flows.nodes.food.venue_decision import decide_venue_type

        weather_info = FoodRecommendInfo(
            city="台北",
            temperature=10.0,
            weather="雨天",
            is_outdoor_friendly=False,
        )
        state: FlowState = {"food_state": {"weather_info": weather_info}}
        result = await decide_venue_type(state)

        # 驗證
        assert "food_state" in result
        assert result["food_state"]["venue_type"] == "indoor"
        assert result["food_state"]["weather_info"].is_outdoor_friendly is False


class TestGenerateRecommendationNode:
    """generate_recommendation 節點測試。"""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """模擬 LLM 客戶端。"""
        client = MagicMock()
        client.chat = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_generate_recommendation_正常情境(
        self, mock_llm_client: MagicMock
    ) -> None:
        """測試 generate_recommendation 節點的正常執行。"""
        from voice_assistant.flows.nodes.food.generate_recommendation import (
            create_generate_recommendation_node,
        )
        from voice_assistant.llm.schemas import ChatMessage

        # 設定 mock 回傳值
        mock_response = ChatMessage(
            role="assistant",
            content="推薦以下戶外餐廳：1. 陽明山餐廳...",
        )
        mock_llm_client.chat.return_value = mock_response

        # 建立節點並執行
        node_fn = create_generate_recommendation_node(mock_llm_client)
        weather_info = FoodRecommendInfo(
            city="台北",
            temperature=22.0,
            weather="晴天",
            is_outdoor_friendly=True,
        )
        state: FlowState = {
            "food_state": {
                "weather_info": weather_info,
                "venue_type": "outdoor",
            }
        }
        result = await node_fn(state)

        # 驗證
        assert "response" in result
        assert "戶外餐廳" in result["response"]


class TestFoodRecommendFlowExecutor:
    """美食推薦流程執行器測試。"""

    @pytest.mark.asyncio
    async def test_flow_name(self) -> None:
        """測試 flow_name 屬性。"""
        from voice_assistant.flows.food_executor import FoodRecommendFlowExecutor

        executor = FoodRecommendFlowExecutor(
            llm_client=MagicMock(),
            tool_registry=MagicMock(),
        )
        assert executor.flow_name == "food"

    @pytest.mark.asyncio
    async def test_get_visualization(self) -> None:
        """測試 Mermaid 視覺化。"""
        from voice_assistant.flows.food_executor import FoodRecommendFlowExecutor

        executor = FoodRecommendFlowExecutor(
            llm_client=MagicMock(),
            tool_registry=MagicMock(),
        )
        viz = executor.get_visualization()
        assert viz is not None
        assert "graph TD" in viz
