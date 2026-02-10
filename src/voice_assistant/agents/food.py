"""Food Recommendation Agent.

美食推薦專家代理，處理餐廳推薦相關請求。
"""

from __future__ import annotations

import logging
from time import time

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.state import AgentResult, AgentTask, AgentType
from voice_assistant.flows.food_executor import FoodRecommendFlowExecutor
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class FoodAgent(BaseAgent):
    """美食推薦專家代理。

    負責處理美食推薦相關任務，包括：
    - 根據城市和天氣推薦餐廳
    - 考慮室內/戶外場地適合性
    - 提供詳細的餐廳資訊

    Attributes:
        agent_type: AgentType.FOOD
        executor: FoodRecommendFlowExecutor 實例
        timeout: 執行逾時（秒）
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        timeout: float = 30.0,
    ) -> None:
        """初始化美食推薦代理。

        Args:
            llm_client: LLM 客戶端
            tool_registry: 工具註冊表
            timeout: 執行逾時（秒）
        """
        self._timeout = timeout
        self.executor = FoodRecommendFlowExecutor(llm_client, tool_registry)

    @property
    def agent_type(self) -> AgentType:
        """回傳 Agent 類型。"""
        return AgentType.FOOD

    @property
    def timeout(self) -> float:
        """回傳執行逾時時間。"""
        return self._timeout

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行美食推薦任務。

        Args:
            task: 任務定義（包含使用者輸入和參數）

        Returns:
            AgentResult: 包含推薦結果或錯誤訊息
        """
        start_time = time()

        try:
            # 從任務描述中提取使用者輸入
            user_input = task.description

            # 執行美食推薦流程
            response = await self.executor.execute(user_input)

            execution_time = time() - start_time

            # 檢查是否有錯誤
            if "錯誤" in response or "失敗" in response:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=self.agent_type,
                    success=False,
                    error=response,
                    execution_time=execution_time,
                )

            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=True,
                data={"response": response},
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time() - start_time
            logger.exception("[FoodAgent] 執行失敗")
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=f"美食推薦處理失敗: {e!s}",
                execution_time=execution_time,
            )
