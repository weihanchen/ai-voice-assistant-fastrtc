"""General Agent.

通用對話專家 Agent，負責處理閒聊及無法分類的請求。
"""

from __future__ import annotations

import time

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.state import AgentResult, AgentTask, AgentType
from voice_assistant.llm.client import LLMClient
from voice_assistant.llm.schemas import ChatMessage

# 通用對話的系統提示詞
GENERAL_SYSTEM_PROMPT = """\
你是一個友善的語音助理。請用繁體中文回應使用者的問題或對話。

注意事項：
1. 保持回應簡潔，適合語音朗讀
2. 如果無法回答問題，請友善地說明
3. 不要使用表情符號或特殊符號
4. 如果是出差相關問題，請提供實用的注意事項（如簽證、電壓、時差、交通等）"""


class GeneralAgent(BaseAgent):
    """通用 Agent（閒聊/Fallback）。

    Args:
        llm_client: LLM 客戶端
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """初始化 General Agent。"""
        self._llm_client = llm_client

    @property
    def agent_type(self) -> AgentType:
        """回傳 Agent 類型。"""
        return AgentType.GENERAL

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行通用對話。

        支援的 task.parameters:
            - message: str - 對話內容（必填）

        Returns:
            AgentResult with data:
                - response: str
        """
        start_time = time.time()

        try:
            # 取得參數
            message = task.parameters.get("message") or task.description
            if not message:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=self.agent_type,
                    success=False,
                    error="缺少必要參數: message",
                    execution_time=time.time() - start_time,
                )

            # 呼叫 LLM
            messages = [ChatMessage(role="user", content=message)]

            response = await self._llm_client.chat(
                messages=messages,
                system_prompt=GENERAL_SYSTEM_PROMPT,
            )

            execution_time = time.time() - start_time

            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=True,
                data={"response": response.content or ""},
                execution_time=execution_time,
            )

        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=f"對話處理發生錯誤: {e}",
                execution_time=time.time() - start_time,
            )
