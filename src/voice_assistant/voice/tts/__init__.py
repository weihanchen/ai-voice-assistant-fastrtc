"""文字轉語音（TTS）模組"""

from voice_assistant.voice.tts.base import TTSModel
from voice_assistant.voice.tts.kokoro import KokoroTTS

__all__ = ["TTSModel", "KokoroTTS"]
