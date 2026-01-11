"""Supervisor Agent.

負責任務拆解與分派、結果彙整的主控 Agent。
"""

from __future__ import annotations

import json

from voice_assistant.agents.state import (
    AgentResult,
    AgentTask,
    AgentType,
    TaskDecomposition,
)
from voice_assistant.llm.client import LLMClient
from voice_assistant.llm.schemas import ChatMessage

# 任務拆解的系統提示詞
# ruff: noqa: E501
DECOMPOSE_SYSTEM_PROMPT = """\
你是一個任務分析專家。根據使用者的輸入，判斷需要哪些專家來處理。

可用的專家類型：
- weather: 天氣查詢（城市天氣、天氣預報）
- finance: 財務查詢（匯率、股價）
- travel: 旅遊規劃（景點推薦、行程建議）
- general: 通用對話（閒聊、無法分類的請求、出差注意事項）

請分析使用者輸入，拆解成一個或多個子任務。每個子任務指定一個專家類型和具體參數。

回應格式（JSON）：
{
    "reasoning": "分析理由",
    "tasks": [
        {
            "agent_type": "專家類型",
            "description": "任務描述",
            "parameters": {"參數名": "參數值"}
        }
    ]
}

範例1 - 股價匯率查詢：
輸入：「查台積電股價和美金匯率」
輸出：{"reasoning": "使用者需要查詢股價和匯率", "tasks": [{"agent_type": "finance", "description": "查詢台積電股價", "parameters": {"query_type": "stock", "symbol": "2330.TW"}}, {"agent_type": "finance", "description": "查詢美金兌台幣匯率", "parameters": {"query_type": "exchange", "from_currency": "USD", "to_currency": "TWD"}}]}

範例2 - 天氣查詢：
輸入：「台北今天天氣如何」
輸出：{"reasoning": "查詢單一城市天氣", "tasks": [{"agent_type": "weather", "description": "查詢台北天氣", "parameters": {"city": "台北"}}]}

範例3 - 旅遊規劃：
輸入：「我想去台中玩」
輸出：{"reasoning": "旅遊意圖，需天氣與景點", "tasks": [{"agent_type": "weather", "description": "查詢台中天氣", "parameters": {"city": "台中"}}, {"agent_type": "travel", "description": "推薦台中景點", "parameters": {"destination": "台中"}}]}

範例4 - 出差助理：
輸入：「後天要去東京出差」
輸出：{"reasoning": "出差意圖，需天氣、匯率和注意事項", "tasks": [{"agent_type": "weather", "description": "查詢東京天氣", "parameters": {"city": "東京"}}, {"agent_type": "finance", "description": "查詢日圓兌台幣匯率", "parameters": {"query_type": "exchange", "from_currency": "JPY", "to_currency": "TWD"}}, {"agent_type": "general", "description": "東京出差注意事項", "parameters": {"message": "請提供去東京出差的注意事項和建議"}}]}

範例5 - 多城市天氣：
輸入：「台北和高雄今天天氣如何」
輸出：{"reasoning": "查詢多個城市天氣", "tasks": [{"agent_type": "weather", "description": "查詢台北天氣", "parameters": {"city": "台北"}}, {"agent_type": "weather", "description": "查詢高雄天氣", "parameters": {"city": "高雄"}}]}
"""

# 結果彙整的系統提示詞
AGGREGATE_SYSTEM_PROMPT = """\
你是一個回應整合專家。根據使用者的原始問題和多個專家的回應結果，生成自然完整的回應。

注意事項：
1. 整合所有成功的結果，用自然語言呈現
2. 如果有部分失敗，說明哪些資訊無法取得
3. 回應應該簡潔但完整
4. 使用繁體中文回應
"""


class SupervisorAgent:
    """Supervisor Agent - 負責任務拆解與分派。

    Args:
        llm_client: LLM 客戶端（用於意圖識別與任務拆解）
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """初始化 Supervisor Agent。"""
        self.llm_client = llm_client

    async def decompose(self, user_input: str) -> TaskDecomposition:
        """將使用者輸入拆解為多個 Agent 任務。

        Args:
            user_input: 使用者原始輸入

        Returns:
            TaskDecomposition: 包含任務清單與拆解理由
        """
        messages = [ChatMessage(role="user", content=user_input)]

        response = await self.llm_client.chat(
            messages=messages,
            system_prompt=DECOMPOSE_SYSTEM_PROMPT,
        )

        # 解析 JSON 回應
        try:
            content = response.content or ""
            # 嘗試提取 JSON（可能包含 markdown 格式）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())

            # 轉換為 AgentTask 列表
            tasks = []
            for task_data in result.get("tasks", []):
                agent_type = AgentType(task_data["agent_type"])
                task = AgentTask(
                    agent_type=agent_type,
                    description=task_data["description"],
                    parameters=task_data.get("parameters", {}),
                )
                tasks.append(task)

            # 如果沒有任務，建立一個 general 任務
            if not tasks:
                tasks = [
                    AgentTask(
                        agent_type=AgentType.GENERAL,
                        description=user_input,
                        parameters={"message": user_input},
                    )
                ]

            return TaskDecomposition(
                tasks=tasks,
                reasoning=result.get("reasoning", ""),
            )

        except (json.JSONDecodeError, KeyError, ValueError):
            # 解析失敗，fallback 到 general agent
            return TaskDecomposition(
                tasks=[
                    AgentTask(
                        agent_type=AgentType.GENERAL,
                        description=user_input,
                        parameters={"message": user_input},
                    )
                ],
                reasoning="無法解析任務，交由 General Agent 處理",
            )

    async def aggregate(
        self,
        user_input: str,
        results: list[AgentResult],
    ) -> str:
        """彙整多個 Agent 結果為自然語言回應。

        Args:
            user_input: 原始使用者輸入（用於上下文）
            results: Agent 執行結果清單

        Returns:
            str: 自然語言回應
        """
        # 整理結果資訊
        results_summary = []
        for result in results:
            if result.success:
                data_str = json.dumps(result.data, ensure_ascii=False)
                results_summary.append(f"[{result.agent_type.value}] 成功: {data_str}")
            else:
                results_summary.append(
                    f"[{result.agent_type.value}] 失敗: {result.error}"
                )

        # 建立彙整請求
        aggregate_request = f"""使用者問題：{user_input}

專家回應結果：
{chr(10).join(results_summary)}

請整合以上資訊，生成一個自然的回應。"""

        messages = [ChatMessage(role="user", content=aggregate_request)]

        response = await self.llm_client.chat(
            messages=messages,
            system_prompt=AGGREGATE_SYSTEM_PROMPT,
        )

        return response.content or "抱歉，無法生成回應。"
