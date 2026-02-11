"""美食推薦 query_weather 節點。

調用 WeatherTool 工具執行天氣查詢。
"""

from __future__ import annotations

import logging
from typing import Any

from voice_assistant.flows.state import FlowState, FoodRecommendInfo
from voice_assistant.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def create_query_weather_node(tool_registry: ToolRegistry) -> Any:
    """建立 query_weather 節點。

    Args:
        tool_registry: 工具註冊表實例。

    Returns:
        LangGraph 節點函式。
    """

    async def query_weather(state: FlowState) -> dict[str, Any]:
        """調用 WeatherTool 工具查詢天氣。"""
        food_state = state.get("food_state") or {}
        city = food_state.get("city")

        if not city:
            return {"error": "缺少必要參數: city"}

        try:
            result = await tool_registry.execute(
                "get_weather",
                {"city": city},
            )

            if not result.success:
                return {"error": f"天氣查詢失敗：{result.error}"}

            weather_data = result.data or {}
            # 防禦性地存取天氣資料
            temperature = weather_data.get("temperature")
            weather = weather_data.get("weather")
            if temperature is None or weather is None:
                logger.warning(
                    "天氣回應缺少必要欄位: temperature=%s, weather=%s",
                    temperature,
                    weather,
                )
                return {"error": "天氣資料不完整，請稍後再試"}

            weather_info = FoodRecommendInfo(
                city=city,
                temperature=temperature,
                weather=weather,
                is_outdoor_friendly=False,  # 將由下一個節點決定
            )

            return {
                "food_state": {
                    **food_state,
                    "weather_info": weather_info,
                },
            }
        except Exception:
            logger.exception("WeatherTool 工具呼叫失敗")
            return {"error": "天氣查詢失敗，請稍後再試"}

    return query_weather
