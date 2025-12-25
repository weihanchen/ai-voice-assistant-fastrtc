# Contract: Voice Pipeline

**Date**: 2025-12-25
**Feature**: 001-fastrtc-voice-pipeline

## Overview

語音管線主契約，定義 VoicePipeline 類別與 FastRTC 整合介面。

---

## VoicePipeline Class

```python
from typing import Iterator, Optional, Callable
import numpy as np
from numpy.typing import NDArray
from voice_assistant.voice.stt import WhisperSTT
from voice_assistant.voice.tts import KokoroTTS
from voice_assistant.llm import LLMClient
from voice_assistant.voice.schemas import (
    VoicePipelineConfig,
    ConversationState,
    VoiceState
)

class VoicePipeline:
    """
    語音管線主類別

    整合 STT、LLM、TTS 實現完整語音對話流程。
    """

    def __init__(
        self,
        config: VoicePipelineConfig,
        llm_client: LLMClient,
        stt: Optional[WhisperSTT] = None,
        tts: Optional[KokoroTTS] = None
    ):
        """
        初始化語音管線

        Args:
            config: 管線配置
            llm_client: LLM 客戶端（來自 000 規格）
            stt: STT 實例（可選，預設自動建立）
            tts: TTS 實例（可選，預設自動建立）
        """
        self.config = config
        self.llm_client = llm_client
        self.state = ConversationState()

        # 初始化 STT
        self.stt = stt or WhisperSTT(
            model_size=config.stt.model_size,
            device=config.stt.device,
            language=config.stt.language
        )

        # 初始化 TTS
        self.tts = tts or KokoroTTS(
            model_path=config.tts.model_path,
            voices_path=config.tts.voices_path,
            voice=config.tts.voice,
            speed=config.tts.speed
        )

    def process_audio(
        self,
        audio: tuple[int, NDArray[np.float32]]
    ) -> Iterator[tuple[int, NDArray[np.float32]]]:
        """
        處理音訊輸入，回傳語音回應串流

        這是 FastRTC ReplyOnPause handler 的主要進入點。

        Args:
            audio: (sample_rate, audio_array) 使用者語音

        Yields:
            (sample_rate, audio_chunk) 助理語音回應
        """
        # 更新狀態為處理中
        self.state.transition_to(VoiceState.PROCESSING)

        try:
            # 1. 語音轉文字
            user_text = self.stt.stt(audio)

            if not user_text.strip():
                # 無有效輸入，回到待命
                self.state.transition_to(VoiceState.IDLE)
                return

            self.state.last_user_text = user_text

            # 2. LLM 處理
            response = self.llm_client.chat(user_text)
            self.state.last_assistant_text = response

            # 3. 更新狀態為回應中
            self.state.transition_to(VoiceState.SPEAKING)
            self.state.turn_count += 1

            # 4. TTS 串流輸出
            for audio_chunk in self.tts.stream_tts_sync(response):
                yield audio_chunk

            # 5. 回應完成，回到待命
            self.state.transition_to(VoiceState.IDLE)

        except Exception as e:
            # 錯誤處理：播放錯誤提示
            error_message = "抱歉，處理時發生錯誤，請再試一次。"
            for audio_chunk in self.tts.stream_tts_sync(error_message):
                yield audio_chunk
            self.state.transition_to(VoiceState.IDLE)
            raise

    def on_interrupt(self) -> None:
        """
        處理使用者中斷

        當使用者在助理回應時開始說話，由 FastRTC 呼叫。
        """
        if self.state.state == VoiceState.SPEAKING:
            self.state.transition_to(VoiceState.INTERRUPTED)
            # FastRTC 會自動停止播放

    def get_state(self) -> ConversationState:
        """取得目前對話狀態"""
        return self.state

    def reset(self) -> None:
        """重置對話狀態"""
        self.state = ConversationState()
```

---

## FastRTC Integration

```python
from fastrtc import Stream, ReplyOnPause, AlgoOptions, SileroVadOptions
from voice_assistant.voice import VoicePipeline
from voice_assistant.voice.schemas import VoicePipelineConfig
from voice_assistant.llm import LLMClient
from voice_assistant.config import Settings

def create_voice_stream(settings: Settings) -> Stream:
    """
    建立 FastRTC 語音串流

    Args:
        settings: 應用程式設定

    Returns:
        配置好的 FastRTC Stream
    """
    # 初始化 LLM Client
    llm_client = LLMClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model
    )

    # 初始化語音管線
    config = VoicePipelineConfig()
    pipeline = VoicePipeline(config=config, llm_client=llm_client)

    # 建立 FastRTC Stream
    stream = Stream(
        handler=ReplyOnPause(
            pipeline.process_audio,
            algo_options=AlgoOptions(
                audio_chunk_duration=config.vad.pause_threshold_ms / 1000,
                started_talking_threshold=0.2,
                speech_threshold=config.vad.speech_threshold
            ),
            model_options=SileroVadOptions(
                threshold=0.5,
                min_speech_duration_ms=config.vad.min_speech_duration_ms,
                min_silence_duration_ms=config.vad.pause_threshold_ms
            ),
            can_interrupt=config.can_interrupt,
            output_sample_rate=config.tts.sample_rate
        ),
        modality="audio",
        mode="send-receive"
    )

    return stream
```

