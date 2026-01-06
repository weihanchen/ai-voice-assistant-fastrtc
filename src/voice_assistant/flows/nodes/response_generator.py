"""回應產生節點。

將處理結果轉換為口語化繁體中文回應。
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from voice_assistant.flows.state import FlowState

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient


RESPONSE_SYSTEM_PROMPT = """\
你是一個友善的語音助手。請將以下資料轉換為口語化的繁體中文回應。

回應要求：
1. 使用自然、口語化的繁體中文
2. 簡潔扼要，適合語音輸出
3. 不要使用專業術語或技術名詞
4. 回應長度控制在 200 字以內
5. 數字要用容易聽懂的方式表達（如：二十五度、一百美金）

如果有錯誤訊息，請以友善的方式告知使用者。
"""


def create_response_generator_node(llm_client: LLMClient) -> Any:
    """建立回應產生節點。

    Args:
        llm_client: LLM 客戶端

    Returns:
        可用於 LangGraph 的節點函式
    """
    from voice_assistant.llm.schemas import ChatMessage

    async def generate_response(state: FlowState) -> dict[str, Any]:
        """產生回應節點函式。

        Args:
            state: 流程狀態

        Returns:
            更新的狀態欄位
        """
        user_input = state.get("user_input", "")
        intent = state.get("intent")
        tool_result = state.get("tool_result")
        travel_state = state.get("travel_state")
        error = state.get("error")

        # 組合要回應的資料
        context_parts = [f"使用者問題：{user_input}"]

        if error:
            context_parts.append(f"錯誤訊息：{error}")
        elif intent == "travel" and travel_state:
            # 旅遊規劃回應
            destination = travel_state.get("destination", "")
            weather_data = travel_state.get("weather_data")
            weather_suitable = travel_state.get("weather_suitable")
            recommendations = travel_state.get("recommendations", [])
            rec_type = travel_state.get("recommendation_type", "outdoor")

            context_parts.append(f"目的地：{destination}")

            if weather_data:
                # 處理 WeatherInfo 物件
                if hasattr(weather_data, "temperature"):
                    temp = weather_data.temperature
                    weather = weather_data.weather
                else:
                    temp = weather_data.get("temperature", 0)
                    weather = weather_data.get("weather", "未知")
                context_parts.append(f"天氣：{weather}，氣溫 {temp} 度")

            if weather_suitable is not None:
                status = "適合出遊" if weather_suitable else "不太適合出遊"
                context_parts.append(f"出遊建議：{status}")

            if recommendations:
                rec_type_name = "戶外活動" if rec_type == "outdoor" else "室內活動"
                rec_list = ", ".join(recommendations)
                context_parts.append(f"推薦{rec_type_name}：{rec_list}")
        elif tool_result:
            # Tool 結果回應
            result_json = json.dumps(tool_result, ensure_ascii=False)
            context_parts.append(f"查詢結果：{result_json}")

        context = "\n".join(context_parts)

        try:
            response = await llm_client.chat(
                messages=[ChatMessage(role="user", content=context)],
                system_prompt=RESPONSE_SYSTEM_PROMPT,
            )

            return {
                "response": response.content or "抱歉，我無法產生回應",
            }

        except Exception:
            # 降級回應
            return {
                "response": _generate_fallback_response(state),
            }

    return generate_response


def _generate_fallback_response(state: FlowState) -> str:
    """產生降級回應。

    Args:
        state: 流程狀態

    Returns:
        回應文字
    """
    error = state.get("error")
    if error:
        return f"抱歉，{error}"

    intent = state.get("intent")
    tool_result = state.get("tool_result")
    travel_state = state.get("travel_state")

    if intent == "travel" and travel_state:
        destination = travel_state.get("destination", "")
        recommendations = travel_state.get("recommendations", [])
        weather_suitable = travel_state.get("weather_suitable")

        if recommendations:
            rec_text = "、".join(recommendations)
            if weather_suitable:
                return f"{destination}今天天氣不錯，適合出遊！推薦您：{rec_text}"
            else:
                return f"{destination}今天天氣不太適合戶外活動，建議您：{rec_text}"

    if tool_result:
        # 簡單格式化 tool 結果
        if "temperature" in tool_result:
            city = tool_result.get("city", "")
            temp = tool_result.get("temperature", 0)
            weather = tool_result.get("weather", "")
            return f"{city}現在{weather}，氣溫{temp}度"
        elif "rate" in tool_result:
            return f"匯率資訊：{tool_result}"
        elif "price" in tool_result:
            return f"股價資訊：{tool_result}"

    return "抱歉，我無法處理您的請求，請稍後再試"
