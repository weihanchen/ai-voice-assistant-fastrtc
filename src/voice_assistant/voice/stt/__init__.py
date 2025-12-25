"""語音轉文字（STT）模組"""

from voice_assistant.voice.stt.base import STTModel
from voice_assistant.voice.stt.whisper import WhisperSTT

__all__ = ["STTModel", "WhisperSTT"]
