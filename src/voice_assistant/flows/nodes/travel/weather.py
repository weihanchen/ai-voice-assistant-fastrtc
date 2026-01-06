"""天氣查詢節點。

查詢目的地的天氣資訊。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from voice_assistant.flows.state import FlowState, TravelPlanState, WeatherInfo

if TYPE_CHECKING:
    from voice_assistant.tools.registry import ToolRegistry


def create_weather_query_node(tool_registry: ToolRegistry) -> Any:
    """建立天氣查詢節點。

    Args:
        tool_registry: Tool 註冊表

    Returns:
        可用於 LangGraph 的節點函式
    """

    async def query_weather(state: FlowState) -> dict[str, Any]:
        """查詢天氣節點函式。

        Args:
            state: 流程狀態

        Returns:
            更新的狀態欄位
        """
        travel_state = state.get("travel_state", {})
        destination = travel_state.get("destination")

        if not destination:
            return {
                "error": "無法查詢天氣：未指定目的地",
            }

        try:
            # 呼叫現有 WeatherTool
            result = await tool_registry.execute(
                "get_weather",
                {"city": destination, "include_details": True},
            )

            if not result.success:
                return {
                    "error": result.error or "天氣查詢失敗",
                }

            # 轉換為 WeatherInfo
            data = result.data or {}
            weather_info = WeatherInfo(
                city=data.get("city", destination),
                temperature=data.get("temperature", 0.0),
                weather=data.get("weather", "未知"),
                weather_code=data.get("weather_code", 0),
                humidity=data.get("humidity"),
                wind_speed=data.get("wind_speed"),
            )

            # 更新 travel_state，保留既有欄位
            updated_travel_state: TravelPlanState = {
                **travel_state,
                "weather_data": weather_info,
            }

            return {"travel_state": updated_travel_state}

        except Exception as e:
            return {
                "error": f"查詢天氣時發生錯誤: {e!s}",
            }

    return query_weather
