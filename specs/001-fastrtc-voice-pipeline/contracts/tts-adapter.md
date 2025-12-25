# Contract: TTS Adapter

**Date**: 2025-12-25
**Feature**: 001-fastrtc-voice-pipeline

## Overview

文字轉語音（Text-to-Speech）轉接器契約，定義 TTS 模組的介面規範。

---

## Protocol Definition

```python
from typing import Protocol, Iterator, AsyncIterator, runtime_checkable
import numpy as np
from numpy.typing import NDArray

@runtime_checkable
class TTSModel(Protocol):
    """
    TTS Model Protocol

    所有 TTS 實作必須符合此介面。
    """

    def tts(self, text: str) -> tuple[int, NDArray[np.float32]]:
        """
        同步生成語音

        Args:
            text: 要轉換的文字

        Returns:
            Tuple of (sample_rate, audio_array)
        """
        ...

    def stream_tts_sync(self, text: str) -> Iterator[tuple[int, NDArray[np.float32]]]:
        """
        同步串流生成語音

        Args:
            text: 要轉換的文字

        Yields:
            Tuple of (sample_rate, audio_chunk)
        """
        ...
```

---

## KokoroTTS Implementation

```python
from kokoro_onnx import Kokoro
import numpy as np
from numpy.typing import NDArray
from typing import Iterator, Optional
from pathlib import Path

class KokoroTTS:
    """
    Kokoro TTS 中文實作

    使用 Kokoro-82M-v1.1-zh 模型進行中文語音合成。
    """

    # 預設中文音色
    DEFAULT_VOICE = "zf_001"

    def __init__(
        self,
        model_path: str | Path,
        voices_path: str | Path,
        voice: Optional[str] = None,
        speed: float = 1.0,
        language: str = "zh"
    ):
        """
        初始化 Kokoro TTS

        Args:
            model_path: ONNX 模型檔案路徑
            voices_path: 音色檔案路徑
            voice: 音色 ID (zf_* 女聲, zm_* 男聲)
            speed: 語速倍率 (0.5-2.0)
            language: 語言代碼
        """
        self.kokoro = Kokoro(str(model_path), str(voices_path))
        self.voice = voice or self.DEFAULT_VOICE
        self.speed = speed
        self.language = language

    def tts(self, text: str) -> tuple[int, NDArray[np.float32]]:
        """
        同步生成語音

        Args:
            text: 中文文字

        Returns:
            (sample_rate, audio_array) tuple
        """
        if not text.strip():
            # 空文字回傳靜音
            return (24000, np.zeros(0, dtype=np.float32))

        samples, sample_rate = self.kokoro.create(
            text,
            voice=self.voice,
            speed=self.speed,
            lang=self.language
        )
        return (sample_rate, samples.astype(np.float32))

    def stream_tts_sync(self, text: str) -> Iterator[tuple[int, NDArray[np.float32]]]:
        """
        同步串流生成語音

        分段生成音訊，適合即時播放。

        Args:
            text: 中文文字

        Yields:
            (sample_rate, audio_chunk) tuples
        """
        if not text.strip():
            return

        # 按標點符號分段
        import re
        sentences = re.split(r'([。！？，；：])', text)

        buffer = ""
        for part in sentences:
            buffer += part
            # 遇到結束標點就生成音訊
            if part in "。！？":
                if buffer.strip():
                    samples, sample_rate = self.kokoro.create(
                        buffer.strip(),
                        voice=self.voice,
                        speed=self.speed,
                        lang=self.language
                    )
                    yield (sample_rate, samples.astype(np.float32))
                buffer = ""

        # 處理剩餘文字
        if buffer.strip():
            samples, sample_rate = self.kokoro.create(
                buffer.strip(),
                voice=self.voice,
                speed=self.speed,
                lang=self.language
            )
            yield (sample_rate, samples.astype(np.float32))

    def set_voice(self, voice: str) -> None:
        """設定音色"""
        self.voice = voice

    def set_speed(self, speed: float) -> None:
        """設定語速"""
        if not 0.5 <= speed <= 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0")
        self.speed = speed
```

---

## Usage Example

```python
from voice_assistant.voice.tts import KokoroTTS

# 初始化 TTS
tts = KokoroTTS(
    model_path="models/kokoro-v1.0.int8.onnx",
    voices_path="models/voices-v1.0.bin",
    voice="zf_001"  # 中文女聲
)

# 同步生成
sample_rate, audio = tts.tts("你好，我是語音助理。")

# 串流生成（適合長文字）
for sample_rate, chunk in tts.stream_tts_sync("這是一段較長的文字。會分段生成。"):
    # 播放或傳送 chunk
    play_audio(sample_rate, chunk)
```

---

## Voice Options

### 中文女聲 (zf_*)

| Voice ID | 風格 |
|----------|------|
| `zf_001` | 標準女聲（預設） |
| `zf_002` | 溫柔女聲 |
| `zf_003` | 活潑女聲 |
| ... | 共 55 種 |

### 中文男聲 (zm_*)

| Voice ID | 風格 |
|----------|------|
| `zm_001` | 標準男聲 |
| `zm_002` | 沉穩男聲 |
| ... | 共 45 種 |

---

## Error Handling

| 錯誤情況 | 處理方式 |
|----------|----------|
| 空文字 | 回傳空音訊陣列 |
| 模型載入失敗 | 拋出 `RuntimeError` |
| 無效音色 ID | 拋出 `ValueError` |
| 記憶體不足 | 分段處理長文字 |

---

## Configuration

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `voice` | `"zf_001"` | 音色 ID |
| `speed` | `1.0` | 語速倍率 |
| `language` | `"zh"` | 語言代碼 |

---

## Model Files

```bash
# 下載模型檔案
mkdir -p models
wget -O models/kokoro-v1.0.int8.onnx \
    https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
wget -O models/voices-v1.0.bin \
    https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

---

## Testing

```python
import pytest
import numpy as np
from voice_assistant.voice.tts import KokoroTTS

class TestKokoroTTS:

    @pytest.fixture
    def tts(self, tmp_path):
        # 使用 mock 或實際模型
        return KokoroTTS(
            model_path="models/kokoro-v1.0.int8.onnx",
            voices_path="models/voices-v1.0.bin"
        )

    def test_implements_protocol(self, tts):
        """驗證實作 TTSModel Protocol"""
        assert hasattr(tts, 'tts')
        assert hasattr(tts, 'stream_tts_sync')

    def test_tts_returns_audio(self, tts):
        """驗證回傳音訊格式"""
        sample_rate, audio = tts.tts("測試")
        assert isinstance(sample_rate, int)
        assert sample_rate == 24000
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32

    def test_tts_empty_text(self, tts):
        """處理空文字"""
        sample_rate, audio = tts.tts("")
        assert len(audio) == 0

    def test_stream_tts_yields_chunks(self, tts):
        """串流生成多個 chunks"""
        chunks = list(tts.stream_tts_sync("第一句。第二句。第三句。"))
        assert len(chunks) == 3

    def test_set_speed_validation(self, tts):
        """語速範圍驗證"""
        with pytest.raises(ValueError):
            tts.set_speed(3.0)
```
