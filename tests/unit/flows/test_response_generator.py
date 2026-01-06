"""回應產生節點單元測試。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from voice_assistant.flows.nodes.response_generator import (
    _generate_fallback_response,
    create_response_generator_node,
)
from voice_assistant.flows.state import FlowState, WeatherInfo


class TestResponseGeneratorNode:
    """回應產生節點測試。"""

    @pytest.mark.asyncio
    async def test_generate_weather_response(self) -> None:
        """應能產生天氣回應。"""
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content="台北現在晴朗，氣溫二十五度，很適合出門！",
            )
        )

        generate = create_response_generator_node(mock_llm)
        state: FlowState = {
            "user_input": "台北天氣如何",
            "intent": "weather",
            "tool_result": {
                "city": "台北",
                "temperature": 25.0,
                "weather": "晴朗",
            },
        }

        result = await generate(state)

        assert "response" in result
        assert "台北" in result["response"]

    @pytest.mark.asyncio
    async def test_generate_travel_response(self) -> None:
        """應能產生旅遊回應。"""
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content="高雄今天天氣不錯，推薦您去西子灣看夕陽！",
            )
        )

        generate = create_response_generator_node(mock_llm)
        state: FlowState = {
            "user_input": "我想去高雄玩",
            "intent": "travel",
            "travel_state": {
                "destination": "高雄",
                "destination_valid": True,
                "weather_data": WeatherInfo(
                    city="高雄",
                    temperature=28.0,
                    weather="晴朗",
                    weather_code=0,
                ),
                "weather_suitable": True,
                "recommendation_type": "outdoor",
                "recommendations": ["西子灣", "旗津海岸", "蓮池潭"],
            },
        }

        result = await generate(state)

        assert "response" in result

    @pytest.mark.asyncio
    async def test_generate_error_response(self) -> None:
        """應能產生錯誤回應。"""
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content="抱歉，目前無法取得天氣資訊，請稍後再試。",
            )
        )

        generate = create_response_generator_node(mock_llm)
        state: FlowState = {
            "user_input": "台北天氣如何",
            "intent": "weather",
            "error": "api_error: 天氣服務暫時無法使用",
        }

        result = await generate(state)

        assert "response" in result


class TestFallbackResponse:
    """降級回應測試。"""

    def test_fallback_error_response(self) -> None:
        """有錯誤時應產生錯誤回應。"""
        state: FlowState = {
            "user_input": "台北天氣",
            "error": "天氣服務暫時無法使用",
        }

        result = _generate_fallback_response(state)

        assert "抱歉" in result
        assert "天氣服務暫時無法使用" in result

    def test_fallback_travel_suitable_response(self) -> None:
        """旅遊天氣適合時應產生適當回應。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "intent": "travel",
            "travel_state": {
                "destination": "台北",
                "weather_suitable": True,
                "recommendations": ["象山步道", "陽明山"],
            },
        }

        result = _generate_fallback_response(state)

        assert "台北" in result
        assert "適合出遊" in result
        assert "象山步道" in result

    def test_fallback_travel_not_suitable_response(self) -> None:
        """旅遊天氣不適合時應產生適當回應。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "intent": "travel",
            "travel_state": {
                "destination": "台北",
                "weather_suitable": False,
                "recommendations": ["台北101觀景台", "故宮博物院"],
            },
        }

        result = _generate_fallback_response(state)

        assert "台北" in result
        assert "不太適合戶外" in result

    def test_fallback_weather_response(self) -> None:
        """天氣工具結果應產生適當回應。"""
        state: FlowState = {
            "user_input": "台北天氣",
            "intent": "weather",
            "tool_result": {
                "city": "台北",
                "temperature": 25,
                "weather": "晴朗",
            },
        }

        result = _generate_fallback_response(state)

        assert "台北" in result
        assert "25" in result

    def test_fallback_default_response(self) -> None:
        """無法處理時應產生預設回應。"""
        state: FlowState = {
            "user_input": "你好",
        }

        result = _generate_fallback_response(state)

        assert "抱歉" in result
