"""Unit tests for WeatherTool."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

# Import mock data
from tests.fixtures.mock_weather import (
    MOCK_WEATHER_BASIC,
    MOCK_WEATHER_DETAILED,
    MOCK_WEATHER_SUNNY,
)
from voice_assistant.tools.weather import (
    CITY_ALIASES,
    TAIWAN_CITIES,
    WEATHER_CODES,
    WeatherTool,
)


class TestWeatherToolProperties:
    """測試 WeatherTool 基本屬性。"""

    @pytest.fixture
    def weather_tool(self) -> WeatherTool:
        return WeatherTool()

    def test_implements_base_tool(self, weather_tool: WeatherTool) -> None:
        """驗證實作 BaseTool。"""
        assert hasattr(weather_tool, "name")
        assert hasattr(weather_tool, "description")
        assert hasattr(weather_tool, "parameters")
        assert hasattr(weather_tool, "execute")

    def test_name(self, weather_tool: WeatherTool) -> None:
        """驗證工具名稱。"""
        assert weather_tool.name == "get_weather"

    def test_description_contains_cities(self, weather_tool: WeatherTool) -> None:
        """驗證描述包含支援的城市。"""
        desc = weather_tool.description
        assert "台北" in desc
        assert "高雄" in desc
        assert "台中" in desc

    def test_parameters_schema(self, weather_tool: WeatherTool) -> None:
        """驗證參數 schema。"""
        params = weather_tool.parameters
        assert params["type"] == "object"
        assert "city" in params["properties"]
        assert "include_details" in params["properties"]
        assert "city" in params["required"]

    def test_to_openai_tool_format(self, weather_tool: WeatherTool) -> None:
        """驗證 OpenAI tools 格式輸出。"""
        tool_def = weather_tool.to_openai_tool()
        assert tool_def["type"] == "function"
        assert tool_def["function"]["name"] == "get_weather"
        assert "parameters" in tool_def["function"]


class TestStaticData:
    """測試靜態資料結構。"""

    def test_taiwan_cities_count(self) -> None:
        """驗證城市數量。"""
        assert len(TAIWAN_CITIES) == 13

    def test_taiwan_cities_coordinates(self) -> None:
        """驗證城市座標格式。"""
        for city, coords in TAIWAN_CITIES.items():
            lat, lon = coords
            assert 21.0 <= lat <= 26.0, f"{city} latitude out of range"
            assert 119.0 <= lon <= 123.0, f"{city} longitude out of range"

    def test_weather_codes_coverage(self) -> None:
        """驗證天氣代碼覆蓋常見情況。"""
        assert 0 in WEATHER_CODES  # 晴朗
        assert 3 in WEATHER_CODES  # 陰天
        assert 61 in WEATHER_CODES  # 小雨
        assert 95 in WEATHER_CODES  # 雷雨

    def test_city_aliases_mapping(self) -> None:
        """驗證城市別名對照。"""
        assert CITY_ALIASES["台北市"] == "台北"
        assert CITY_ALIASES["高雄市"] == "高雄"


class TestResolveCityMethod:
    """測試城市解析邏輯。"""

    @pytest.fixture
    def weather_tool(self) -> WeatherTool:
        return WeatherTool()

    def test_resolve_standard_city(self, weather_tool: WeatherTool) -> None:
        """測試標準城市名稱解析。"""
        result = weather_tool._resolve_city("台北")
        assert result is not None
        city_name, coords = result
        assert city_name == "台北"
        assert coords == (25.0330, 121.5654)

    def test_resolve_city_alias(self, weather_tool: WeatherTool) -> None:
        """測試城市別名解析。"""
        result = weather_tool._resolve_city("台北市")
        assert result is not None
        city_name, _ = result
        assert city_name == "台北"

    def test_resolve_unsupported_city(self, weather_tool: WeatherTool) -> None:
        """測試不支援的城市。"""
        result = weather_tool._resolve_city("東京")
        assert result is None

    def test_resolve_unrecognized_input(self, weather_tool: WeatherTool) -> None:
        """測試無法辨識的輸入。"""
        result = weather_tool._resolve_city("ABCD")
        assert result is None


class TestGetWeatherDescription:
    """測試天氣描述轉換。"""

    @pytest.fixture
    def weather_tool(self) -> WeatherTool:
        return WeatherTool()

    def test_known_code(self, weather_tool: WeatherTool) -> None:
        """測試已知代碼轉換。"""
        assert weather_tool._get_weather_description(0) == "晴朗"
        assert weather_tool._get_weather_description(3) == "陰天"
        assert weather_tool._get_weather_description(61) == "小雨"

    def test_unknown_code(self, weather_tool: WeatherTool) -> None:
        """測試未知代碼處理。"""
        assert weather_tool._get_weather_description(999) == "未知天氣"


class TestExecuteBasicQuery:
    """測試基本天氣查詢（User Story 1）。"""

    @pytest.fixture
    def weather_tool(self) -> WeatherTool:
        return WeatherTool()

    @pytest.mark.asyncio
    async def test_execute_success_basic(self, weather_tool: WeatherTool) -> None:
        """測試成功的基本查詢。"""
        with patch.object(
            weather_tool, "_fetch_weather", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_WEATHER_BASIC

            result = await weather_tool.execute(city="台北")

            assert result.success is True
            assert result.data is not None
            assert result.data["city"] == "台北"
            assert result.data["temperature"] == 22.5
            assert result.data["weather"] == "陰天"
            assert "queried_at" in result.data

    @pytest.mark.asyncio
    async def test_execute_success_with_alias(self, weather_tool: WeatherTool) -> None:
        """測試使用城市別名查詢。"""
        with patch.object(
            weather_tool, "_fetch_weather", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_WEATHER_BASIC

            result = await weather_tool.execute(city="台北市")

            assert result.success is True
            assert result.data is not None
            assert result.data["city"] == "台北"

    @pytest.mark.asyncio
    async def test_execute_sunny_weather(self, weather_tool: WeatherTool) -> None:
        """測試晴天查詢。"""
        with patch.object(
            weather_tool, "_fetch_weather", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_WEATHER_SUNNY

            result = await weather_tool.execute(city="高雄")

            assert result.success is True
            assert result.data is not None
            assert result.data["weather"] == "晴朗"


class TestExecuteUnsupportedCity:
    """測試不支援城市錯誤處理（User Story 2）。"""

    @pytest.fixture
    def weather_tool(self) -> WeatherTool:
        return WeatherTool()

    @pytest.mark.asyncio
    async def test_execute_unsupported_city(self, weather_tool: WeatherTool) -> None:
        """測試查詢不支援的城市。"""
        result = await weather_tool.execute(city="東京")

        assert result.success is False
        assert result.error is not None
        assert "unsupported_city" in result.error

    @pytest.mark.asyncio
    async def test_execute_unrecognized_city(self, weather_tool: WeatherTool) -> None:
        """測試查詢無法辨識的城市。"""
        result = await weather_tool.execute(city="ABCD123")

        assert result.success is False
        assert result.error is not None
        assert "unsupported_city" in result.error


class TestExecuteWithDetails:
    """測試詳細資訊查詢（User Story 3）。"""

    @pytest.fixture
    def weather_tool(self) -> WeatherTool:
        return WeatherTool()

    @pytest.mark.asyncio
    async def test_execute_with_details(self, weather_tool: WeatherTool) -> None:
        """測試包含詳細資訊的查詢。"""
        with patch.object(
            weather_tool, "_fetch_weather", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = MOCK_WEATHER_DETAILED

            result = await weather_tool.execute(city="台北", include_details=True)

            assert result.success is True
            assert result.data is not None
            assert result.data["humidity"] == 75
            assert result.data["apparent_temperature"] == 24.1
            assert result.data["wind_speed"] == 12.3


class TestErrorHandling:
    """測試錯誤處理（Phase 6）。"""

    @pytest.fixture
    def weather_tool(self) -> WeatherTool:
        return WeatherTool()

    @pytest.mark.asyncio
    async def test_api_timeout(self, weather_tool: WeatherTool) -> None:
        """測試 API 逾時處理。"""
        with patch.object(
            weather_tool, "_fetch_weather", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = httpx.TimeoutException("Timeout")

            result = await weather_tool.execute(city="台北")

            assert result.success is False
            assert result.error is not None
            assert "api_timeout" in result.error

    @pytest.mark.asyncio
    async def test_network_error(self, weather_tool: WeatherTool) -> None:
        """測試網路錯誤處理。"""
        with patch.object(
            weather_tool, "_fetch_weather", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = httpx.RequestError("Network error")

            result = await weather_tool.execute(city="台北")

            assert result.success is False
            assert result.error is not None
            assert "network_error" in result.error

    @pytest.mark.asyncio
    async def test_api_error(self, weather_tool: WeatherTool) -> None:
        """測試 API 回應錯誤處理。"""
        with patch.object(
            weather_tool, "_fetch_weather", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = ValueError("API returned status 500")

            result = await weather_tool.execute(city="台北")

            assert result.success is False
            assert result.error is not None
            assert "api_error" in result.error
