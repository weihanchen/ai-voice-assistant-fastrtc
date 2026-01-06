"""意圖分類節點。

使用 LLM 分類使用者意圖並提取 Tool 參數。
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from voice_assistant.flows.state import FlowState, IntentType

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient


CLASSIFIER_SYSTEM_PROMPT = """\
你是一個語音助手的意圖分類器。請分析使用者的輸入並分類意圖。

支援的意圖類型：
1. weather - 天氣查詢（關鍵詞：天氣、氣溫、溫度、會下雨嗎）
2. exchange - 匯率換算（關鍵詞：匯率、換台幣、換美金、多少錢+貨幣）
3. stock - 股票查詢（關鍵詞：股價、股票、多少錢+公司名）
4. travel - 旅遊規劃（關鍵詞：想去...玩、想去...旅遊、規劃行程）

請以 JSON 格式回覆：
{
    "intent": "weather" | "exchange" | "stock" | "travel",
    "tool_name": "get_weather" | "get_exchange_rate" | "get_stock_price" | null,
    "tool_args": {...} | null
}

Tool 參數格式：
- weather: {"city": "城市名"}
- exchange: {"from_currency": "USD", "to_currency": "TWD", "amount": 100}
- stock: {"symbol": "股票代號"}
- travel: null (不需要 tool_args)

範例：
使用者：台北天氣如何
回覆：{"intent": "weather", "tool_name": "get_weather", "tool_args": {"city": "台北"}}

使用者：100美金換台幣
回覆：{"intent": "exchange", "tool_name": "get_exchange_rate", \
"tool_args": {"from_currency": "USD", "to_currency": "TWD", "amount": 100}}

使用者：台積電股價
回覆：{"intent": "stock", "tool_name": "get_stock_price", \
"tool_args": {"symbol": "2330.TW"}}

使用者：我想去高雄玩
回覆：{"intent": "travel", "tool_name": null, "tool_args": null}
"""


def create_classifier_node(llm_client: LLMClient) -> Any:
    """建立意圖分類節點。

    Args:
        llm_client: LLM 客戶端

    Returns:
        可用於 LangGraph 的節點函式
    """
    from voice_assistant.llm.schemas import ChatMessage

    async def classify_intent(state: FlowState) -> dict[str, Any]:
        """分類意圖節點函式。

        Args:
            state: 流程狀態

        Returns:
            更新的狀態欄位
        """
        user_input = state.get("user_input", "")

        try:
            response = await llm_client.chat(
                messages=[ChatMessage(role="user", content=user_input)],
                system_prompt=CLASSIFIER_SYSTEM_PROMPT,
            )

            # 解析 JSON 回應
            content = response.content or "{}"
            # 移除可能的 markdown 程式碼區塊標記
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])

            result = json.loads(content)

            intent: IntentType = result.get("intent", "weather")
            tool_name = result.get("tool_name")
            tool_args = result.get("tool_args")

            return {
                "intent": intent,
                "tool_name": tool_name,
                "tool_args": tool_args,
            }

        except json.JSONDecodeError:
            # JSON 解析失敗，嘗試從文字推斷
            return _fallback_classify(user_input)
        except Exception as e:
            return {
                "error": f"意圖分類失敗: {e!s}",
            }

    return classify_intent


def _fallback_classify(user_input: str) -> dict[str, Any]:
    """降級分類：基於關鍵字的簡單分類。

    Args:
        user_input: 使用者輸入

    Returns:
        分類結果
    """
    text = user_input.lower()

    # 旅遊關鍵詞
    travel_keywords = ["想去", "旅遊", "旅行", "玩", "走走", "規劃行程"]
    if any(kw in text for kw in travel_keywords):
        return {
            "intent": "travel",
            "tool_name": None,
            "tool_args": None,
        }

    # 天氣關鍵詞
    weather_keywords = ["天氣", "氣溫", "溫度", "下雨"]
    if any(kw in text for kw in weather_keywords):
        # 嘗試提取城市
        cities = [
            "台北",
            "新北",
            "桃園",
            "台中",
            "台南",
            "高雄",
            "基隆",
            "新竹",
            "嘉義",
            "屏東",
            "宜蘭",
            "花蓮",
            "台東",
        ]
        city = next((c for c in cities if c in user_input), "台北")
        return {
            "intent": "weather",
            "tool_name": "get_weather",
            "tool_args": {"city": city},
        }

    # 匯率關鍵詞
    exchange_keywords = ["匯率", "換台幣", "換美金", "換日幣"]
    if any(kw in text for kw in exchange_keywords):
        return {
            "intent": "exchange",
            "tool_name": "get_exchange_rate",
            "tool_args": {"from_currency": "USD", "to_currency": "TWD", "amount": 1},
        }

    # 股票關鍵詞
    stock_keywords = ["股價", "股票"]
    if any(kw in text for kw in stock_keywords):
        return {
            "intent": "stock",
            "tool_name": "get_stock_price",
            "tool_args": {"symbol": "2330.TW"},
        }

    # 預設為天氣查詢
    return {
        "intent": "weather",
        "tool_name": "get_weather",
        "tool_args": {"city": "台北"},
    }
