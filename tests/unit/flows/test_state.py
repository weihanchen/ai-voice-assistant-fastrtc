"""狀態模型單元測試。"""

import pytest

from voice_assistant.flows.state import (
    CITY_RECOMMENDATIONS,
    FlowState,
    IntentType,
    RecommendationType,
    TravelPlanState,
    WeatherInfo,
    is_weather_suitable,
)


class TestWeatherInfo:
    """WeatherInfo 模型測試。"""

    def test_create_weather_info_basic(self) -> None:
        """測試建立基本天氣資訊。"""
        info = WeatherInfo(
            city="台北",
            temperature=25.0,
            weather="晴朗",
            weather_code=0,
        )
        assert info.city == "台北"
        assert info.temperature == 25.0
        assert info.weather == "晴朗"
        assert info.weather_code == 0
        assert info.humidity is None
        assert info.wind_speed is None

    def test_create_weather_info_full(self) -> None:
        """測試建立完整天氣資訊。"""
        info = WeatherInfo(
            city="高雄",
            temperature=30.5,
            weather="多雲",
            weather_code=2,
            humidity=75.0,
            wind_speed=10.5,
        )
        assert info.city == "高雄"
        assert info.humidity == 75.0
        assert info.wind_speed == 10.5


class TestIsWeatherSuitable:
    """is_weather_suitable 函式測試。"""

    def test_sunny_comfortable_temp_is_suitable(self) -> None:
        """晴朗且舒適溫度應適合出遊。"""
        info = WeatherInfo(
            city="台北", temperature=25.0, weather="晴朗", weather_code=0
        )
        assert is_weather_suitable(info) is True

    def test_cloudy_comfortable_temp_is_suitable(self) -> None:
        """多雲且舒適溫度應適合出遊。"""
        info = WeatherInfo(
            city="台北", temperature=22.0, weather="多雲", weather_code=2
        )
        assert is_weather_suitable(info) is True

    def test_rainy_is_not_suitable(self) -> None:
        """下雨不適合出遊。"""
        # 小雨 (code 51)
        info = WeatherInfo(
            city="台北", temperature=25.0, weather="小雨", weather_code=51
        )
        assert is_weather_suitable(info) is False

        # 中雨 (code 63)
        info = WeatherInfo(
            city="台北", temperature=25.0, weather="中雨", weather_code=63
        )
        assert is_weather_suitable(info) is False

        # 陣雨 (code 80)
        info = WeatherInfo(
            city="台北", temperature=25.0, weather="陣雨", weather_code=80
        )
        assert is_weather_suitable(info) is False

        # 雷雨 (code 95)
        info = WeatherInfo(
            city="台北", temperature=25.0, weather="雷雨", weather_code=95
        )
        assert is_weather_suitable(info) is False

    def test_too_cold_is_not_suitable(self) -> None:
        """溫度過低不適合出遊。"""
        info = WeatherInfo(
            city="台北", temperature=10.0, weather="晴朗", weather_code=0
        )
        assert is_weather_suitable(info) is False

    def test_too_hot_is_not_suitable(self) -> None:
        """溫度過高不適合出遊。"""
        info = WeatherInfo(
            city="台北", temperature=38.0, weather="晴朗", weather_code=0
        )
        assert is_weather_suitable(info) is False

    def test_boundary_temp_15_is_suitable(self) -> None:
        """溫度剛好 15°C 應適合出遊。"""
        info = WeatherInfo(
            city="台北", temperature=15.0, weather="晴朗", weather_code=0
        )
        assert is_weather_suitable(info) is True

    def test_boundary_temp_35_is_suitable(self) -> None:
        """溫度剛好 35°C 應適合出遊。"""
        info = WeatherInfo(
            city="台北", temperature=35.0, weather="晴朗", weather_code=0
        )
        assert is_weather_suitable(info) is True

    def test_boundary_temp_14_9_is_not_suitable(self) -> None:
        """溫度 14.9°C 不適合出遊。"""
        info = WeatherInfo(
            city="台北", temperature=14.9, weather="晴朗", weather_code=0
        )
        assert is_weather_suitable(info) is False

    def test_boundary_temp_35_1_is_not_suitable(self) -> None:
        """溫度 35.1°C 不適合出遊。"""
        info = WeatherInfo(
            city="台北", temperature=35.1, weather="晴朗", weather_code=0
        )
        assert is_weather_suitable(info) is False


class TestCityRecommendations:
    """城市景點推薦測試。"""

    def test_all_taiwan_cities_have_recommendations(self) -> None:
        """所有台灣主要城市都應有推薦景點。"""
        expected_cities = [
            "台北",
            "新北",
            "桃園",
            "台中",
            "台南",
            "高雄",
            "基隆",
            "新竹",
            "嘉義",
            "屏東",
            "宜蘭",
            "花蓮",
            "台東",
        ]
        for city in expected_cities:
            assert city in CITY_RECOMMENDATIONS, f"{city} 應在推薦清單中"

    def test_each_city_has_outdoor_and_indoor(self) -> None:
        """每個城市都應有戶外和室內推薦。"""
        for city, recs in CITY_RECOMMENDATIONS.items():
            assert "outdoor" in recs, f"{city} 應有 outdoor 推薦"
            assert "indoor" in recs, f"{city} 應有 indoor 推薦"
            assert len(recs["outdoor"]) >= 3, f"{city} outdoor 推薦應至少 3 項"
            assert len(recs["indoor"]) >= 3, f"{city} indoor 推薦應至少 3 項"


class TestFlowState:
    """FlowState 類型測試。"""

    def test_create_minimal_flow_state(self) -> None:
        """測試建立最小流程狀態。"""
        state: FlowState = {"user_input": "我想去台北玩"}
        assert state["user_input"] == "我想去台北玩"

    def test_create_full_flow_state(self) -> None:
        """測試建立完整流程狀態。"""
        state: FlowState = {
            "user_input": "台北天氣如何",
            "intent": "weather",
            "tool_name": "get_weather",
            "tool_args": {"city": "台北"},
            "tool_result": {"temperature": 25.0},
            "travel_state": None,
            "response": "台北目前氣溫 25 度",
            "error": None,
        }
        assert state["intent"] == "weather"
        assert state["tool_name"] == "get_weather"


class TestTravelPlanState:
    """TravelPlanState 類型測試。"""

    def test_create_travel_plan_state(self) -> None:
        """測試建立旅遊規劃狀態。"""
        state: TravelPlanState = {
            "destination": "台北",
            "destination_valid": True,
            "weather_data": WeatherInfo(
                city="台北", temperature=25.0, weather="晴朗", weather_code=0
            ),
            "weather_suitable": True,
            "recommendation_type": "outdoor",
            "recommendations": ["象山步道", "陽明山國家公園"],
        }
        assert state["destination"] == "台北"
        assert state["weather_suitable"] is True
        assert len(state["recommendations"]) == 2


class TestIntentType:
    """IntentType 類型測試。"""

    def test_valid_intent_types(self) -> None:
        """測試有效的意圖類型。"""
        valid_intents: list[IntentType] = ["weather", "exchange", "stock", "travel"]
        for intent in valid_intents:
            # 型別檢查通過即表示有效
            assert intent in ["weather", "exchange", "stock", "travel"]


class TestRecommendationType:
    """RecommendationType 類型測試。"""

    def test_valid_recommendation_types(self) -> None:
        """測試有效的建議類型。"""
        valid_types: list[RecommendationType] = [
            "outdoor",
            "indoor",
            "alternative_date",
        ]
        for rec_type in valid_types:
            assert rec_type in ["outdoor", "indoor", "alternative_date"]
