"""Weather query tool for voice assistant."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult

# T003: 台灣城市經緯度對照表
TAIWAN_CITIES: dict[str, tuple[float, float]] = {
    "台北": (25.0330, 121.5654),
    "新北": (25.0120, 121.4657),
    "桃園": (24.9936, 121.3010),
    "台中": (24.1477, 120.6736),
    "台南": (22.9908, 120.2133),
    "高雄": (22.6273, 120.3014),
    "基隆": (25.1276, 121.7392),
    "新竹": (24.8015, 120.9718),
    "嘉義": (23.4801, 120.4491),
    "屏東": (22.6690, 120.4866),
    "宜蘭": (24.7570, 121.7533),
    "花蓮": (23.9910, 121.6114),
    "台東": (22.7583, 121.1444),
}

# T004: WMO 天氣代碼中文對照表
WEATHER_CODES: dict[int, str] = {
    0: "晴朗",
    1: "晴時多雲",
    2: "多雲",
    3: "陰天",
    45: "霧",
    48: "濃霧",
    51: "小雨",
    53: "毛毛雨",
    55: "細雨",
    56: "凍雨",
    57: "凍雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "凍雨",
    67: "凍雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "陣雨",
    81: "陣雨",
    82: "雷陣雨",
    85: "小雪",
    86: "大雪",
    95: "雷雨",
    96: "雷雨伴隨冰雹",
    99: "大雷雨伴隨冰雹",
}

# T005: 城市別名對照表
CITY_ALIASES: dict[str, str] = {
    "台北市": "台北",
    "新北市": "新北",
    "桃園市": "桃園",
    "台中市": "台中",
    "台南市": "台南",
    "高雄市": "高雄",
    "基隆市": "基隆",
    "新竹市": "新竹",
    "新竹縣": "新竹",
    "嘉義市": "嘉義",
    "嘉義縣": "嘉義",
    "屏東縣": "屏東",
    "宜蘭縣": "宜蘭",
    "花蓮縣": "花蓮",
    "台東縣": "台東",
}

# Open-Meteo API 設定
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
API_TIMEOUT = 5.0  # 秒


class WeatherTool(BaseTool):
    """天氣查詢工具 - 查詢台灣主要城市的即時天氣資訊。"""

    @property
    def name(self) -> str:
        """工具名稱。"""
        return "get_weather"

    @property
    def description(self) -> str:
        """工具描述（供 LLM 判斷何時調用）。"""
        return (
            "查詢台灣城市的即時天氣資訊。"
            "可查詢溫度、天氣狀況、濕度、風速等。"
            "支援的城市：台北、新北、桃園、台中、台南、高雄、"
            "基隆、新竹、嘉義、屏東、宜蘭、花蓮、台東。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON Schema 參數定義。"""
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "要查詢的城市名稱，例如：台北、高雄、台中",
                },
                "include_details": {
                    "type": "boolean",
                    "description": "是否包含詳細資訊（濕度、風速、體感溫度）",
                    "default": False,
                },
            },
            "required": ["city"],
        }

    def _resolve_city(self, city: str) -> tuple[str, tuple[float, float]] | None:
        """
        解析城市名稱，回傳標準城市名與座標。

        Args:
            city: 使用者輸入的城市名稱

        Returns:
            (標準城市名, (緯度, 經度)) 或 None（不支援的城市）
        """
        # 先查詢別名
        normalized = CITY_ALIASES.get(city, city)

        # 查詢座標
        coords = TAIWAN_CITIES.get(normalized)
        if coords:
            return (normalized, coords)

        return None

    def _get_weather_description(self, code: int) -> str:
        """
        將 WMO 天氣代碼轉換為中文描述。

        Args:
            code: WMO 天氣代碼

        Returns:
            中文天氣描述
        """
        return WEATHER_CODES.get(code, "未知天氣")

    async def _fetch_weather(
        self, latitude: float, longitude: float, include_details: bool = False
    ) -> dict[str, Any]:
        """
        從 Open-Meteo API 取得天氣資料。

        Args:
            latitude: 緯度
            longitude: 經度
            include_details: 是否包含詳細資訊

        Returns:
            天氣資料字典

        Raises:
            httpx.TimeoutException: API 逾時
            httpx.RequestError: 網路錯誤
            ValueError: API 回應錯誤
        """
        # 基本參數
        current_params = ["temperature_2m", "weather_code"]

        # 詳細資訊參數
        if include_details:
            current_params.extend(
                ["relative_humidity_2m", "apparent_temperature", "wind_speed_10m"]
            )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(current_params),
        }

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(OPEN_METEO_BASE_URL, params=params)

            if response.status_code >= 400:
                raise ValueError(f"API returned status {response.status_code}")

            return response.json()

    async def execute(
        self, city: str, include_details: bool = False, **kwargs: Any
    ) -> ToolResult:
        """
        執行天氣查詢。

        Args:
            city: 城市名稱
            include_details: 是否包含詳細資訊

        Returns:
            ToolResult: 成功時包含天氣資料，失敗時包含錯誤訊息
        """
        # 解析城市
        resolved = self._resolve_city(city)
        if not resolved:
            return ToolResult.fail(
                "unsupported_city: 目前僅支援台灣主要城市的天氣查詢，"
                "例如台北、高雄、台中、台南、新北、桃園、基隆、新竹、嘉義、屏東、宜蘭、花蓮、台東"
            )

        city_name, (lat, lon) = resolved

        try:
            # 呼叫 API
            data = await self._fetch_weather(lat, lon, include_details)
            current = data.get("current", {})

            # 基本資訊
            temperature = current.get("temperature_2m")
            weather_code = current.get("weather_code", 0)
            weather_desc = self._get_weather_description(weather_code)

            result: dict[str, Any] = {
                "city": city_name,
                "temperature": temperature,
                "weather": weather_desc,
                "queried_at": datetime.now(UTC).isoformat(),
            }

            # 詳細資訊
            if include_details:
                result["humidity"] = current.get("relative_humidity_2m")
                result["apparent_temperature"] = current.get("apparent_temperature")
                result["wind_speed"] = current.get("wind_speed_10m")

            return ToolResult.ok(result)

        except httpx.TimeoutException:
            return ToolResult.fail("api_timeout: 天氣服務暫時無法使用，請稍後再試")
        except httpx.RequestError:
            return ToolResult.fail("network_error: 網路連線異常，請檢查網路狀態")
        except ValueError as e:
            return ToolResult.fail(f"api_error: 無法取得天氣資訊 ({e})")
