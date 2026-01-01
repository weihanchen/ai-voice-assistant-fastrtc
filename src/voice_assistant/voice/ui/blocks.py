"""Gradio Blocks UI 定義

提供自定義對話介面，整合 WebRTC 音訊與文字顯示。
"""

import logging

import gradio as gr

logger = logging.getLogger(__name__)


def create_additional_outputs() -> list[gr.components.Component]:
    """建立額外輸出元件

    Returns:
        用於 Stream additional_outputs 的元件列表：
        [chatbot, status_display]
    """
    chatbot = gr.Chatbot(
        label="對話記錄",
        type="messages",
        height=400,
        show_label=True,
    )

    status_display = gr.Textbox(
        label="狀態",
        value="🟢 待命",
        interactive=False,
        show_label=True,
    )

    return [chatbot, status_display]


def additional_outputs_handler(
    old_chatbot: list[dict[str, str]],
    old_status: str,
    new_history: list[dict[str, str]],
    new_status: str,
) -> tuple[list[dict[str, str]], str]:
    """處理 AdditionalOutputs 的回呼

    FastRTC 的 additional_outputs_handler 簽章為：
    (old_1, old_2, ..., new_1, new_2, ...) -> (result_1, result_2, ...)

    其中 old_* 是目前 UI 元件的狀態，new_* 是來自 AdditionalOutputs 的新資料。

    Args:
        old_chatbot: 目前 Chatbot 狀態（由 Gradio 自動傳入）
        old_status: 目前狀態顯示狀態（由 Gradio 自動傳入）
        new_history: 來自 AdditionalOutputs 的對話歷史
        new_status: 來自 AdditionalOutputs 的狀態文字

    Returns:
        (updated_chatbot, updated_status)
    """
    logger.debug(f"[UI] 更新 - 狀態: {new_status}, 訊息數: {len(new_history)}")
    return (new_history, new_status)
