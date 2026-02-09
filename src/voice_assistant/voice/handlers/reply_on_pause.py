"""FastRTC ReplyOnPause 處理器整合

建立 FastRTC 語音串流，配置 ReplyOnPause 機制。
"""

import logging

import gradio as gr
import numpy as np
from fastrtc import AlgoOptions, ReplyOnPause, SileroVadOptions, Stream, WebRTC

from voice_assistant.agents import MultiAgentExecutor
from voice_assistant.config import Settings
from voice_assistant.flows import FlowExecutor, FlowRegistry, ToolCallingExecutor
from voice_assistant.llm.client import LLMClient
from voice_assistant.roles.predefined.assistant import AssistantRole
from voice_assistant.roles.predefined.coach import CoachRole
from voice_assistant.roles.predefined.interviewer import InterviewerRole
from voice_assistant.roles.registry import RoleRegistry
from voice_assistant.tools import (
    ToolRegistry,
)
from voice_assistant.voice.pipeline import VoicePipeline
from voice_assistant.voice.schemas import VoicePipelineConfig
from voice_assistant.voice.ui import (
    additional_outputs_handler,
    audio_input_handler,
    create_additional_outputs,
    create_flow_visualization,
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

    # 建立語音管線配置（使用正確 config 類別）
    from voice_assistant.voice.schemas import (
        STTConfig,
        TTSConfig,
        VADConfig,
    )

    config = VoicePipelineConfig(
        stt=STTConfig(
            model_size=settings.whisper_model_size,
            model_path=settings.whisper_model_path,
            language=settings.whisper_language,
            device=settings.whisper_device,
        ),
        tts=TTSConfig(
            model_path=settings.tts_model_path,
            voice=settings.tts_voice,
            speed=settings.tts_speed,
        ),
        vad=VADConfig(
            pause_threshold_ms=settings.vad_pause_threshold_ms,
            min_speech_duration_ms=settings.vad_min_speech_duration_ms,
            speech_threshold=settings.vad_speech_threshold,
            min_silence_duration_ms=settings.vad_min_silence_duration_ms,
        ),
        can_interrupt=True,
        server_host=settings.server_host,
        server_port=settings.server_port,
    )

    # 初始化工具註冊表（自動掃描 BaseTool 子類別）
    tool_registry = ToolRegistry()
    tool_registry.auto_discover()

    # 009: 建立 FlowRegistry 並註冊所有流程執行器
    # 注意：ToolCallingExecutor 的 system_prompt_provider 使用 late-binding，
    # 在 pipeline 建立後會自動引用 pipeline._get_current_system_prompt
    _pipeline_ref: list[VoicePipeline | None] = [None]

    flow_registry = FlowRegistry()
    flow_registry.register(
        ToolCallingExecutor(
            llm_client=llm_client,
            tool_registry=tool_registry,
            system_prompt_provider=lambda: (
                _pipeline_ref[0]._get_current_system_prompt()
                if _pipeline_ref[0] is not None
                else VoicePipeline.DEFAULT_SYSTEM_PROMPT
            ),
        )
    )
    flow_registry.register(FlowExecutor(llm_client, tool_registry))
    flow_registry.register(MultiAgentExecutor(llm_client, tool_registry))

    # ----------
    # 初始化角色註冊表與預設角色
    role_registry = RoleRegistry()
    role_registry.register(AssistantRole())
    role_registry.register(CoachRole())
    role_registry.register(InterviewerRole())

    # 建立角色選項：ID -> 顯示名稱（含 emoji）
    role_display_map = {
        "assistant": "🤖 助理",
        "coach": "💪 教練",
        "interviewer": "👔 面試官",
    }
    available_roles = {
        role.id: role_display_map.get(role.id, role.name)
        for role in role_registry.list_roles()
    }
    default_role_id = next(iter(available_roles)) if available_roles else ""

    # 初始化意圖辨識器
    from voice_assistant.intent.recognizer import IntentRecognizer

    intent_recognizer = IntentRecognizer(llm_client)

    # 初始化語音管線（使用 009 FlowRegistry 統一流程介面）
    pipeline = VoicePipeline(
        config=config,
        llm_client=llm_client,
        tool_registry=tool_registry,
        intent_recognizer=intent_recognizer,
        role_registry=role_registry,
        flow_registry=flow_registry,
    )
    # 設定 late-binding 參考，讓 ToolCallingExecutor 使用角色感知的 system_prompt
    _pipeline_ref[0] = pipeline
    # 啟動階段先設置預設角色
    if default_role_id:
        pipeline.switch_role(role_registry.get(default_role_id))

    # 回調 glue：角色切換
    def on_role_change(role_id: str, current_chatbot: list, current_status: str):
        # 防禦式：確保 current_chatbot 和 current_status 有預設值
        current_chatbot = current_chatbot or []
        current_status = current_status or "🟢 待命"
        role = role_registry.get(role_id)
        pipeline.switch_role(role)
        welcome = (
            role.get_welcome_message() if hasattr(role, "get_welcome_message") else None
        )
        if welcome:
            # 在歡迎語前加入視覺分隔，避免與上一句緊鄰
            updated_chatbot = current_chatbot + [
                {"role": "assistant", "content": f"---\n\n{welcome}"}
            ]
            updated_status = f"🟢 {role.name}已啟用"
            # 注意：歡迎語只在對話框顯示，不播放 TTS（避免與 WebRTC 串流衝突）
            return updated_chatbot, updated_status
        return current_chatbot, current_status

    # 建立額外輸出元件（Chatbot 和狀態）
    chatbot, status_display = create_additional_outputs()

    # 建立流程視覺化元件
    flow_viz = create_flow_visualization()

    # ---- [AI assistant injects welcome on initial load] ----
    initial_history = []
    initial_status = "🟢 待命"
    default_role = role_registry.get(default_role_id) if default_role_id else None

    if default_role and hasattr(default_role, "get_welcome_message"):
        welcome_msg = default_role.get_welcome_message()
        if welcome_msg:
            initial_history = [{"role": "assistant", "content": welcome_msg}]
            initial_status = f"🟢 {default_role.name}已啟用"
            # 注意：首次載入時不播放 TTS（WebRTC 連線尚未建立）

    chatbot.value = initial_history
    status_display.value = initial_status

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
        additional_outputs=[chatbot, status_display, flow_viz],
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
        current_flow_viz: str,
    ):
        """處理上傳的音訊檔案（generator 模式，即時串流更新 UI）。

        使用 yield 逐步回傳流程圖更新，讓 Gradio 即時反映節點執行狀態。

        Args:
            audio: (sample_rate, audio_array) 或 None
            current_chatbot: 目前的對話記錄
            current_status: 目前的狀態文字
            current_flow_viz: 目前的流程視覺化 HTML

        Yields:
            (updated_chatbot, updated_status, audio_input_value, updated_flow_viz)
        """
        if audio is None:
            yield current_chatbot, current_status, None, current_flow_viz
            return

        # 轉換音訊格式
        processed_audio = audio_input_handler(audio)
        if processed_audio is None:
            yield current_chatbot, current_status, None, current_flow_viz
            return

        logger.info("[Handler] 開始處理上傳的音訊檔案")

        # 使用 pipeline 處理音訊（generator 模式）
        # 每次收到 AdditionalOutputs 即 yield 更新給 UI
        final_chatbot = current_chatbot
        final_status = current_status
        final_flow_viz = current_flow_viz

        try:
            for output in pipeline.process_audio_with_outputs(processed_audio):
                # 檢查是否為 AdditionalOutputs
                from fastrtc import AdditionalOutputs

                if isinstance(output, AdditionalOutputs):
                    # AdditionalOutputs 物件（3 個引數：history, status, flow_viz）
                    final_chatbot = output.args[0]
                    final_status = output.args[1]
                    final_flow_viz = output.args[2]
                    # 即時串流更新給 Gradio UI
                    yield final_chatbot, final_status, None, final_flow_viz
                # 音訊輸出在這裡忽略（不播放 TTS）
        except Exception as e:
            logger.error(f"[Handler] 處理上傳音訊失敗: {e}", exc_info=True)
            final_status = f"❌ 處理失敗: {e}"

        logger.info("[Handler] 上傳音訊處理完成")
        # 最終結果（確保最後一次更新到達 UI）
        yield final_chatbot, final_status, None, final_flow_viz

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
                # 角色切換下拉選單元件
                # choices 格式：[(顯示名稱, role_id), ...]
                dropdown = gr.Dropdown(
                    choices=[
                        (display_name, role_id)
                        for role_id, display_name in available_roles.items()
                    ],
                    value=default_role_id,
                    label="選擇角色",
                    interactive=True,
                )
                # 正確綁定 chatbot/state 做到 UI 更新
                dropdown.change(
                    fn=on_role_change,
                    inputs=[dropdown, chatbot, status_display],
                    outputs=[chatbot, status_display],
                )

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
                        "上傳預錄的音訊檔案來測試對話功能，適用於無法使用麥克風的環境。"
                    )
                    audio_input = gr.Audio(
                        label="上傳音訊檔案",
                        type="numpy",
                        sources=["upload"],
                    )
                    submit_btn = gr.Button("🎯 處理音訊", variant="primary")

                # 流程視覺化面板
                with gr.Accordion("📊 流程圖", open=False):
                    flow_viz.render()

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
            inputs=[chatbot, status_display, flow_viz],
            outputs=[chatbot, status_display, flow_viz],
            concurrency_limit=stream.concurrency_limit,
        )

        # 綁定音訊上傳處理事件
        submit_btn.click(
            fn=process_uploaded_audio,
            inputs=[audio_input, chatbot, status_display, flow_viz],
            outputs=[chatbot, status_display, audio_input, flow_viz],
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
