"""Gradio Blocks UI 定義

提供自定義對話介面，整合 WebRTC 音訊與文字顯示。
"""

import logging
from typing import TYPE_CHECKING

import gradio as gr
import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

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
    try:
        logger.debug(f"[UI] 更新 - 狀態: {new_status}, 訊息數: {len(new_history)}")
        return (new_history, new_status)
    except Exception as e:
        logger.error(f"[UI] 更新失敗: {e}", exc_info=True)
        return (old_chatbot, old_status)


def create_audio_input() -> gr.Audio:
    """建立音訊上傳元件

    用於上傳預錄音訊檔案，替代麥克風輸入進行測試。

    Returns:
        gr.Audio: 音訊上傳元件
    """
    return gr.Audio(
        label="上傳音訊檔案（測試用）",
        type="numpy",
        sources=["upload"],
        show_label=True,
    )


def audio_input_handler(
    audio: tuple[int, "NDArray[np.float32]"] | None,
) -> tuple[int, "NDArray[np.float32]"] | None:
    """處理上傳的音訊檔案

    將上傳的音訊轉換為 FastRTC 期望的格式。

    Args:
        audio: (sample_rate, audio_array) 或 None

    Returns:
        轉換後的音訊 tuple 或 None
    """
    if audio is None:
        logger.debug("[UI] 無音訊輸入")
        return None

    sample_rate, audio_array = audio
    logger.info(
        f"[UI] 收到上傳音訊: sample_rate={sample_rate}, "
        f"shape={audio_array.shape}, dtype={audio_array.dtype}"
    )

    # 確保音訊為 float32 格式
    if audio_array.dtype != np.float32:
        if audio_array.dtype == np.int16:
            audio_array = audio_array.astype(np.float32) / 32768.0
        elif audio_array.dtype == np.int32:
            audio_array = audio_array.astype(np.float32) / 2147483648.0
        else:
            audio_array = audio_array.astype(np.float32)
        logger.debug(f"[UI] 音訊轉換為 float32: dtype={audio_array.dtype}")

    # 確保音訊為單聲道
    if audio_array.ndim > 1:
        audio_array = audio_array.mean(axis=1)
        logger.debug(f"[UI] 音訊轉換為單聲道: shape={audio_array.shape}")

    return (sample_rate, audio_array)


def create_custom_ui(
    webrtc_component: gr.components.Component,
    chatbot: gr.Chatbot,
    status_display: gr.Textbox,
    process_uploaded_audio_fn: callable,
) -> gr.Blocks:
    """建立包含音訊上傳功能的自訂 UI

    Args:
        webrtc_component: FastRTC WebRTC 元件
        chatbot: 對話記錄元件
        status_display: 狀態顯示元件
        process_uploaded_audio_fn: 處理上傳音訊的回呼函式

    Returns:
        gr.Blocks: 自訂的 Gradio Blocks UI
    """
    column_css = (
        ".my-column {"
        "display: flex !important; "
        "justify-content: center !important; "
        "align-items: center !important"
        "};"
    )
    with gr.Blocks(title="AI 語音助理", css=column_css) as demo:
        gr.HTML("<h1 style='text-align: center'>AI 語音助理</h1>")

        with gr.Row():
            # 左側：WebRTC 串流
            with gr.Column(scale=1):
                webrtc_component.render()

                # 音訊上傳區
                with gr.Accordion("📁 音訊檔案測試", open=False):
                    audio_input = gr.Audio(
                        label="上傳音訊檔案",
                        type="numpy",
                        sources=["upload"],
                    )
                    submit_btn = gr.Button("🎯 處理音訊", variant="primary")

            # 右側：對話記錄與狀態
            with gr.Column(scale=1):
                chatbot.render()
                status_display.render()

        # 綁定音訊上傳處理事件
        submit_btn.click(
            fn=process_uploaded_audio_fn,
            inputs=[audio_input, chatbot, status_display],
            outputs=[chatbot, status_display, audio_input],
        )

    return demo
