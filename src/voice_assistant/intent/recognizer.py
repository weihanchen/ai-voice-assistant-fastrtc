"""
意圖辨識器骨架。
"""

import json

from voice_assistant.llm.client import LLMClient
from voice_assistant.llm.schemas import ChatMessage

from .schemas import Intent


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
        ]

        # 使用明確的 system prompt 指導 LLM 僅在明確切換指令時呼叫 function
        system_msg = """你是一個意圖識別助手。
你的任務是判斷使用者是否**明確要求切換語音助理的角色**。

**只有在以下情況才呼叫 switch_role 函式：**
- 使用者明確說「切換到XXX」、「換成XXX模式」、「我要XXX角色」等切換指令
- XXX 必須是：助理、教練、面試官之一

**不要呼叫 switch_role 的情況：**
- 普通對話或詢問問題（如：「台北天氣如何」、「你好」、「幫我查詢資料」）
- 使用者沒有明確提到角色切換

如果不是明確的切換指令，請不要呼叫任何函式。"""

        user_msg = ChatMessage(role="user", content=text)
        response = await self.llm_client.chat(
            [user_msg], tools=tools, system_prompt=system_msg
        )
        tool_calls = response.tool_calls or []
        for call in tool_calls:
            if call.function.get("name") == "switch_role":
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
        # fallback: 無 tool_call
        return Intent(name="unknown", description="未識別命令", params={}, score=None)

    def recognize(self, text: str) -> Intent:
        """
        從文字中推斷意圖（同步版本佔位）。
        """
        raise NotImplementedError("請用 recognize_intent_with_llm 或自行實作同步識別")
