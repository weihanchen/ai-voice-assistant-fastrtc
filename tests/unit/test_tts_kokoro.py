"""KokoroTTS 單元測試

測試 Kokoro TTS 實作是否符合 TTSModel Protocol。
"""

import numpy as np
import pytest

from voice_assistant.voice.tts.base import TTSModel


class TestKokoroTTSProtocol:
    """測試 KokoroTTS 符合 TTSModel Protocol"""

    def test_kokoro_tts_implements_protocol(self):
        """驗證 KokoroTTS 實作 TTSModel Protocol"""
        from voice_assistant.voice.tts.kokoro import KokoroTTS

        tts = KokoroTTS.__new__(KokoroTTS)
        # 檢查是否有必要方法
        assert hasattr(tts, "tts")
        assert hasattr(tts, "stream_tts_sync")
        assert callable(getattr(tts, "tts"))
        assert callable(getattr(tts, "stream_tts_sync"))

    def test_kokoro_tts_is_runtime_checkable(self):
        """驗證可透過 isinstance 檢查 Protocol"""
        from voice_assistant.voice.tts.kokoro import KokoroTTS

        tts = KokoroTTS.__new__(KokoroTTS)
        tts.tts = lambda text: (24000, np.zeros(0, dtype=np.float32))
        tts.stream_tts_sync = lambda text: iter([])
        assert isinstance(tts, TTSModel)


class TestKokoroTTSFunctionality:
    """測試 KokoroTTS 功能（需要模型，使用 mock）"""

    @pytest.fixture
    def mock_kokoro_tts(self, mocker):
        """建立 mock KokoroTTS"""
        from voice_assistant.voice.tts.kokoro import KokoroTTS

        # Mock Kokoro
        mock_kokoro = mocker.MagicMock()
        mock_kokoro.create.return_value = (
            np.zeros(24000, dtype=np.float32),
            24000,
        )

        mocker.patch(
            "voice_assistant.voice.tts.kokoro.Kokoro",
            return_value=mock_kokoro,
        )

        return KokoroTTS(
            model_path="models/kokoro-v1.0.int8.onnx",
            voices_path="models/voices-v1.0.bin",
        )

    def test_tts_returns_audio_tuple(self, mock_kokoro_tts):
        """驗證 tts 回傳 (sample_rate, audio_array) tuple"""
        sample_rate, audio = mock_kokoro_tts.tts("測試")
        assert isinstance(sample_rate, int)
        assert sample_rate == 24000
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32

    def test_tts_empty_text(self, mock_kokoro_tts):
        """處理空文字"""
        sample_rate, audio = mock_kokoro_tts.tts("")
        assert sample_rate == 24000
        assert len(audio) == 0

    def test_stream_tts_yields_chunks(self, mock_kokoro_tts, mocker):
        """串流生成多個 chunks"""
        # Mock create for streaming
        mock_kokoro_tts.kokoro.create.return_value = (
            np.zeros(24000, dtype=np.float32),
            24000,
        )

        chunks = list(mock_kokoro_tts.stream_tts_sync("第一句。第二句。"))
        # 應該有多個 chunks（依句號分段）
        assert len(chunks) >= 1
        for sample_rate, chunk in chunks:
            assert isinstance(sample_rate, int)
            assert isinstance(chunk, np.ndarray)

    def test_set_speed_validation(self, mock_kokoro_tts):
        """語速範圍驗證"""
        with pytest.raises(ValueError):
            mock_kokoro_tts.set_speed(3.0)

    def test_set_speed_valid(self, mock_kokoro_tts):
        """設定有效語速"""
        mock_kokoro_tts.set_speed(1.5)
        assert mock_kokoro_tts.speed == 1.5
