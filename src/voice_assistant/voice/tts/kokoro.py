"""Kokoro TTS 中文實作

使用原生 kokoro + misaki[zh] 進行中文語音合成。
支援 Kokoro-82M-v1.1-zh 中文模型。

模型會自動從 HuggingFace 下載並快取。
可透過以下方式控制模型位置：
1. 設定環境變數 HF_HOME 指定快取目錄（例如 HF_HOME=./models）
2. 預先下載模型後，設定 HF_HUB_OFFLINE=1 離線使用

預先下載模型：
    uv run python scripts/download_models.py
"""

import os
import re
from collections.abc import Iterator
from pathlib import Path

import numpy as np
from kokoro import KPipeline
from numpy.typing import NDArray


class KokoroTTS:
    """Kokoro TTS 中文實作

    使用 Kokoro-82M-v1.1-zh 模型進行中文語音合成。
    """

    # 預設中文音色 (可用: zf_001~zf_085 女聲, zm_010~zm_100 男聲)
    # 完整列表: https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh/tree/main/voices
    DEFAULT_VOICE = "zf_001"

    # 中文模型 repo
    CHINESE_REPO = "hexgrad/Kokoro-82M-v1.1-zh"

    def __init__(
        self,
        model_path: str | None = None,  # HuggingFace 快取目錄
        voices_path: str | None = None,  # 保留相容性
        voice: str | None = None,
        speed: float = 1.0,
        language: str = "z",  # Kokoro 使用 'z' 代表中文
    ):
        """初始化 Kokoro TTS

        Args:
            model_path: HuggingFace 快取目錄（會設定 HF_HOME 環境變數）
                        例如: "models" 會將模型快取到 ./models 目錄
                        若不指定則使用預設 HuggingFace 快取目錄
            voices_path: (已棄用) 保留相容性
            voice: 音色 ID (zf_* 女聲, zm_* 男聲)
            speed: 語速倍率 (0.5-2.0)
            language: 語言代碼 ('z' = 中文)
        """
        # 設定模型快取目錄
        if model_path:
            cache_dir = Path(model_path).resolve()
            cache_dir.mkdir(parents=True, exist_ok=True)
            os.environ["HF_HOME"] = str(cache_dir)

        # 使用 KPipeline 載入中文模型
        self.pipeline = KPipeline(
            lang_code=language,
            repo_id=self.CHINESE_REPO,
        )
        self.voice = voice or self.DEFAULT_VOICE
        self.speed = speed
        self.sample_rate = 24000  # Kokoro 預設輸出 24kHz

    def tts(self, text: str) -> tuple[int, NDArray[np.float32]]:
        """同步生成語音

        Args:
            text: 中文文字

        Returns:
            (sample_rate, audio_array) tuple
        """
        if not text.strip():
            # 空文字回傳靜音
            return (self.sample_rate, np.zeros(0, dtype=np.float32))

        # 使用 pipeline 生成音訊
        audio_chunks = []
        generator = self.pipeline(
            text,
            voice=self.voice,
            speed=self.speed,
        )

        for _gs, _ps, audio in generator:
            # Kokoro 回傳 PyTorch Tensor，需轉換為 numpy
            if hasattr(audio, "numpy"):
                audio = audio.numpy()
            audio_chunks.append(audio)

        if not audio_chunks:
            return (self.sample_rate, np.zeros(0, dtype=np.float32))

        # 合併所有音訊片段
        combined = np.concatenate(audio_chunks)
        return (self.sample_rate, combined.astype(np.float32))

    def stream_tts_sync(
        self, text: str
    ) -> Iterator[tuple[int, NDArray[np.float32]]]:
        """同步串流生成語音

        分段生成音訊，適合即時播放。

        Args:
            text: 中文文字

        Yields:
            (sample_rate, audio_chunk) tuples
        """
        if not text.strip():
            return

        # 按標點符號分段
        sentences = re.split(r"([。！？，；：])", text)

        buffer = ""
        for part in sentences:
            buffer += part
            # 遇到結束標點就生成音訊
            if part in "。！？":
                if buffer.strip():
                    generator = self.pipeline(
                        buffer.strip(),
                        voice=self.voice,
                        speed=self.speed,
                    )
                    for _gs, _ps, audio in generator:
                        # Kokoro 回傳 PyTorch Tensor，需轉換為 numpy
                        if hasattr(audio, "numpy"):
                            audio = audio.numpy()
                        yield (self.sample_rate, audio.astype(np.float32))
                buffer = ""

        # 處理剩餘文字
        if buffer.strip():
            generator = self.pipeline(
                buffer.strip(),
                voice=self.voice,
                speed=self.speed,
            )
            for _gs, _ps, audio in generator:
                # Kokoro 回傳 PyTorch Tensor，需轉換為 numpy
                if hasattr(audio, "numpy"):
                    audio = audio.numpy()
                yield (self.sample_rate, audio.astype(np.float32))

    def set_voice(self, voice: str) -> None:
        """設定音色"""
        self.voice = voice

    def set_speed(self, speed: float) -> None:
        """設定語速"""
        if not 0.5 <= speed <= 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0")
        self.speed = speed
