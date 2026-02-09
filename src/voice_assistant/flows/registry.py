"""流程註冊表。

提供流程執行器的集中管理，支援註冊、查詢、列舉等操作。
"""

from __future__ import annotations

import logging

from voice_assistant.flows.base import BaseFlowExecutor
from voice_assistant.flows.exceptions import FlowNotFoundError

logger = logging.getLogger(__name__)


class FlowRegistry:
    """流程執行器註冊表。

    管理所有已註冊的 BaseFlowExecutor 實例，
    提供依名稱查詢的統一介面。
    """

    def __init__(self) -> None:
        self._executors: dict[str, BaseFlowExecutor] = {}

    def register(self, executor: BaseFlowExecutor) -> None:
        """註冊流程執行器。

        Args:
            executor: 要註冊的流程執行器實例。

        Raises:
            ValueError: 若同名流程已存在。
        """
        name = executor.flow_name
        if name in self._executors:
            msg = f"流程 {name!r} 已註冊"
            raise ValueError(msg)
        self._executors[name] = executor
        logger.info("已註冊流程: %s", name)

    def get(self, name: str) -> BaseFlowExecutor:
        """依名稱取得流程執行器。

        Args:
            name: 流程名稱。

        Returns:
            對應的流程執行器實例。

        Raises:
            FlowNotFoundError: 若指定名稱的流程不存在。
        """
        executor = self._executors.get(name)
        if executor is None:
            raise FlowNotFoundError(name)
        return executor

    def list_flows(self) -> list[str]:
        """列出所有已註冊的流程名稱。

        Returns:
            流程名稱列表。
        """
        return list(self._executors.keys())

    def has(self, name: str) -> bool:
        """檢查指定名稱的流程是否已註冊。

        Args:
            name: 流程名稱。

        Returns:
            True 若流程已註冊，否則 False。
        """
        return name in self._executors
