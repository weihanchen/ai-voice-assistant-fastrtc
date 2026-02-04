"""
角色選擇器 UI 元件 ─ Gradio dropdown + 狀態顯示 glue
"""

from collections.abc import Callable
from typing import Any

import gradio as gr


def create_role_selector(
    available_roles: dict[str, str],  # id: 顯示名稱
    on_role_change: Callable[[str], Any],
    current_role_id: str | None = None,
    label: str = "選擇角色：",
):
    """
    建立 Gradio 下拉選單作為角色切換介面。使用者選擇後自動調用 callback。
    Args:
        available_roles: 角色字典
        on_role_change: 切換 callback（傳 selected id）
        current_role_id: 預設選中角色 id
        label: UI 標題
    Returns: gr.Dropdown
    """
    options = list(available_roles.keys())
    default_value = (
        current_role_id
        if current_role_id is not None and current_role_id in available_roles
        else (next(iter(available_roles)) if available_roles else "")
    )
    dd = gr.Dropdown(
        choices=options,
        value=default_value,
        label=label,
    )

    def _on_change(role_id):
        if role_id:
            on_role_change(role_id)

    dd.change(_on_change, inputs=dd, outputs=None)
    return dd


def create_role_selector_with_status(
    available_roles: dict[str, str],  # id: 顯示名稱
    on_role_change: Callable[[str], Any],
    current_role_id: str | None = None,
    label: str = "選擇角色：",
):
    """
    建立帶狀態文字的角色下拉選單與即時狀態回饋。
    Returns: (gr.Dropdown, gr.Textbox)
    """
    options = [(rid, name) for rid, name in available_roles.items()]
    default_value = (
        current_role_id
        if current_role_id is not None and current_role_id in available_roles
        else (next(iter(available_roles)) if available_roles else "")
    )
    status = gr.Textbox(
        value=f"目前角色：{available_roles.get(default_value, '')}",
        label="角色狀態",
        interactive=False,
    )
    dropdown = gr.Dropdown(
        choices=options,
        value=default_value,
        label=label,
    )

    def _on_change(role_id):
        if role_id:
            on_role_change(role_id)
            # 用新角色名稱更新狀態顯示
            return f"目前角色：{available_roles.get(role_id, '')}"
        return status.value

    dropdown.change(_on_change, inputs=dropdown, outputs=status)
    return dropdown, status
