# Contract: STT Adapter

**Date**: 2025-12-25
**Feature**: 001-fastrtc-voice-pipeline

## Overview

語音轉文字（Speech-to-Text）轉接器契約，定義 FastRTC STTModel Protocol 的實作介面。

---

## Protocol Definition

```python
from typing import Protocol, runtime_checkable
import numpy as np
from numpy.typing import NDArray

@runtime_checkable
class STTModel(Protocol):
    """
    FastRTC STTModel Protocol

    所有 STT 實作必須符合此介面，以便與 FastRTC ReplyOnPause 整合。
    """

    def stt(self, audio: tuple[int, NDArray[np.int16 | np.float32]]) -> str:
        """
        將音訊轉換為文字

        Args:
            audio: Tuple of (sample_rate, audio_array)
                - sample_rate: 取樣率 (Hz)
                - audio_array: 音訊資料，dtype 為 int16 或 float32

        Returns:
            辨識出的文字內容
        """
        ...
```

---

## WhisperSTT Implementation

```python
from faster_whisper import WhisperModel
import numpy as np
from numpy.typing import NDArray

class WhisperSTT:
    """
    faster-whisper 實作 STTModel Protocol

    使用 faster-whisper 進行中文語音辨識。
    """

    def __init__(
        self,
        model_size: str = "tiny",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "zh"
    ):
        """
        初始化 Whisper 模型

        Args:
            model_size: 模型大小 (tiny/base/small/medium/large)
            device: 運算裝置 (cpu/cuda)
            compute_type: 計算精度 (int8/float16/float32)
            language: 目標語言代碼
        """
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        self.language = language

    def stt(self, audio: tuple[int, NDArray[np.int16 | np.float32]]) -> str:
        """
        將音訊轉換為文字

        Args:
            audio: (sample_rate, audio_array) tuple

        Returns:
            辨識出的中文文字
        """
        sample_rate, audio_array = audio

        # 正規化為 float32
        if audio_array.dtype == np.int16:
            audio_array = audio_array.astype(np.float32) / 32768.0

        # 執行辨識
        segments, info = self.model.transcribe(
            audio_array,
            language=self.language,
            beam_size=1,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500
            )
        )

        # 合併所有片段
        return "".join(segment.text for segment in segments).strip()
```

---

## Usage Example

```python
from voice_assistant.voice.stt import WhisperSTT
from fastrtc import ReplyOnPause, Stream

# 初始化 STT
stt = WhisperSTT(model_size="tiny", language="zh")

def handler(audio):
    text = stt.stt(audio)
    print(f"User said: {text}")
    # ... 處理後續邏輯
    yield audio  # echo back

stream = Stream(
    handler=ReplyOnPause(handler),
    modality="audio",
    mode="send-receive"
)
```

---

## Error Handling

| 錯誤情況 | 處理方式 |
|----------|----------|
| 空音訊 | 回傳空字串 `""` |
| 音訊過短 (<250ms) | 回傳空字串，由 VAD 過濾 |
| 模型載入失敗 | 拋出 `RuntimeError` |
| 辨識逾時 | 設定合理 timeout，回傳部分結果 |

---

## Configuration

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `model_size` | `"tiny"` | 模型大小，影響準確度與速度 |
| `device` | `"cpu"` | 運算裝置 |
| `compute_type` | `"int8"` | 計算精度，int8 最快 |
| `language` | `"zh"` | 目標語言（繁體/簡體中文） |

---

## Testing

```python
import pytest
import numpy as np
from voice_assistant.voice.stt import WhisperSTT

class TestWhisperSTT:

    def test_implements_protocol(self):
        """驗證實作 STTModel Protocol"""
        stt = WhisperSTT()
        assert hasattr(stt, 'stt')
        assert callable(stt.stt)

    def test_stt_returns_string(self):
        """驗證回傳字串"""
        stt = WhisperSTT()
        # 產生靜音音訊
        audio = (16000, np.zeros(16000, dtype=np.float32))
        result = stt.stt(audio)
        assert isinstance(result, str)

    def test_stt_handles_empty_audio(self):
        """處理空音訊"""
        stt = WhisperSTT()
        audio = (16000, np.array([], dtype=np.float32))
        result = stt.stt(audio)
        assert result == ""
```
