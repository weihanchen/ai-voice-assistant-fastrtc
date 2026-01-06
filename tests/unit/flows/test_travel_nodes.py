"""旅遊規劃節點單元測試。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from voice_assistant.flows.nodes.travel.evaluator import evaluate_weather
from voice_assistant.flows.nodes.travel.recommender import (
    recommend_indoor,
    recommend_outdoor,
)
from voice_assistant.flows.state import FlowState, WeatherInfo


class TestEvaluateWeather:
    """天氣評估節點測試。"""

    @pytest.mark.asyncio
    async def test_evaluate_sunny_weather_is_suitable(self) -> None:
        """晴朗天氣應評估為適合出遊。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
                "weather_data": WeatherInfo(
                    city="台北",
                    temperature=25.0,
                    weather="晴朗",
                    weather_code=0,
                ),
            },
        }

        result = await evaluate_weather(state)

        assert "travel_state" in result
        assert result["travel_state"]["weather_suitable"] is True

    @pytest.mark.asyncio
    async def test_evaluate_rainy_weather_is_not_suitable(self) -> None:
        """下雨天氣應評估為不適合出遊。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
                "weather_data": WeatherInfo(
                    city="台北",
                    temperature=25.0,
                    weather="小雨",
                    weather_code=51,
                ),
            },
        }

        result = await evaluate_weather(state)

        assert "travel_state" in result
        assert result["travel_state"]["weather_suitable"] is False

    @pytest.mark.asyncio
    async def test_evaluate_cold_weather_is_not_suitable(self) -> None:
        """低溫天氣應評估為不適合出遊。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
                "weather_data": WeatherInfo(
                    city="台北",
                    temperature=10.0,
                    weather="晴朗",
                    weather_code=0,
                ),
            },
        }

        result = await evaluate_weather(state)

        assert "travel_state" in result
        assert result["travel_state"]["weather_suitable"] is False

    @pytest.mark.asyncio
    async def test_evaluate_without_weather_data_returns_error(self) -> None:
        """缺少天氣資料應回傳錯誤。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
            },
        }

        result = await evaluate_weather(state)

        assert "error" in result


class TestRecommendOutdoor:
    """戶外建議節點測試。"""

    @pytest.mark.asyncio
    async def test_recommend_outdoor_for_taipei(self) -> None:
        """台北應有戶外建議。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
                "weather_suitable": True,
            },
        }

        result = await recommend_outdoor(state)

        assert "travel_state" in result
        assert result["travel_state"]["recommendation_type"] == "outdoor"
        assert len(result["travel_state"]["recommendations"]) <= 3
        assert "象山步道" in result["travel_state"]["recommendations"]

    @pytest.mark.asyncio
    async def test_recommend_outdoor_for_kaohsiung(self) -> None:
        """高雄應有戶外建議。"""
        state: FlowState = {
            "user_input": "我想去高雄玩",
            "travel_state": {
                "destination": "高雄",
                "destination_valid": True,
                "weather_suitable": True,
            },
        }

        result = await recommend_outdoor(state)

        assert "travel_state" in result
        assert result["travel_state"]["recommendation_type"] == "outdoor"
        assert "西子灣" in result["travel_state"]["recommendations"]


