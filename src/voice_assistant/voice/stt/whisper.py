"""faster-whisper STT 實作

實作 FastRTC STTModel Protocol，使用 faster-whisper 進行中文語音辨識。
"""

import numpy as np
from faster_whisper import WhisperModel
from numpy.typing import NDArray
from scipy import signal


class WhisperSTT:
    """faster-whisper 實作 STTModel Protocol

    使用 faster-whisper 進行中文語音辨識。
    """

    def __init__(
        self,
        model_size: str = "tiny",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "zh",
        beam_size: int = 5,
        vad_filter: bool = True,
        min_silence_duration_ms: int = 500,
    ):
        """初始化 Whisper 模型

        Args:
            model_size: 模型大小 (tiny/base/small/medium/large)
            device: 運算裝置 (cpu/cuda)
            compute_type: 計算精度 (int8/float16/float32)
            language: 目標語言代碼
            beam_size: Beam search 大小（較大值提升準確度但較慢）
            vad_filter: 是否啟用 VAD 過濾靜音
            min_silence_duration_ms: VAD 靜音閾值（毫秒）
        """
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )
        self.language = language
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self.min_silence_duration_ms = min_silence_duration_ms

    def stt(self, audio: tuple[int, NDArray[np.int16 | np.float32]]) -> str:
        """將音訊轉換為文字

        Args:
            audio: (sample_rate, audio_array) tuple

        Returns:
            辨識出的中文文字
        """
        sample_rate, audio_array = audio

        # 處理空音訊
        if len(audio_array) == 0:
            return ""

        # 確保音訊為 1D (FastRTC 可能傳入多維陣列)
        if audio_array.ndim > 1:
            # 處理多維陣列：取第一個聲道避免 interleaving 破壞音訊
            # shape (samples, channels) -> 取 [:, 0]
            # shape (channels, samples) -> 取 [0, :]
            if audio_array.shape[0] > audio_array.shape[1]:
                # (samples, channels) 格式
                audio_array = audio_array[:, 0]
            else:
                # (channels, samples) 格式
                audio_array = audio_array[0, :]

        # 正規化為 float32
        if audio_array.dtype == np.int16:
            audio_array = audio_array.astype(np.float32) / 32768.0
        elif audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)

        # Whisper 預期 16kHz 輸入，重採樣
        target_sr = 16000
        if sample_rate != target_sr:
            num_samples = int(len(audio_array) * target_sr / sample_rate)
            audio_array = signal.resample(audio_array, num_samples).astype(np.float32)

        # 執行辨識（條件性建構 kwargs 避免傳遞 None）
        transcribe_kwargs = {
            "language": self.language,
            "beam_size": self.beam_size,
            "vad_filter": self.vad_filter,
        }
        if self.vad_filter:
            transcribe_kwargs["vad_parameters"] = {
                "min_silence_duration_ms": self.min_silence_duration_ms
            }
        segments, _info = self.model.transcribe(audio_array, **transcribe_kwargs)

        # 合併所有片段
        return "".join(segment.text for segment in segments).strip()
