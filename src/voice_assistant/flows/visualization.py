"""流程視覺化模組。

提供 Mermaid 格式的流程圖輸出功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


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
