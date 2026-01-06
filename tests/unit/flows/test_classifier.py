"""意圖分類節點單元測試。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from voice_assistant.flows.nodes.classifier import (
    _fallback_classify,
    create_classifier_node,
)
from voice_assistant.flows.state import FlowState


class TestClassifierNode:
    """意圖分類節點測試。"""

    @pytest.mark.asyncio
    async def test_classify_weather_intent(self) -> None:
        """應能分類天氣意圖。"""
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content='{"intent": "weather", "tool_name": "get_weather", "tool_args": {"city": "台北"}}',
            )
        )

        classify = create_classifier_node(mock_llm)
        state: FlowState = {"user_input": "台北天氣如何"}

        result = await classify(state)

        assert result["intent"] == "weather"
        assert result["tool_name"] == "get_weather"
        assert result["tool_args"]["city"] == "台北"

    @pytest.mark.asyncio
    async def test_classify_travel_intent(self) -> None:
        """應能分類旅遊意圖。"""
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content='{"intent": "travel", "tool_name": null, "tool_args": null}',
            )
        )

        classify = create_classifier_node(mock_llm)
        state: FlowState = {"user_input": "我想去高雄玩"}

        result = await classify(state)

        assert result["intent"] == "travel"
        assert result["tool_name"] is None

    @pytest.mark.asyncio
    async def test_classify_exchange_intent(self) -> None:
        """應能分類匯率意圖。"""
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content='{"intent": "exchange", "tool_name": "get_exchange_rate", "tool_args": {"from_currency": "USD", "to_currency": "TWD", "amount": 100}}',
            )
        )

        classify = create_classifier_node(mock_llm)
        state: FlowState = {"user_input": "100美金換台幣"}

        result = await classify(state)

        assert result["intent"] == "exchange"
        assert result["tool_name"] == "get_exchange_rate"

    @pytest.mark.asyncio
    async def test_classify_stock_intent(self) -> None:
        """應能分類股票意圖。"""
        from voice_assistant.llm.schemas import ChatMessage

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(
            return_value=ChatMessage(
                role="assistant",
                content='{"intent": "stock", "tool_name": "get_stock_price", "tool_args": {"symbol": "2330.TW"}}',
            )
        )

        classify = create_classifier_node(mock_llm)
        state: FlowState = {"user_input": "台積電股價"}

        result = await classify(state)

        assert result["intent"] == "stock"
        assert result["tool_name"] == "get_stock_price"


class TestFallbackClassify:
    """降級分類測試。"""

    def test_fallback_travel_keywords(self) -> None:
        """應能識別旅遊關鍵詞。"""
        result = _fallback_classify("我想去台北玩")
        assert result["intent"] == "travel"

        result = _fallback_classify("想去高雄旅遊")
        assert result["intent"] == "travel"

    def test_fallback_weather_keywords(self) -> None:
        """應能識別天氣關鍵詞。"""
        result = _fallback_classify("台北天氣如何")
        assert result["intent"] == "weather"
        assert result["tool_args"]["city"] == "台北"

        result = _fallback_classify("高雄會下雨嗎")
        assert result["intent"] == "weather"
        assert result["tool_args"]["city"] == "高雄"

    def test_fallback_exchange_keywords(self) -> None:
        """應能識別匯率關鍵詞。"""
        result = _fallback_classify("美金匯率多少")
        assert result["intent"] == "exchange"

        result = _fallback_classify("換台幣")
        assert result["intent"] == "exchange"

    def test_fallback_stock_keywords(self) -> None:
        """應能識別股票關鍵詞。"""
        result = _fallback_classify("台積電股價")
        assert result["intent"] == "stock"

        result = _fallback_classify("股票查詢")
        assert result["intent"] == "stock"

    def test_fallback_default_to_weather(self) -> None:
        """無法識別時應預設為天氣查詢。"""
        result = _fallback_classify("你好")
        assert result["intent"] == "weather"
