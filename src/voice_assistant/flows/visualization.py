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


def apply_node_labels(
    mermaid_code: str,
    label_map: dict[str, str],
) -> str:
    """將 Mermaid 流程圖中的節點 ID 替換為使用者友善的顯示標籤。

    保留原始節點 ID 作為 Mermaid 節點識別碼，僅加入中括號標籤。
    例如：``__start__`` → ``__start__[開始]``，
    ``classifier`` → ``classifier[意圖分類]``。

    對於已經有標籤的節點（如 ``node[Label]``），會替換既有標籤。
    對於 LangGraph 自動產生的特殊格式（如 ``__start__([<p>__start__</p>])``），
    會替換為簡潔的標籤格式。

    Args:
        mermaid_code: 原始 Mermaid 原始碼
        label_map: 節點 ID 到顯示標籤的映射

    Returns:
        替換標籤後的 Mermaid 原始碼
    """
    def replace_bracket_label(text: str, node_id: str, label: str) -> str:
        needle = f"{node_id}["
        index = 0
        result_parts: list[str] = []

        while True:
            start = text.find(needle, index)
            if start == -1:
                result_parts.append(text[index:])
                break

            # 將命中的節點前段落保留
            result_parts.append(text[index:start])
            bracket_start = start + len(node_id)
            scan_index = bracket_start + 1
            depth = 1
            quote: str | None = None
            escape = False

            while scan_index < len(text):
                char = text[scan_index]
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif quote:
                    if char == quote:
                        quote = None
                else:
                    if char in ("'", '"'):
                        quote = char
                    elif char == "[":
                        depth += 1
                    elif char == "]":
                        depth -= 1
                        if depth == 0:
                            scan_index += 1
                            break
                scan_index += 1

            if depth != 0:
                # 找不到完整配對，避免卡住，保留原文
                result_parts.append(text[start:])
                break

            result_parts.append(f"{node_id}[{label}]")
            index = scan_index

        return "".join(result_parts)

    result = mermaid_code
    for node_id, label in label_map.items():
        # 匹配 LangGraph 常見的節點定義格式：
        # 1. node_id([<p>node_id</p>]) — LangGraph __start__/__end__ 格式
        # 2. node_id[Label] 或 node_id["Label"] — 一般節點
        # 3. node_id(Label) — 圓角節點
        # 4. 單獨的 node_id（無括號）— 邊定義中的節點引用不處理

        # 先處理 LangGraph 特殊格式：node_id([<p>...</p>])
        stadium_pattern = re.compile(
            rf'{re.escape(node_id)}\(\[["<].*?[">]\]\)',
        )
        result = stadium_pattern.sub(f"{node_id}([{label}])", result)

        # 再處理一般方括號格式：node_id[...] 或 node_id["..."]，支援巢狀與引號
        result = replace_bracket_label(result, node_id, label)

        # 處理圓括號格式：node_id(...)（但排除已處理的 ([ ]) 格式）
        paren_pattern = re.compile(
            rf"{re.escape(node_id)}\((?!\[)[^\)]*\)",
        )
        result = paren_pattern.sub(f"{node_id}([{label}])", result)

    return result


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
