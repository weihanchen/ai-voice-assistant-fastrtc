"""美食推薦 venue_decision 節點。

根據天氣決定室內或戶外餐廳。
"""

from __future__ import annotations

import logging
from typing import Any

from voice_assistant.flows.state import FlowState

logger = logging.getLogger(__name__)


async def decide_venue_type(state: FlowState) -> dict[str, Any]:
    """根據天氣決定推薦室內或戶外餐廳。

    決策邏輯：
    - 溫度 15-28°C 且非雨天 → 戶外
    - 其他情況 → 室內
    """
    food_state = state.get("food_state") or {}
    weather_info = food_state.get("weather_info")

    if not weather_info:
        return {"error": "缺少天氣資訊"}

    temperature = weather_info.temperature
    weather = weather_info.weather.lower()

    # 判斷是否適合戶外用餐
    is_comfortable_temp = 15 <= temperature <= 28
    is_not_rainy = "rain" not in weather and "雨" not in weather

    if is_comfortable_temp and is_not_rainy:
        venue_type = "outdoor"
        is_outdoor_friendly = True
    else:
        venue_type = "indoor"
        is_outdoor_friendly = False

    # 更新 weather_info 的 is_outdoor_friendly 欄位
    updated_weather_info = weather_info.model_copy(
        update={"is_outdoor_friendly": is_outdoor_friendly}
    )

    return {
        "food_state": {
            **food_state,
            "venue_type": venue_type,
            "weather_info": updated_weather_info,
        },
    }
