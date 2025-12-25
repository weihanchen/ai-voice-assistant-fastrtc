# Research: FastRTC Voice Pipeline

**Date**: 2025-12-25
**Feature**: 001-fastrtc-voice-pipeline

## 1. faster-whisper 整合 FastRTC

### Decision
使用 faster-whisper 實作 FastRTC 的 STTModel Protocol，支援中文語音辨識。

### Rationale
- FastRTC 內建 Moonshine 僅支援英文
- faster-whisper 比 OpenAI whisper 快 4 倍，記憶體使用更低
- 可透過實作 STTModel Protocol 無縫整合 FastRTC
- tiny 模型約 39MB，符合成本最小化原則

### Implementation

```python
from typing import Protocol
import numpy as np
from numpy.typing import NDArray

class STTModel(Protocol):
    """FastRTC STTModel Protocol"""
    def stt(self, audio: tuple[int, NDArray[np.int16 | np.float32]]) -> str: ...
```

```python
from faster_whisper import WhisperModel
import numpy as np

class WhisperSTT:
    """faster-whisper 實作 FastRTC STTModel Protocol"""

    def __init__(self, model_size: str = "tiny", device: str = "cpu"):
        self.model = WhisperModel(model_size, device=device, compute_type="int8")

    def stt(self, audio: tuple[int, np.ndarray]) -> str:
        sample_rate, audio_array = audio
        # 轉換為 float32 並正規化
        if audio_array.dtype == np.int16:
            audio_array = audio_array.astype(np.float32) / 32768.0

        segments, info = self.model.transcribe(
            audio_array,
            language="zh",  # 繁體中文
            beam_size=1,    # 最快速度
            vad_filter=True # 過濾靜音
        )
        return "".join(segment.text for segment in segments)
```

### Alternatives Considered
| 方案 | 說明 | 拒絕原因 |
|------|------|----------|
| Moonshine | FastRTC 內建 | 不支援中文 |
| OpenAI Whisper | 原版模型 | 速度較慢，記憶體使用高 |
| Azure Speech | 雲端 API | 需付費，增加延遲 |

