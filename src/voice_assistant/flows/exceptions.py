"""流程模組自訂例外。"""

from __future__ import annotations


class FlowNotFoundError(Exception):
    """當 FlowRegistry 中找不到指定流程時拋出。"""

    def __init__(self, flow_name: str) -> None:
        self.flow_name = flow_name
        super().__init__(f"找不到流程: {flow_name!r}")
