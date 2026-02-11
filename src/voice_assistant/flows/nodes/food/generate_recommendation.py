"""美食推薦 generate_recommendation 節點。

根據城市、天氣和場地類型生成餐廳推薦。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from voice_assistant.flows.state import FlowState

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient

logger = logging.getLogger(__name__)

GENERATE_RECOMMENDATION_SYSTEM_PROMPT = """你是一個專業的美食推薦助手。

根據使用者的城市、當前天氣和適合的用餐場地類型（室內/戶外），推薦 3-5 家合適的餐廳。

推薦內容應包括：
1. 餐廳名稱
2. 餐廳類型（例如：日式料理、咖啡廳、燒烤店等）
3. 推薦理由（結合天氣狀況說明為何適合）

輸出格式：
直接以自然語言回應，友善且有吸引力。

範例：
根據台北目前 22°C 的舒適天氣，我為您推薦以下戶外餐廳：

1. 陽明山上的草山小鎮 - 景觀餐廳，可以邊用餐邊欣賞台北夜景
2. 淡水老街的漁人碼頭餐廳 - 海鮮料理，戶外座位可眺望淡水河
3. 內湖大湖公園旁的湖畔咖啡 - 輕食咖啡廳，湖邊座位非常愜意
"""


def create_generate_recommendation_node(llm_client: LLMClient) -> Any:
    """建立 generate_recommendation 節點。

    Args:
        llm_client: LLM 客戶端實例。

    Returns:
        LangGraph 節點函式。
    """

    async def generate_recommendation(state: FlowState) -> dict[str, Any]:
        """生成餐廳推薦。"""
        from voice_assistant.llm.schemas import ChatMessage

        food_state = state.get("food_state") or {}
        weather_info = food_state.get("weather_info")
        venue_type = food_state.get("venue_type")

        if not weather_info or not venue_type:
            return {"error": "缺少必要資訊"}

        # 構建使用者提示詞
        venue_type_text = "戶外" if venue_type == "outdoor" else "室內"
        user_prompt = f"""城市：{weather_info.city}
天氣：{weather_info.weather}
溫度：{weather_info.temperature}°C
推薦場地類型：{venue_type_text}

請推薦適合的餐廳。"""

        try:
            response = await llm_client.chat(
                messages=[ChatMessage(role="user", content=user_prompt)],
                system_prompt=GENERATE_RECOMMENDATION_SYSTEM_PROMPT,
            )

            recommendation = response.content or "無法產生推薦"

            return {
                "food_state": {
                    **food_state,
                    "recommendation": recommendation,
                },
                "response": recommendation,
            }
        except Exception:
            logger.exception("generate_recommendation 執行失敗")
            return {"error": "餐廳推薦產生失敗"}

    return generate_recommendation