class TestRecommendIndoor:
    """室內建議節點測試。"""

    @pytest.mark.asyncio
    async def test_recommend_indoor_for_taipei(self) -> None:
        """台北應有室內建議。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
                "weather_suitable": False,
            },
        }

        result = await recommend_indoor(state)

        assert "travel_state" in result
        assert result["travel_state"]["recommendation_type"] == "indoor"
        assert len(result["travel_state"]["recommendations"]) <= 3
        assert "台北101觀景台" in result["travel_state"]["recommendations"]

    @pytest.mark.asyncio
    async def test_recommend_indoor_for_taichung(self) -> None:
        """台中應有室內建議。"""
        state: FlowState = {
            "user_input": "我想去台中玩",
            "travel_state": {
                "destination": "台中",
                "destination_valid": True,
                "weather_suitable": False,
            },
        }

        result = await recommend_indoor(state)

        assert "travel_state" in result
        assert result["travel_state"]["recommendation_type"] == "indoor"
        assert "國立自然科學博物館" in result["travel_state"]["recommendations"]

    @pytest.mark.asyncio
    async def test_recommend_without_destination_returns_error(self) -> None:
        """缺少目的地應回傳錯誤。"""
        state: FlowState = {
            "user_input": "我想去玩",
            "travel_state": {},
        }

        result = await recommend_indoor(state)

        assert "error" in result


class TestDestinationParserNode:
    """目的地解析節點測試。"""

    @pytest.mark.asyncio
    async def test_parse_taipei_destination(self) -> None:
        """應能解析台北目的地。"""
        from voice_assistant.flows.nodes.travel.destination import (
            create_destination_parser_node,
        )
        from voice_assistant.llm.schemas import ChatMessage

        # Mock LLM client
        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content='{"destination": "台北"}',
            )
        )

        parse_destination = create_destination_parser_node(mock_llm)
        state: FlowState = {"user_input": "我想去台北玩"}

        result = await parse_destination(state)

        assert "travel_state" in result
        assert result["travel_state"]["destination"] == "台北"
        assert result["travel_state"]["destination_valid"] is True

    @pytest.mark.asyncio
    async def test_parse_unsupported_destination(self) -> None:
        """不支援的城市應標記為無效。"""
        from voice_assistant.flows.nodes.travel.destination import (
            create_destination_parser_node,
        )
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content='{"destination": "東京"}',
            )
        )

        parse_destination = create_destination_parser_node(mock_llm)
        state: FlowState = {"user_input": "我想去東京玩"}

        result = await parse_destination(state)

        assert "travel_state" in result
        assert result["travel_state"]["destination"] == "東京"
        assert result["travel_state"]["destination_valid"] is False

    @pytest.mark.asyncio
    async def test_parse_no_destination(self) -> None:
        """無法識別目的地應標記為無效。"""
        from voice_assistant.flows.nodes.travel.destination import (
            create_destination_parser_node,
        )
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content='{"destination": null}',
            )
        )

        parse_destination = create_destination_parser_node(mock_llm)
        state: FlowState = {"user_input": "幫我規劃行程"}

        result = await parse_destination(state)

        assert "travel_state" in result
        assert result["travel_state"]["destination"] is None
        assert result["travel_state"]["destination_valid"] is False


class TestWeatherQueryNode:
    """天氣查詢節點測試。"""

    @pytest.mark.asyncio
    async def test_query_weather_success(self) -> None:
        """成功查詢天氣。"""
        from voice_assistant.flows.nodes.travel.weather import (
            create_weather_query_node,
        )
        from voice_assistant.tools.schemas import ToolResult

        # Mock ToolRegistry
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(
            return_value=ToolResult.ok(
                {
                    "city": "台北",
                    "temperature": 25.0,
                    "weather": "晴朗",
                    "weather_code": 0,
                    "humidity": 70.0,
                    "wind_speed": 5.0,
                }
            )
        )

        query_weather = create_weather_query_node(mock_registry)
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
            },
        }

        result = await query_weather(state)

        assert "travel_state" in result
        weather_data = result["travel_state"]["weather_data"]
        assert weather_data.city == "台北"
        assert weather_data.temperature == 25.0

    @pytest.mark.asyncio
    async def test_query_weather_failure(self) -> None:
        """天氣查詢失敗應回傳錯誤。"""
        from voice_assistant.flows.nodes.travel.weather import (
            create_weather_query_node,
        )
        from voice_assistant.tools.schemas import ToolResult

        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(
            return_value=ToolResult.fail("api_error: 無法取得天氣資訊")
        )

        query_weather = create_weather_query_node(mock_registry)
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
            },
        }

        result = await query_weather(state)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_weather_without_destination(self) -> None:
        """缺少目的地應回傳錯誤。"""
        from voice_assistant.flows.nodes.travel.weather import (
            create_weather_query_node,
        )

        mock_registry = MagicMock()
        query_weather = create_weather_query_node(mock_registry)
        state: FlowState = {
            "user_input": "我想去玩",
            "travel_state": {},
        }

        result = await query_weather(state)

        assert "error" in result