### References
- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [FastRTC STT Gallery](https://fastrtc.org/speech_to_text_gallery/)

---

## 2. Kokoro TTS 中文支援

### Decision
使用 Kokoro-82M-v1.1-zh 中文模型，透過 kokoro-onnx 套件整合。

### Rationale
- Kokoro 有專用中文模型，支援 103 種中文音色
- kokoro-onnx 提供簡潔 Python API
- ONNX 格式支援 CPU 推理，量化模型約 80MB
- 支援串流輸出，適合即時語音回應

### Implementation

```python
from kokoro_onnx import Kokoro
import numpy as np

class KokoroTTS:
    """Kokoro TTS 中文實作"""

    def __init__(self, model_path: str, voices_path: str):
        self.kokoro = Kokoro(model_path, voices_path)
        self.voice = "zf_001"  # 中文女聲
        self.speed = 1.0

    def tts(self, text: str) -> tuple[int, np.ndarray]:
        """同步生成語音"""
        samples, sample_rate = self.kokoro.create(
            text,
            voice=self.voice,
            speed=self.speed,
            lang="zh"
        )
        return (sample_rate, samples)

    async def stream_tts(self, text: str):
        """非同步串流生成"""
        stream = self.kokoro.create_stream(
            text,
            voice=self.voice,
            speed=self.speed,
            lang="zh"
        )
        async for samples, sample_rate in stream:
            yield (sample_rate, samples)
```

### Model Files
- `kokoro-v1.0.int8.onnx`（量化模型，約 80MB）
- `voices-v1.0.bin`（音色檔案）

### Chinese Voice Options
| 前綴 | 說明 |
|------|------|
| `zf_*` | 中文女聲（55 種） |
| `zm_*` | 中文男聲（45 種） |

### Alternatives Considered
| 方案 | 說明 | 拒絕原因 |
|------|------|----------|
| FastRTC 內建 Kokoro | 預設英文 | 需要中文模型 |
| Edge TTS | 微軟雲端 | 需網路，增加延遲 |
| pyttsx3 | 本地 TTS | 音質較差 |

### References
- [Kokoro-82M-v1.1-zh on Hugging Face](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh)
- [kokoro-onnx GitHub](https://github.com/thewh1teagle/kokoro-onnx)
- [kokoro-onnx PyPI](https://pypi.org/project/kokoro-onnx/)

---

## 3. FastRTC ReplyOnPause 整合

### Decision
使用 FastRTC ReplyOnPause 處理器，配置 0.5 秒停頓閾值。

### Rationale
- ReplyOnPause 自動處理語音偵測與輪流機制
- 內建 Silero VAD 模型，過濾背景噪音
- 支援中斷（can_interrupt=True）
- 可自訂停頓偵測參數

### Implementation

```python
from fastrtc import Stream, ReplyOnPause, AlgoOptions, SileroVadOptions

def voice_handler(audio: tuple[int, np.ndarray]):
    """語音處理主函式"""
    # STT
    text = stt_model.stt(audio)

    # LLM 處理
    response = llm_client.chat(text)

    # TTS 串流輸出
    for audio_chunk in tts_model.stream_tts_sync(response):
        yield audio_chunk

stream = Stream(
    handler=ReplyOnPause(
        voice_handler,
        algo_options=AlgoOptions(
            audio_chunk_duration=0.5,      # 0.5 秒閾值
            started_talking_threshold=0.2,
            speech_threshold=0.1
        ),
        model_options=SileroVadOptions(
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=500   # 0.5 秒靜音觸發
        ),
        can_interrupt=True,  # 支援中斷
        output_sample_rate=24000
    ),
    modality="audio",
    mode="send-receive"
)
```

### Configuration Parameters
| 參數 | 值 | 說明 |
|------|-----|------|
| `audio_chunk_duration` | 0.5 | 音訊區塊長度（秒） |
| `min_silence_duration_ms` | 500 | 最小靜音時長觸發回應 |
| `can_interrupt` | True | 允許使用者打斷 |
| `output_sample_rate` | 24000 | 輸出取樣率（Kokoro 預設） |

### References
- [FastRTC ReplyOnPause 文件](https://fastrtc.org/reference/reply_on_pause/)
- [FastRTC Audio Streaming](https://fastrtc.org/userguide/audio/)

---

## 4. Gradio UI 整合

### Decision
使用 FastRTC 內建的 Gradio WebRTC UI。

### Rationale
- 一行程式碼啟動：`stream.ui.launch()`
- 內建麥克風權限處理與錯誤訊息
- 支援 WebRTC，低延遲
- 自動處理瀏覽器相容性

### Implementation

```python
# 啟動 Gradio UI
stream.ui.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=False
)
```

### References
- [FastRTC 官網](https://fastrtc.org/)

---

## 5. 相依套件版本

### 核心套件
| 套件 | 版本 | 說明 |
|------|------|------|
| fastrtc | >=0.0.33 | WebRTC 框架 |
| faster-whisper | >=1.0.0 | 中文 ASR |
| kokoro-onnx | >=0.4.0 | 中文 TTS（需 Python <3.14） |
| openai | >=1.58.x | LLM SDK |
| pydantic | >=2.10.x | 資料驗證 |

### 注意事項
- **kokoro-onnx** 目前要求 Python >=3.10, <3.14
- 若使用 Python 3.14，需評估替代方案或等待套件更新
- 建議先以 Python 3.12 或 3.13 開發測試

### 替代方案（若 Python 版本衝突）
- 直接使用 kokoro 套件（非 ONNX）：`pip install kokoro>=0.8.2 "misaki[zh]>=0.8.2"`
- 使用 sherpa-onnx：支援 Kokoro 模型且版本相容性更好

---

## 6. 效能預估

| 項目 | 預估值 | 說明 |
|------|--------|------|
| ASR 延遲 | ~0.5s | faster-whisper tiny, CPU |
| TTS 延遲 | ~0.3s | Kokoro 量化模型, CPU |
| LLM 延遲 | ~1.5s | GPT-4o-mini API |
| 總延遲 | ~2.3s | 低於 3 秒目標 |
| 記憶體 | ~200MB | ASR 39MB + TTS 80MB + FastRTC |

---

## Summary

所有技術選型已完成研究，無需進一步澄清：

1. **ASR**: faster-whisper tiny 模型，實作 STTModel Protocol
2. **TTS**: Kokoro-82M-v1.1-zh 中文模型，透過 kokoro-onnx
3. **Handler**: FastRTC ReplyOnPause，0.5 秒停頓閾值
4. **UI**: FastRTC 內建 Gradio WebRTC UI
5. **Python 版本**: 建議 3.12/3.13（kokoro-onnx 相容性考量）
