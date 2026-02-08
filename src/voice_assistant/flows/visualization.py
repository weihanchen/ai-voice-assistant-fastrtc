"""流程視覺化模組。

提供 Mermaid 格式的流程圖輸出功能，支援節點狀態高亮。
"""

from __future__ import annotations

import re
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


class NodeStatus(str, Enum):
    """節點執行狀態。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FlowVisualization(BaseModel):
    """流程視覺化資料模型。

    封裝 Mermaid 原始碼與各節點的執行狀態。

    Attributes:
        mermaid_code: Mermaid 格式的流程圖原始碼
        node_statuses: 節點名稱到執行狀態的映射
    """

    mermaid_code: str
    node_statuses: dict[str, NodeStatus] = Field(default_factory=dict)


def get_mermaid_diagram(graph: CompiledStateGraph) -> str:
    """產生流程圖的 Mermaid 原始碼。

    Args:
        graph: 編譯後的 LangGraph

    Returns:
        Mermaid 格式字串
    """
    return graph.get_graph().draw_mermaid()


def save_mermaid_png(graph: CompiledStateGraph, output_path: str) -> None:
    """將流程圖儲存為 PNG 圖片。

    注意：此功能需要額外安裝 graphviz 相關依賴。

    Args:
        graph: 編譯後的 LangGraph
        output_path: 輸出檔案路徑
    """
    png_data = graph.get_graph().draw_mermaid_png()
    with open(output_path, "wb") as f:
        f.write(png_data)


def render_mermaid_with_status(
    mermaid_code: str,
    node_statuses: dict[str, NodeStatus] | None = None,
) -> str:
    """為 Mermaid 流程圖注入節點狀態 CSS class。

    將節點狀態映射為 Mermaid CSS class 標記（如 :::running），
    讓前端可以根據狀態套用不同樣式。

    Args:
        mermaid_code: 原始 Mermaid 原始碼
        node_statuses: 節點名稱到狀態的映射，為 None 或空 dict 時回傳原始碼

    Returns:
        注入狀態 CSS class 後的 Mermaid 原始碼
    """
    if not node_statuses:
        return mermaid_code

    result = mermaid_code
    for node_name, status in node_statuses.items():
        # 匹配 Mermaid 節點定義（例如 "node_id[Label]" 或 "node_id(Label)"）
        # 支援多種括號格式：[]、()、{}、([])、[[]]
        pattern = re.compile(
            rf"({re.escape(node_name)}"  # 節點 ID
            r'(?:\[[\["]?[^\]]*[\]"]?\]'  # [...] 或 [["..."]]
            r"|\([^\)]*\)"  # (...)
            r"|\{[^\}]*\}"  # {...}
            r"))"  # 結尾
        )
        replacement = rf"\1:::{status.value}"
        result = pattern.sub(replacement, result)

    return result
