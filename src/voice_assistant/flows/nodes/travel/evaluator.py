"""天氣評估節點。

評估天氣是否適合出遊。
"""

from __future__ import annotations

from typing import Any

from voice_assistant.flows.state import (
    FlowState,
    TravelPlanState,
    WeatherInfo,
    is_weather_suitable,
)


async def evaluate_weather(state: FlowState) -> dict[str, Any]:
    """評估天氣節點函式。

    根據天氣資訊判斷是否適合出遊。

    Args:
        state: 流程狀態

    Returns:
        更新的狀態欄位
    """
    travel_state = state.get("travel_state", {})
    weather_data = travel_state.get("weather_data")

    if not weather_data:
        return {
            "error": "無法評估天氣：缺少天氣資訊",
        }

    # 確保 weather_data 是 WeatherInfo 類型
    if isinstance(weather_data, dict):
        weather_info = WeatherInfo(**weather_data)
    else:
        weather_info = weather_data

    # 評估天氣是否適合出遊
    suitable = is_weather_suitable(weather_info)

    # 更新 travel_state，保留既有欄位
    updated_travel_state: TravelPlanState = {
        **travel_state,
        "weather_suitable": suitable,
    }

    return {"travel_state": updated_travel_state}
