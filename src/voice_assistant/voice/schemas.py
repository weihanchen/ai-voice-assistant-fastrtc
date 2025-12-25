"""語音管線資料模型

定義音訊處理、語音辨識、語音合成與對話狀態相關的資料結構。
"""

from datetime import datetime
from enum import Enum
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field


class AudioFrame(BaseModel):
    """音訊資料框架"""

    sample_rate: int = Field(default=24000, description="取樣率 (Hz)")
    samples: bytes = Field(description="音訊樣本資料 (numpy array 序列化)")
    dtype: Literal["int16", "float32"] = Field(
        default="float32", description="資料型別"
    )
    channels: int = Field(default=1, description="聲道數 (1=mono, 2=stereo)")
    timestamp_ms: int = Field(default=0, description="時間戳記 (毫秒)")

    model_config = {"arbitrary_types_allowed": True}

    def to_numpy(self) -> NDArray[np.float32]:
        """轉換為 numpy array"""
        dtype_map = {"int16": np.int16, "float32": np.float32}
        return np.frombuffer(self.samples, dtype=dtype_map[self.dtype])

    @classmethod
    def from_numpy(
        cls,
        array: NDArray,
        sample_rate: int = 24000,
        timestamp_ms: int = 0,
    ) -> "AudioFrame":
        """從 numpy array 建立"""
        dtype_str: Literal["int16", "float32"] = (
            "int16" if array.dtype == np.int16 else "float32"
        )
        return cls(
            sample_rate=sample_rate,
            samples=array.tobytes(),
            dtype=dtype_str,
            timestamp_ms=timestamp_ms,
        )


class TranscribedText(BaseModel):
    """語音辨識結果"""

    text: str = Field(description="辨識出的文字內容")
    language: str = Field(default="zh", description="偵測到的語言代碼")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="辨識信心分數 (0.0-1.0)"
    )
    duration_ms: int = Field(default=0, description="音訊時長 (毫秒)")
    is_partial: bool = Field(default=False, description="是否為部分辨識結果（串流用）")


class TTSConfig(BaseModel):
    """TTS 配置"""

    model_path: str = Field(
        default="models", description="模型快取目錄（HF_HOME）"
    )
    voice: str = Field(
        default="zf_001", description="音色 ID (zf_* 中文女聲, zm_* 中文男聲)"
    )
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="語速倍率 (0.5-2.0)")
    language: str = Field(default="z", description="語言代碼 (z=中文)")
    sample_rate: int = Field(default=24000, description="輸出取樣率 (Hz)")


class VoiceState(str, Enum):
    """語音管線狀態"""

    IDLE = "idle"  # 待命
    LISTENING = "listening"  # 聆聽中
    PROCESSING = "processing"  # 處理中（ASR + LLM）
    SPEAKING = "speaking"  # 回應中（TTS 播放）
    INTERRUPTED = "interrupted"  # 被中斷


class ConversationState(BaseModel):
    """對話狀態"""

    state: VoiceState = Field(default=VoiceState.IDLE, description="目前狀態")
    last_user_text: str | None = Field(
        default=None, description="最後一次使用者輸入文字"
    )
    last_assistant_text: str | None = Field(
        default=None, description="最後一次助理回應文字"
    )
    turn_count: int = Field(default=0, description="對話輪數")
    started_at: datetime = Field(
        default_factory=datetime.now, description="對話開始時間"
    )
    last_activity_at: datetime = Field(
        default_factory=datetime.now, description="最後活動時間"
    )

    def transition_to(self, new_state: VoiceState) -> None:
        """狀態轉移"""
        self.state = new_state
        self.last_activity_at = datetime.now()


class STTConfig(BaseModel):
    """ASR 配置"""

    model_size: str = Field(default="tiny", description="Whisper 模型大小")
    device: str = Field(default="cpu", description="運算裝置")
    language: str = Field(default="zh", description="目標語言")
    beam_size: int = Field(default=1, description="Beam search 大小")
    vad_filter: bool = Field(default=True, description="啟用 VAD 過濾")


class VADConfig(BaseModel):
    """語音活動偵測配置"""

    pause_threshold_ms: int = Field(default=500, description="停頓閾值 (毫秒)")
    min_speech_duration_ms: int = Field(default=250, description="最小語音時長")
    speech_threshold: float = Field(default=0.5, description="語音偵測閾值")


class VoicePipelineConfig(BaseModel):
    """語音管線配置"""

    stt: STTConfig = Field(default_factory=STTConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    vad: VADConfig = Field(default_factory=VADConfig)
    can_interrupt: bool = Field(default=True, description="允許使用者中斷")
    server_host: str = Field(default="0.0.0.0", description="伺服器主機")
    server_port: int = Field(default=7860, description="伺服器埠號")
