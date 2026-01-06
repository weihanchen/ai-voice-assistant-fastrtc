"""流程圖單元測試。"""

from unittest.mock import MagicMock

from voice_assistant.flows.graphs.main_router import route_by_intent
from voice_assistant.flows.graphs.travel_planner import (
    route_by_destination_valid,
    route_by_weather,
)
from voice_assistant.flows.state import FlowState


class TestRouteByIntent:
    """意圖路由測試。"""

    def test_route_weather_to_tool_executor(self) -> None:
        """天氣意圖應路由到工具執行器。"""
        state: FlowState = {
            "user_input": "台北天氣",
            "intent": "weather",
            "tool_name": "get_weather",
        }

        result = route_by_intent(state)

        assert result == "tool_executor"

    def test_route_exchange_to_tool_executor(self) -> None:
        """匯率意圖應路由到工具執行器。"""
        state: FlowState = {
            "user_input": "美金匯率",
            "intent": "exchange",
            "tool_name": "get_exchange_rate",
        }

        result = route_by_intent(state)

        assert result == "tool_executor"

    def test_route_stock_to_tool_executor(self) -> None:
        """股票意圖應路由到工具執行器。"""
        state: FlowState = {
            "user_input": "台積電股價",
            "intent": "stock",
            "tool_name": "get_stock_price",
        }

        result = route_by_intent(state)

        assert result == "tool_executor"

    def test_route_travel_to_subgraph(self) -> None:
        """旅遊意圖應路由到子流程。"""
        state: FlowState = {
            "user_input": "我想去高雄玩",
            "intent": "travel",
        }

        result = route_by_intent(state)

        assert result == "travel_subgraph"

    def test_route_error_to_response_generator(self) -> None:
        """有錯誤時應路由到回應產生器。"""
        state: FlowState = {
            "user_input": "台北天氣",
            "error": "分類失敗",
        }

        result = route_by_intent(state)

        assert result == "response_generator"


class TestRouteByDestinationValid:
    """目的地驗證路由測試。"""

    def test_valid_destination_routes_to_query_weather(self) -> None:
        """有效目的地應路由到天氣查詢。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "destination_valid": True,
            },
        }

        result = route_by_destination_valid(state)

        assert result == "query_weather"

    def test_invalid_destination_routes_to_handler(self) -> None:
        """無效目的地應路由到錯誤處理。"""
        state: FlowState = {
            "user_input": "我想去東京玩",
            "travel_state": {
                "destination": "東京",
                "destination_valid": False,
            },
        }

        result = route_by_destination_valid(state)

        assert result == "handle_invalid_destination"


class TestRouteByWeather:
    """天氣條件路由測試。"""

    def test_suitable_weather_routes_to_outdoor(self) -> None:
        """適合天氣應路由到戶外建議。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "weather_suitable": True,
            },
        }

        result = route_by_weather(state)

        assert result == "recommend_outdoor"

    def test_unsuitable_weather_routes_to_indoor(self) -> None:
        """不適合天氣應路由到室內建議。"""
        state: FlowState = {
            "user_input": "我想去台北玩",
            "travel_state": {
                "destination": "台北",
                "weather_suitable": False,
            },
        }

        result = route_by_weather(state)

        assert result == "recommend_indoor"


class TestTravelPlannerGraph:
    """旅遊規劃流程圖測試。"""

    def test_create_travel_planner_graph(self) -> None:
        """應能建立旅遊規劃流程圖。"""
        from voice_assistant.flows.graphs.travel_planner import (
            create_travel_planner_graph,
        )

        mock_llm = MagicMock()
        mock_registry = MagicMock()

        graph = create_travel_planner_graph(mock_llm, mock_registry)

        # 驗證圖已編譯
        assert graph is not None
        # 驗證有 Mermaid 輸出
        mermaid = graph.get_graph().draw_mermaid()
        assert "parse_destination" in mermaid


class TestMainRouterGraph:
    """主路由流程圖測試。"""

    def test_create_main_router_graph(self) -> None:
        """應能建立主路由流程圖。"""
        from voice_assistant.flows.graphs.main_router import create_main_router_graph

        mock_llm = MagicMock()
        mock_registry = MagicMock()

        graph = create_main_router_graph(mock_llm, mock_registry)

        # 驗證圖已編譯
        assert graph is not None
        # 驗證有 Mermaid 輸出
        mermaid = graph.get_graph().draw_mermaid()
        assert "classifier" in mermaid
        assert "tool_executor" in mermaid
        assert "travel_subgraph" in mermaid
