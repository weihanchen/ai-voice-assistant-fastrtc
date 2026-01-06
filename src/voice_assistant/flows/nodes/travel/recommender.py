"""建議產生節點。

根據天氣狀況產生旅遊建議。
"""

from __future__ import annotations

from typing import Any

from voice_assistant.flows.state import (
    CITY_RECOMMENDATIONS,
    FlowState,
    RecommendationType,
    TravelPlanState,
)


async def recommend_outdoor(state: FlowState) -> dict[str, Any]:
    """產生戶外活動建議。

    Args:
        state: 流程狀態

    Returns:
        更新的狀態欄位
    """
    return _generate_recommendations(state, "outdoor")


async def recommend_indoor(state: FlowState) -> dict[str, Any]:
    """產生室內活動建議。

    Args:
        state: 流程狀態

    Returns:
        更新的狀態欄位
    """
    return _generate_recommendations(state, "indoor")


def _generate_recommendations(
    state: FlowState, rec_type: RecommendationType
) -> dict[str, Any]:
    """產生建議的通用函式。

    Args:
        state: 流程狀態
        rec_type: 建議類型（outdoor 或 indoor）

    Returns:
        更新的狀態欄位
    """
    travel_state = state.get("travel_state", {})
    destination = travel_state.get("destination")

    if not destination:
        return {
            "error": "無法產生建議：缺少目的地資訊",
        }

    # 從靜態資料取得建議
    city_recs = CITY_RECOMMENDATIONS.get(destination, {})
    recommendations = city_recs.get(rec_type, [])

    # 最多取 3 個建議
    recommendations = recommendations[:3]

    # 如果沒有建議，使用預設訊息
    if not recommendations:
        if rec_type == "outdoor":
            recommendations = ["戶外景點探索", "當地特色小吃", "市區散步"]
        else:
            recommendations = ["百貨公司逛街", "特色咖啡廳", "當地博物館"]

    # 更新 travel_state，保留既有欄位
    updated_travel_state: TravelPlanState = {
        **travel_state,
        "recommendation_type": rec_type,
        "recommendations": recommendations,
    }

    return {"travel_state": updated_travel_state}
