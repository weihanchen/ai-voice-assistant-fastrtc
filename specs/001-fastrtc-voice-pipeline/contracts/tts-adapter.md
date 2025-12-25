# Contract: TTS Adapter

**Date**: 2025-12-25
**Feature**: 001-fastrtc-voice-pipeline
**Updated**: 2025-12-25 (使用原生 kokoro + misaki[zh])

## Overview

文字轉語音（Text-to-Speech）轉接器契約，定義 TTS 模組的介面規範。

> **實作更新**: 原先規劃使用 `kokoro-onnx`，但實測發現其使用 espeak 後端不支援中文。
> 最終採用原生 `kokoro` 套件搭配 `misaki[zh]` 中文 G2P 模組。

---

## Protocol Definition

```python
from typing import Protocol, Iterator, runtime_checkable
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
from kokoro import KPipeline
import numpy as np
from numpy.typing import NDArray
from typing import Iterator
from pathlib import Path
import os
import re

class KokoroTTS:
    """
    Kokoro TTS 中文實作

    使用 Kokoro-82M-v1.1-zh 模型進行中文語音合成。
    透過原生 kokoro + misaki[zh] 套件實作。
    """

    # 預設中文音色
    DEFAULT_VOICE = "zf_001"

    # 中文模型 repo
    CHINESE_REPO = "hexgrad/Kokoro-82M-v1.1-zh"

    def __init__(
        self,
        model_path: str | None = None,
        voice: str | None = None,
        speed: float = 1.0,
        language: str = "z"  # Kokoro 使用 'z' 代表中文
    ):
        """
        初始化 Kokoro TTS

        Args:
            model_path: HuggingFace 快取目錄（設定 HF_HOME）
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
        """
        同步生成語音

        Args:
            text: 中文文字

        Returns:
            (sample_rate, audio_array) tuple
        """
        if not text.strip():
            return (self.sample_rate, np.zeros(0, dtype=np.float32))

        audio_chunks = []
        generator = self.pipeline(text, voice=self.voice, speed=self.speed)

        for _gs, _ps, audio in generator:
            if hasattr(audio, "numpy"):
                audio = audio.numpy()
            audio_chunks.append(audio)

        if not audio_chunks:
            return (self.sample_rate, np.zeros(0, dtype=np.float32))

        combined = np.concatenate(audio_chunks)
        return (self.sample_rate, combined.astype(np.float32))

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
        sentences = re.split(r'([。！？，；：])', text)

        buffer = ""
        for part in sentences:
            buffer += part
            if part in "。！？":
                if buffer.strip():
                    generator = self.pipeline(
                        buffer.strip(),
                        voice=self.voice,
                        speed=self.speed,
                    )
                    for _gs, _ps, audio in generator:
                        if hasattr(audio, "numpy"):
                            audio = audio.numpy()
                        yield (self.sample_rate, audio.astype(np.float32))
                buffer = ""

        if buffer.strip():
            generator = self.pipeline(
                buffer.strip(),
                voice=self.voice,
                speed=self.speed,
            )
            for _gs, _ps, audio in generator:
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
```

---

## Usage Example

```python
from voice_assistant.voice.tts import KokoroTTS

# 初始化 TTS（模型自動從 HuggingFace 下載）
tts = KokoroTTS(
    model_path="models",  # HF_HOME 快取目錄
    voice="zf_001"        # 中文女聲
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

| Voice ID | 說明 |
|----------|------|
| `zf_001` ~ `zf_085` | 85 種中文女聲 |

### 中文男聲 (zm_*)

| Voice ID | 說明 |
|----------|------|
| `zm_010` ~ `zm_100` | 中文男聲 |

完整音色列表：https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh/tree/main/voices

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
| `model_path` | `None` | HuggingFace 快取目錄 |
| `voice` | `"zf_001"` | 音色 ID |
| `speed` | `1.0` | 語速倍率 |
| `language` | `"z"` | 語言代碼（中文） |

---

## Model Setup

模型會自動從 HuggingFace 下載並快取。

### 預先下載模型

```bash
# 下載模型
uv run python scripts/download_models.py

# 或直接使用 huggingface-cli
huggingface-cli download hexgrad/Kokoro-82M-v1.1-zh --local-dir models/hub
```

### 離線模式

```bash
export HF_HUB_OFFLINE=1
```

---

## Dependencies

```toml
# pyproject.toml
[project.dependencies]
kokoro = ">=0.8.2"
misaki = { version = ">=0.8.2", extras = ["zh"] }
```

---

## Testing

```python
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

class TestKokoroTTS:

    @pytest.fixture
    def mock_tts(self, mocker):
        """建立 mock TTS 實例"""
        mock_pipeline = MagicMock()
        mock_audio = np.zeros(24000, dtype=np.float32)
        mock_pipeline.return_value = iter([("g", "p", mock_audio)])

        mocker.patch(
            "voice_assistant.voice.tts.kokoro.KPipeline",
            return_value=mock_pipeline
        )

        from voice_assistant.voice.tts.kokoro import KokoroTTS
        return KokoroTTS()

    def test_implements_protocol(self, mock_tts):
        """驗證實作 TTSModel Protocol"""
        assert hasattr(mock_tts, 'tts')
        assert hasattr(mock_tts, 'stream_tts_sync')

    def test_tts_returns_audio(self, mock_tts):
        """驗證回傳音訊格式"""
        sample_rate, audio = mock_tts.tts("測試")
        assert isinstance(sample_rate, int)
        assert sample_rate == 24000
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32

    def test_tts_empty_text(self, mock_tts):
        """處理空文字"""
        sample_rate, audio = mock_tts.tts("")
        assert len(audio) == 0

    def test_set_speed_validation(self, mock_tts):
        """語速範圍驗證"""
        with pytest.raises(ValueError):
            mock_tts.set_speed(3.0)
```
