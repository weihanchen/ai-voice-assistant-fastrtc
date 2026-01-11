"""Weather Agent.

天氣查詢專家 Agent，負責處理天氣相關的任務。
"""

from __future__ import annotations

import time

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.state import AgentResult, AgentTask, AgentType
from voice_assistant.tools.registry import ToolRegistry


class WeatherAgent(BaseAgent):
    """天氣查詢 Agent。

    Args:
        tool_registry: Tool 註冊表（用於取得 WeatherTool）
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        """初始化 Weather Agent。"""
        self._tool_registry = tool_registry

    @property
    def agent_type(self) -> AgentType:
        """回傳 Agent 類型。"""
        return AgentType.WEATHER

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行天氣查詢。

        支援的 task.parameters:
            - city: str - 城市名稱（必填）
            - include_details: bool - 是否包含詳細資訊（選填）

        Returns:
            AgentResult with data:
                - city: str
                - temperature: float
                - weather: str
                - humidity: float (if include_details)
        """
        start_time = time.time()

        try:
            # 取得參數
            city = task.parameters.get("city")
            if not city:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=self.agent_type,
                    success=False,
                    error="缺少必要參數: city",
                    execution_time=time.time() - start_time,
                )

            include_details = task.parameters.get("include_details", False)

            # 執行 Tool
            tool_result = await self._tool_registry.execute(
                "get_weather",
                {"city": city, "include_details": include_details},
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
                    error=tool_result.error or "天氣查詢失敗",
                    execution_time=execution_time,
                )

        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=f"天氣查詢發生錯誤: {e}",
                execution_time=time.time() - start_time,
            )
