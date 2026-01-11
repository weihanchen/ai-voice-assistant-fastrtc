"""Finance Agent.

財務查詢專家 Agent，負責處理匯率與股價相關的任務。
"""

from __future__ import annotations

import time

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.state import AgentResult, AgentTask, AgentType
from voice_assistant.tools.registry import ToolRegistry


class FinanceAgent(BaseAgent):
    """財務查詢 Agent（匯率+股價）。

    Args:
        tool_registry: Tool 註冊表
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        """初始化 Finance Agent。"""
        self._tool_registry = tool_registry

    @property
    def agent_type(self) -> AgentType:
        """回傳 Agent 類型。"""
        return AgentType.FINANCE

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行財務查詢。

        支援的 task.parameters:
            匯率查詢:
                - query_type: "exchange"
                - from_currency: str
                - to_currency: str
                - amount: float (optional)
            股價查詢:
                - query_type: "stock"
                - symbol: str

        Returns:
            AgentResult with data (匯率):
                - from_currency: str
                - to_currency: str
                - rate: float
            AgentResult with data (股價):
                - symbol: str
                - price: float
                - currency: str
        """
        start_time = time.time()

        try:
            query_type = task.parameters.get("query_type", "").lower()

            if query_type == "exchange":
                return await self._execute_exchange(task, start_time)
            elif query_type == "stock":
                return await self._execute_stock(task, start_time)
            else:
                # 嘗試根據參數推斷類型
                if "symbol" in task.parameters or "stock" in task.parameters:
                    return await self._execute_stock(task, start_time)
                elif "from_currency" in task.parameters:
                    return await self._execute_exchange(task, start_time)
                else:
                    return AgentResult(
                        task_id=task.task_id,
                        agent_type=self.agent_type,
                        success=False,
                        error="無法識別查詢類型，請指定 query_type (exchange/stock)",
                        execution_time=time.time() - start_time,
                    )

        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=f"財務查詢發生錯誤: {e}",
                execution_time=time.time() - start_time,
            )

    async def _execute_exchange(
        self, task: AgentTask, start_time: float
    ) -> AgentResult:
        """執行匯率查詢。"""
        from_currency = task.parameters.get("from_currency")
        if not from_currency:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error="缺少必要參數: from_currency",
                execution_time=time.time() - start_time,
            )

        to_currency = task.parameters.get("to_currency", "TWD")
        amount = task.parameters.get("amount", 1.0)

        tool_result = await self._tool_registry.execute(
            "get_exchange_rate",
            {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "amount": amount,
            },
        )

        execution_time = time.time() - start_time

        if tool_result.success:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=True,
                data=tool_result.data,
                execution_time=execution_time,
            )
        else:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=tool_result.error or "匯率查詢失敗",
                execution_time=execution_time,
            )

    async def _execute_stock(self, task: AgentTask, start_time: float) -> AgentResult:
        """執行股價查詢。"""
        symbol = task.parameters.get("symbol") or task.parameters.get("stock")
        if not symbol:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error="缺少必要參數: symbol",
                execution_time=time.time() - start_time,
            )

        tool_result = await self._tool_registry.execute(
            "get_stock_price",
            {"stock": symbol},
        )

        execution_time = time.time() - start_time

        if tool_result.success:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=True,
                data=tool_result.data,
                execution_time=execution_time,
            )
        else:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=tool_result.error or "股價查詢失敗",
                execution_time=execution_time,
            )
