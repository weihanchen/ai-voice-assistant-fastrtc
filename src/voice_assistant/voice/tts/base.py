"""TTS Protocol 定義

定義 TTSModel Protocol，所有 TTS 實作必須符合此介面。
"""

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class TTSModel(Protocol):
    """TTS Model Protocol

    所有 TTS 實作必須符合此介面。
    """

    def tts(self, text: str) -> tuple[int, NDArray[np.float32]]:
        """同步生成語音

        Args:
            text: 要轉換的文字

        Returns:
            Tuple of (sample_rate, audio_array)
        """
        ...

    def stream_tts_sync(self, text: str) -> Iterator[tuple[int, NDArray[np.float32]]]:
        """同步串流生成語音

        Args:
            text: 要轉換的文字

        Yields:
            Tuple of (sample_rate, audio_chunk)
        """
        ...
