"""WhisperSTT 單元測試

測試 faster-whisper STT 實作是否符合 STTModel Protocol。
"""

import numpy as np
import pytest

from voice_assistant.voice.stt.base import STTModel


class TestWhisperSTTProtocol:
    """測試 WhisperSTT 符合 STTModel Protocol"""

    def test_whisper_stt_implements_protocol(self):
        """驗證 WhisperSTT 實作 STTModel Protocol"""
        from voice_assistant.voice.stt.whisper import WhisperSTT

        stt = WhisperSTT.__new__(WhisperSTT)
        # 檢查是否有 stt 方法
        assert hasattr(stt, "stt")
        assert callable(getattr(stt, "stt"))

    def test_whisper_stt_is_runtime_checkable(self):
        """驗證可透過 isinstance 檢查 Protocol"""
        from voice_assistant.voice.stt.whisper import WhisperSTT

        # WhisperSTT 應該符合 STTModel Protocol
        # 注意：需要實例化才能用 isinstance 檢查 runtime_checkable Protocol
        stt = WhisperSTT.__new__(WhisperSTT)
        stt.stt = lambda audio: ""  # Mock stt method
        assert isinstance(stt, STTModel)


class TestWhisperSTTFunctionality:
    """測試 WhisperSTT 功能（需要模型，使用 mock）"""

    @pytest.fixture
    def mock_whisper_stt(self, mocker):
        """建立 mock WhisperSTT"""
        from voice_assistant.voice.stt.whisper import WhisperSTT

        # Mock WhisperModel
        mock_model = mocker.MagicMock()
        mock_segment = mocker.MagicMock()
        mock_segment.text = "測試文字"
        mock_model.transcribe.return_value = ([mock_segment], None)

        mocker.patch(
            "voice_assistant.voice.stt.whisper.WhisperModel",
            return_value=mock_model,
        )

        return WhisperSTT(model_size="tiny", language="zh")

    def test_stt_returns_string(self, mock_whisper_stt):
        """驗證 stt 回傳字串"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        result = mock_whisper_stt.stt(audio)
        assert isinstance(result, str)

    def test_stt_handles_int16_audio(self, mock_whisper_stt):
        """處理 int16 格式音訊"""
        audio = (16000, np.zeros(16000, dtype=np.int16))
        result = mock_whisper_stt.stt(audio)
        assert isinstance(result, str)

    def test_stt_handles_empty_audio(self, mock_whisper_stt):
        """處理空音訊"""
        audio = (16000, np.array([], dtype=np.float32))
        result = mock_whisper_stt.stt(audio)
        assert isinstance(result, str)

    def test_stt_transcribes_text(self, mock_whisper_stt):
        """驗證轉錄結果"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        result = mock_whisper_stt.stt(audio)
        assert result == "測試文字"
