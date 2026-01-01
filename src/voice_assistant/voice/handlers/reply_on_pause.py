"""FastRTC ReplyOnPause 處理器整合

建立 FastRTC 語音串流，配置 ReplyOnPause 機制。
"""

import logging

import gradio as gr
import numpy as np
from fastrtc import AlgoOptions, ReplyOnPause, SileroVadOptions, Stream, WebRTC

from voice_assistant.config import Settings
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools import (
    ExchangeRateTool,
    StockPriceTool,
    ToolRegistry,
    WeatherTool,
)
from voice_assistant.voice.pipeline import VoicePipeline
from voice_assistant.voice.schemas import VoicePipelineConfig
from voice_assistant.voice.ui import (
    additional_outputs_handler,
    audio_input_handler,
    create_additional_outputs,
)

logger = logging.getLogger(__name__)


def create_voice_stream(settings: Settings) -> Stream:
    """建立 FastRTC 語音串流

    Args:
        settings: 應用程式設定

    Returns:
        配置好的 FastRTC Stream（已設定自定義 UI 與事件綁定）
    """
    # 初始化 LLM Client
    llm_client = LLMClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )

    # 建立語音管線配置
    config = VoicePipelineConfig(
        stt={
            "model_size": settings.whisper_model_size,
            "model_path": settings.whisper_model_path,
            "language": settings.whisper_language,
            "device": settings.whisper_device,
        },
        tts={
            "model_path": settings.tts_model_path,
            "voice": settings.tts_voice,
            "speed": settings.tts_speed,
        },
        vad={
            "pause_threshold_ms": settings.vad_pause_threshold_ms,
            "min_speech_duration_ms": settings.vad_min_speech_duration_ms,
            "speech_threshold": settings.vad_speech_threshold,
            "min_silence_duration_ms": settings.vad_min_silence_duration_ms,
        },
        can_interrupt=True,
        server_host=settings.server_host,
        server_port=settings.server_port,
    )

    # 初始化工具註冊表（Composition Root）
    tool_registry = ToolRegistry()
    tool_registry.register(WeatherTool())
    tool_registry.register(ExchangeRateTool())
    tool_registry.register(StockPriceTool())

    # 初始化語音管線
    pipeline = VoicePipeline(
        config=config,
        llm_client=llm_client,
        tool_registry=tool_registry,
    )

    # 建立額外輸出元件（Chatbot 和狀態）
    chatbot, status_display = create_additional_outputs()

    # 建立 FastRTC Stream（使用 process_audio_with_outputs 以支援 AdditionalOutputs）
    stream = Stream(
        handler=ReplyOnPause(
            pipeline.process_audio_with_outputs,
            algo_options=AlgoOptions(
                audio_chunk_duration=config.vad.pause_threshold_ms / 1000,
                started_talking_threshold=0.2,
                speech_threshold=config.vad.speech_threshold,
            ),
            model_options=SileroVadOptions(
                threshold=0.5,
                min_speech_duration_ms=config.vad.min_speech_duration_ms,
                min_silence_duration_ms=config.vad.pause_threshold_ms,
            ),
            can_interrupt=config.can_interrupt,
            output_sample_rate=config.tts.sample_rate,
        ),
        modality="audio",
        mode="send-receive",
        additional_outputs=[chatbot, status_display],
        additional_outputs_handler=additional_outputs_handler,
    )

    # 建立清除對話的函式（閉包，捕獲 pipeline 參考）
    def clear_conversation() -> tuple[list[dict[str, str]], str]:
        """清除對話歷史

        同時清除 UI 顯示和 pipeline 內部狀態。

        Returns:
            (empty_chatbot, reset_status)
        """
        pipeline.state.history.clear()
        logger.info("[Handler] 對話歷史已清除")
        return [], "🟢 待命"

    # 建立處理上傳音訊的函式（閉包，捕獲 pipeline 參考）
    def process_uploaded_audio(
        audio: tuple[int, np.ndarray] | None,
        current_chatbot: list[dict[str, str]],
        current_status: str,
    ) -> tuple[list[dict[str, str]], str, None]:
        """處理上傳的音訊檔案

        Args:
            audio: (sample_rate, audio_array) 或 None
            current_chatbot: 目前的對話記錄
            current_status: 目前的狀態文字

        Returns:
            (updated_chatbot, updated_status, cleared_audio_input)
        """
        if audio is None:
            return current_chatbot, current_status, None

        # 轉換音訊格式
        processed_audio = audio_input_handler(audio)
        if processed_audio is None:
            return current_chatbot, current_status, None

        logger.info("[Handler] 開始處理上傳的音訊檔案")

        # 使用 pipeline 處理音訊（同步方式）
        # 收集所有輸出
        final_chatbot = current_chatbot
        final_status = current_status

        try:
            for output in pipeline.process_audio_with_outputs(processed_audio):
                # 檢查是否為 AdditionalOutputs
                if hasattr(output, "args"):
                    # AdditionalOutputs 物件
                    final_chatbot = output.args[0]
                    final_status = output.args[1]
                # 音訊輸出在這裡忽略（不播放 TTS）
        except Exception as e:
            logger.error(f"[Handler] 處理上傳音訊失敗: {e}", exc_info=True)
            final_status = f"❌ 處理失敗: {e}"

        logger.info("[Handler] 上傳音訊處理完成")
        return final_chatbot, final_status, None

    # 建立自訂 UI，添加音訊上傳功能
    sidebar_css = """
    .gradio-container .sidebar {
        background-color: color-mix(
            in srgb, var(--block-background-fill) 50%, transparent
        ) !important;
    }
    body.dark .gradio-container .sidebar {
        background-color: color-mix(
            in srgb, var(--block-background-fill) 50%, transparent
        ) !important;
    }
    """
    with gr.Blocks(title="AI 語音助理", css=sidebar_css) as custom_ui:
        gr.HTML("<h1 style='text-align: center'>AI 語音助理</h1>")

        with gr.Row():
            # 左側：對話記錄（主要區域）
            with gr.Column(scale=2):
                chatbot.render()
                clear_btn = gr.Button("🗑️ 清除對話", variant="secondary")

            # 右側：控制區
            with gr.Column(scale=1):
                # WebRTC 串流元件（放在右側上方，關閉全螢幕模式）
                webrtc = WebRTC(
                    label="語音串流",
                    mode="send-receive",
                    modality="audio",
                    full_screen=False,
                )
                stream.webrtc_component = webrtc

                status_display.render()

                # 音訊上傳區
                with gr.Accordion("📁 音訊檔案測試模式", open=False):
                    gr.Markdown(
                        "上傳預錄的音訊檔案來測試對話功能，"
                        "適用於無法使用麥克風的環境。"
                    )
                    audio_input = gr.Audio(
                        label="上傳音訊檔案",
                        type="numpy",
                        sources=["upload"],
                    )
                    submit_btn = gr.Button("🎯 處理音訊", variant="primary")

        # 綁定 WebRTC 串流事件
        webrtc.stream(
            fn=stream.event_handler,
            inputs=[webrtc],
            outputs=[webrtc],
            time_limit=stream.time_limit,
            concurrency_limit=stream.concurrency_limit,
        )

        # 綁定 AdditionalOutputs 事件
        webrtc.on_additional_outputs(
            additional_outputs_handler,
            inputs=[chatbot, status_display],
            outputs=[chatbot, status_display],
            concurrency_limit=stream.concurrency_limit,
        )

        # 綁定音訊上傳處理事件
        submit_btn.click(
            fn=process_uploaded_audio,
            inputs=[audio_input, chatbot, status_display],
            outputs=[chatbot, status_display, audio_input],
        )

        # 綁定清除對話事件
        clear_btn.click(
            fn=clear_conversation,
            inputs=[],
            outputs=[chatbot, status_display],
        )

    # 替換 Stream 的預設 UI
    stream.ui = custom_ui

    return stream
