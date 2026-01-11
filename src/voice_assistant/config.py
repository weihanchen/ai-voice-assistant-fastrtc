"""Configuration management for voice assistant."""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings


class FlowMode(str, Enum):
    """流程處理模式。

    - TOOLS: 純 Tool 呼叫模式
    - LANGGRAPH: LangGraph 流程模式 (006 架構)
    - MULTI_AGENT: 多代理協作模式 (007 架構)
    """

    TOOLS = "tools"
    LANGGRAPH = "langgraph"
    MULTI_AGENT = "multi_agent"


class Settings(BaseSettings):
    """應用程式配置。"""

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # STT (Speech-to-Text)
    whisper_model_size: str = "small"
    whisper_model_path: str = "models/whisper"  # 模型快取目錄
    whisper_device: str = "cpu"
    whisper_language: str = "zh"

    # TTS (Text-to-Speech)
    tts_model_path: str = "models"  # HuggingFace 快取目錄
    tts_voice: str = "zf_001"
    tts_speed: float = 1.0

    # VAD (Voice Activity Detection)
    vad_pause_threshold_ms: int = 500
    vad_min_speech_duration_ms: int = 250
    vad_speech_threshold: float = 0.5
    vad_min_silence_duration_ms: int = 500  # Whisper VAD 靜音閾值

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 7860

    # Flow Mode
    flow_mode: FlowMode = FlowMode.MULTI_AGENT

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # 忽略未定義的環境變數（如 HF_HUB_OFFLINE）
    }


@lru_cache
def get_settings() -> Settings:
    """取得應用程式設定（快取）"""
    return Settings()
