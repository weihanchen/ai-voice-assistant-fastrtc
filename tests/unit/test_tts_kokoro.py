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

        # Mock KPipeline（原生 kokoro 使用的類別）
        mock_pipeline = mocker.MagicMock()
        # pipeline() 回傳 generator of (graphemes, phonemes, audio)
        mock_audio = np.zeros(24000, dtype=np.float32)
        mock_pipeline.return_value = iter([("g", "p", mock_audio)])

        mocker.patch(
            "voice_assistant.voice.tts.kokoro.KPipeline",
            return_value=mock_pipeline,
        )

        tts = KokoroTTS(voice="zf_001")
        tts.pipeline = mock_pipeline
        return tts

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

    def test_stream_tts_yields_chunks(self, mock_kokoro_tts):
        """串流生成多個 chunks"""
        # 重設 mock 以回傳多個 chunk
        mock_audio = np.zeros(12000, dtype=np.float32)
        mock_kokoro_tts.pipeline.return_value = iter([
            ("g1", "p1", mock_audio),
            ("g2", "p2", mock_audio),
        ])

        chunks = list(mock_kokoro_tts.stream_tts_sync("第一句。第二句。"))
        # 應該有 chunks
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
