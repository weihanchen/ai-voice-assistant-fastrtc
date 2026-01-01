"""FastRTC ReplyOnPause 處理器整合

建立 FastRTC 語音串流，配置 ReplyOnPause 機制。
"""

from fastrtc import AlgoOptions, ReplyOnPause, SileroVadOptions, Stream

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
    create_additional_outputs,
)


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

    # 建立 FastRTC Stream（使用 process_audio_with_outputs 以支援 AdditionalOutputs）
    # additional_outputs 會在 Gradio UI 中顯示 Chatbot 和狀態
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
        additional_outputs=create_additional_outputs(),
        additional_outputs_handler=additional_outputs_handler,
    )

    return stream
