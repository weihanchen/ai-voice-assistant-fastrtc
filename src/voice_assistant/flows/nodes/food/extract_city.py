"""美食推薦 extract_city 節點。

從使用者輸入中提取城市名稱。
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

from voice_assistant.flows.state import FlowState

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient

logger = logging.getLogger(__name__)


class ExtractCityResponse(BaseModel):
    """LLM 城市提取回應 schema。"""

    city: str | None = None


EXTRACT_CITY_SYSTEM_PROMPT = """你是一個城市名稱提取助手。

使用者會提供一段關於美食推薦的查詢，你需要從中提取出城市名稱。

回應格式（JSON）：
{
  "city": "城市名稱"
}

如果無法提取城市名稱，回應：
{
  "city": null
}

範例：
- 輸入："台北有什麼好吃的？" → {"city": "台北"}
- 輸入："我在高雄，推薦餐廳" → {"city": "高雄"}
- 輸入："推薦美食" → {"city": null}
"""


def create_extract_city_node(llm_client: LLMClient) -> Any:
    """建立 extract_city 節點。

    Args:
        llm_client: LLM 客戶端實例。

    Returns:
        LangGraph 節點函式。
    """

    async def extract_city(state: FlowState) -> dict[str, Any]:
        """從使用者輸入中提取城市名稱。"""
        from voice_assistant.llm.schemas import ChatMessage

        user_input = state.get("user_input", "")

        try:
            response = await llm_client.chat(
                messages=[ChatMessage(role="user", content=user_input)],
                system_prompt=EXTRACT_CITY_SYSTEM_PROMPT,
            )

            content = response.content or ""
            # 移除可能的 markdown 程式碼區塊標記
            content = (
                content.strip().removeprefix("```json").removesuffix("```").strip()
            )
            result = json.loads(content)

            # 使用 Pydantic 驗證回應格式
            city_response = ExtractCityResponse(**result)

            if not city_response.city:
                return {"error": "無法從您的輸入中識別城市，請明確指定城市名稱。"}

            return {
                "food_state": {
                    "city": city_response.city,
                },
            }
        except json.JSONDecodeError as e:
            logger.warning("extract_city JSON 解析失敗: %s", e)
            return {"error": "城市提取處理失敗"}
        except ValidationError as e:
            logger.warning("extract_city Pydantic 驗證失敗: %s", e)
            return {"error": "城市提取處理失敗"}
        except Exception:
            logger.exception("extract_city 執行失敗")
            return {"error": "城市提取執行時發生錯誤"}

    return extract_city
