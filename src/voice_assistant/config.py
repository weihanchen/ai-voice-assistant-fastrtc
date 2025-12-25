"""Configuration management for voice assistant."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用程式配置。"""

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # STT (Speech-to-Text)
    whisper_model_size: str = "tiny"
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

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 7860

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """取得應用程式設定（快取）"""
    return Settings()
