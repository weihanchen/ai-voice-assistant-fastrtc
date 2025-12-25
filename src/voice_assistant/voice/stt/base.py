"""STT Protocol 定義

定義 FastRTC STTModel Protocol，所有 STT 實作必須符合此介面。
"""

from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class STTModel(Protocol):
    """FastRTC STTModel Protocol

    所有 STT 實作必須符合此介面，以便與 FastRTC ReplyOnPause 整合。
    """

    def stt(self, audio: tuple[int, NDArray[np.int16 | np.float32]]) -> str:
        """將音訊轉換為文字

        Args:
            audio: Tuple of (sample_rate, audio_array)
                - sample_rate: 取樣率 (Hz)
                - audio_array: 音訊資料，dtype 為 int16 或 float32

        Returns:
            辨識出的文字內容
        """
        ...