---

## Main Entry Point

```python
# src/voice_assistant/main.py

from voice_assistant.voice import create_voice_stream
from voice_assistant.config import get_settings

def main():
    """語音助理入口點"""
    settings = get_settings()

    # 建立語音串流
    stream = create_voice_stream(settings)

    # 啟動 Gradio UI
    stream.ui.launch(
        server_name=settings.server_host,
        server_port=settings.server_port,
        share=False
    )

if __name__ == "__main__":
    main()
```

---

## State Machine Events

| 事件 | 觸發條件 | 狀態轉移 |
|------|----------|----------|
| `speech_detected` | VAD 偵測到語音 | IDLE → LISTENING |
| `pause_detected` | 靜音 >= 0.5 秒 | LISTENING → PROCESSING |
| `response_ready` | LLM 回應完成 | PROCESSING → SPEAKING |
| `playback_complete` | TTS 播放完成 | SPEAKING → IDLE |
| `user_interrupt` | 使用者在播放中說話 | SPEAKING → INTERRUPTED |
| `resume` | 中斷後處理完成 | INTERRUPTED → PROCESSING |

---

## Error Handling

```python
from enum import Enum

class VoiceError(str, Enum):
    """語音管線錯誤類型"""
    STT_FAILED = "stt_failed"
    LLM_FAILED = "llm_failed"
    TTS_FAILED = "tts_failed"
    TIMEOUT = "timeout"

ERROR_MESSAGES = {
    VoiceError.STT_FAILED: "抱歉，我沒有聽清楚，請再說一次。",
    VoiceError.LLM_FAILED: "抱歉，處理時發生問題，請稍後再試。",
    VoiceError.TTS_FAILED: "語音輸出發生問題。",
    VoiceError.TIMEOUT: "回應時間過長，請再試一次。"
}
```

---

## Testing

```python
import pytest
from unittest.mock import Mock, MagicMock
import numpy as np
from voice_assistant.voice import VoicePipeline
from voice_assistant.voice.schemas import VoicePipelineConfig, VoiceState

class TestVoicePipeline:

    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.chat.return_value = "這是測試回應。"
        return llm

    @pytest.fixture
    def mock_stt(self):
        stt = Mock()
        stt.stt.return_value = "這是測試輸入"
        return stt

    @pytest.fixture
    def mock_tts(self):
        tts = Mock()
        tts.stream_tts_sync.return_value = iter([
            (24000, np.zeros(1000, dtype=np.float32))
        ])
        return tts

    @pytest.fixture
    def pipeline(self, mock_llm, mock_stt, mock_tts):
        return VoicePipeline(
            config=VoicePipelineConfig(),
            llm_client=mock_llm,
            stt=mock_stt,
            tts=mock_tts
        )

    def test_initial_state_is_idle(self, pipeline):
        """初始狀態為 IDLE"""
        assert pipeline.state.state == VoiceState.IDLE

    def test_process_audio_calls_stt(self, pipeline, mock_stt):
        """處理音訊會呼叫 STT"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        list(pipeline.process_audio(audio))
        mock_stt.stt.assert_called_once()

    def test_process_audio_calls_llm(self, pipeline, mock_llm):
        """處理音訊會呼叫 LLM"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        list(pipeline.process_audio(audio))
        mock_llm.chat.assert_called_once_with("這是測試輸入")

    def test_process_audio_yields_tts_output(self, pipeline):
        """處理音訊會產生 TTS 輸出"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        chunks = list(pipeline.process_audio(audio))
        assert len(chunks) == 1

    def test_state_transitions(self, pipeline):
        """狀態轉移正確"""
        audio = (16000, np.zeros(16000, dtype=np.float32))

        # 消耗 generator
        list(pipeline.process_audio(audio))

        # 最終狀態應為 IDLE
        assert pipeline.state.state == VoiceState.IDLE
        assert pipeline.state.turn_count == 1
```
