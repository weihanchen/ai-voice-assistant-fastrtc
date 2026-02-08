"""流程執行器基底類別。

定義所有流程執行器的統一介面，消除 VoicePipeline 中的 if/elif 分支。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseFlowExecutor(ABC):
    """流程執行器抽象基底類別。

    所有流程模式（Tool Calling、LangGraph、Multi-Agent）
    都必須繼承此類別並實作統一介面。
    """

    @property
    @abstractmethod
    def flow_name(self) -> str:
        """流程名稱，用於 FlowRegistry 識別。"""

    @abstractmethod
    async def execute(self, user_input: str) -> str:
        """執行流程並回傳回應文字。

        Args:
            user_input: 使用者輸入的文字。

        Returns:
            LLM 產生的回應文字。
        """

    def get_visualization(self) -> str | None:
        """取得流程的 Mermaid 視覺化圖表。

        預設回傳 None，子類別可覆寫以提供視覺化。

        Returns:
            Mermaid 格式的流程圖字串，或 None。
        """
        return None
