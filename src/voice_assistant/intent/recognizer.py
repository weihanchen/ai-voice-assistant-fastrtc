"""
意圖辨識器骨架。
"""

import json
import logging

from voice_assistant.llm.client import LLMClient
from voice_assistant.llm.schemas import ChatMessage

from .schemas import Intent

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """意圖辨識器基底類別，支援 LLM function calling。"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def recognize_intent_with_llm(self, text: str) -> Intent:
        """
        使用 OpenAI Function Calling 辨識語音指令 intent。
        """
        from .schemas import Intent

        # 定義 function calling 規格
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "switch_role",
                    "description": (
                        "當使用者**明確要求切換角色**時使用"
                        "（例如：「切換到面試官」、「換成教練模式」）。"
                        "如果只是普通對話或詢問問題，請勿呼叫此函式。"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "role_id": {
                                "type": "string",
                                "description": (
                                    "目標角色 id，必須是以下之一："
                                    "assistant（助理）、coach（教練）、"
                                    "interviewer（面試官）"
                                ),
                                "enum": ["assistant", "coach", "interviewer"],
                            }
                        },
                        "required": ["role_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "food_recommendation",
                    "description": (
                        "當使用者要求**美食/餐廳推薦**時使用"
                        "（例如：「推薦台北的餐廳」、「今天吃什麼」、「附近有什麼好吃的」）。"
                        "如果沒有明確提及美食/餐廳相關需求，請勿呼叫此函式。"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "美食推薦查詢文字，"
                                    "例如：「台北的高級餐廳」、「今天天氣推薦室內或戶外」"
                                ),
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

        # 使用明確的 system prompt 指導 LLM 僅在明確指令時呼叫 function
        system_msg = """你是一個意圖識別助手。
你的任務是判斷使用者的真實意圖，並在符合條件時呼叫相應函式。

**切換角色情況（呼叫 switch_role）：**
- 使用者明確說「切換到XXX」、「換成XXX模式」、「我要XXX角色」等切換指令
- XXX 必須是：助理、教練、面試官之一

**美食推薦情況（呼叫 food_recommendation）：**
- 使用者詢問美食/餐廳推薦（如：「推薦台北的餐廳」、「吃什麼」）
- 使用者要求基於天氣或地點的餐飲建議

**不要呼叫任何函式的情況：**
- 普通對話或詢問問題（如：「台北天氣如何」、「你好」、「幫我查詢資料」）
- 使用者沒有明確提到角色切換或美食推薦需求"""

        user_msg = ChatMessage(role="user", content=text)

        # 在 try/except 塊中包裝外部 API 調用
        try:
            response = await self.llm_client.chat(
                [user_msg], tools=tools, system_prompt=system_msg
            )
        except Exception as e:
            logger.exception(
                "意圖辨識 LLM API 調用失敗 - "
                "user_msg.content=%s, "
                "tools names=%s, "
                "system_msg length=%d, "
                "error=%s",
                text[:100],  # 限制日誌中的文本長度
                [t["function"]["name"] for t in tools],
                len(system_msg),
                str(e),
            )
            # 返回錯誤意圖而非靜默失敗
            return Intent(
                name="error",
                description=f"意圖辨識服務暫時無法使用：{type(e).__name__}",
                params={"error_context": "llm_api_call_failed"},
                score=None,
            )

        tool_calls = response.tool_calls or []
        for call in tool_calls:
            function_name = call.function.get("name")
            if function_name == "switch_role":
                # 解析 arguments json
                try:
                    args = json.loads(call.function["arguments"])
                except Exception:
                    args = {}
                return Intent(
                    name="switch_role",
                    description="使用者要求切換角色",
                    params=args,
                    score=None,
                )
            elif function_name == "food_recommendation":
                # 解析 arguments json
                try:
                    args = json.loads(call.function["arguments"])
                except Exception:
                    args = {}
                return Intent(
                    name="food_recommendation",
                    description="使用者要求美食推薦",
                    params=args,
                    score=None,
                )
        # fallback: 無 tool_call
        return Intent(name="unknown", description="未識別命令", params={}, score=None)

    def recognize(self, text: str) -> Intent:
        """
        從文字中推斷意圖（同步版本佔位）。
        """
        raise NotImplementedError("請用 recognize_intent_with_llm 或自行實作同步識別")
