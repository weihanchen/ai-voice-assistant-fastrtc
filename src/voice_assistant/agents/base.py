"""Base Agent Abstract Class.

定義所有專家 Agent 的抽象基底類別。
"""

from abc import ABC, abstractmethod

from voice_assistant.agents.state import AgentResult, AgentTask, AgentType


class BaseAgent(ABC):
    """Agent 抽象基底類別。

    所有專家 Agent 必須繼承此類別並實作 execute 方法。
    """

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """回傳 Agent 類型識別碼。

        Returns:
            AgentType: Agent 類型（WEATHER/FINANCE/TRAVEL/GENERAL）
        """
        ...

    @property
    def timeout(self) -> float:
        """執行逾時秒數（可覆寫）。

        Returns:
            float: 預設 10.0 秒
        """
        return 10.0

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """執行任務。

        Args:
            task: 待執行的任務

        Returns:
            AgentResult: 執行結果

        Note:
            不應拋出例外，錯誤應包裝在 AgentResult.error 中
        """
        ...
