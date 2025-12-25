"""語音管線主類別

整合 STT、LLM、TTS 實現完整語音對話流程。
"""

import asyncio
import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from voice_assistant.llm.schemas import ChatMessage
from voice_assistant.voice.schemas import (
    ConversationState,
    VoicePipelineConfig,
    VoiceState,
)
from voice_assistant.voice.stt.whisper import WhisperSTT
from voice_assistant.voice.tts.kokoro import KokoroTTS

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient


class VoicePipeline:
    """語音管線主類別

    整合 STT、LLM、TTS 實現完整語音對話流程。
    """

    def __init__(
        self,
        config: VoicePipelineConfig,
        llm_client: "LLMClient",
        stt: WhisperSTT | None = None,
        tts: KokoroTTS | None = None,
    ):
        """初始化語音管線

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
            language=config.stt.language,
        )

        # 初始化 TTS（model_path 為 HF_HOME 快取目錄）
        self.tts = tts or KokoroTTS(
            model_path=config.tts.model_path,
            voice=config.tts.voice,
            speed=config.tts.speed,
        )

    def process_audio(
        self,
        audio: tuple[int, NDArray[np.float32]],
    ) -> Iterator[tuple[int, NDArray[np.float32]]]:
        """處理音訊輸入，回傳語音回應串流

        這是 FastRTC ReplyOnPause handler 的主要進入點。

        Args:
            audio: (sample_rate, audio_array) 使用者語音

        Yields:
            (sample_rate, audio_chunk) 助理語音回應
        """
        # 更新狀態為處理中
        self.state.transition_to(VoiceState.PROCESSING)
        sample_rate, audio_array = audio
        logger.info(f"[Pipeline] 收到音訊: sample_rate={sample_rate}, shape={audio_array.shape}, dtype={audio_array.dtype}")

        try:
            # 1. 語音轉文字
            logger.info("[Pipeline] 開始 STT 辨識...")
            user_text = self.stt.stt(audio)
            logger.info(f"[Pipeline] STT 結果: '{user_text}'")

            if not user_text.strip():
                # 無有效輸入，回到待命
                logger.info("[Pipeline] 無有效語音輸入，跳過")
                self.state.transition_to(VoiceState.IDLE)
                return

            self.state.last_user_text = user_text

            # 2. LLM 處理
            logger.info(f"[Pipeline] 呼叫 LLM: '{user_text}'")
            user_message = ChatMessage(role="user", content=user_text)
            llm_response = asyncio.get_event_loop().run_until_complete(
                self.llm_client.chat([user_message])
            )
            response = llm_response.content or ""
            logger.info(f"[Pipeline] LLM 回應: '{response}'")
            self.state.last_assistant_text = response

            # 3. 更新狀態為回應中
            self.state.transition_to(VoiceState.SPEAKING)
            self.state.turn_count += 1

            # 4. TTS 串流輸出
            logger.info("[Pipeline] 開始 TTS 串流...")
            chunk_count = 0
            for audio_chunk in self.tts.stream_tts_sync(response):
                chunk_count += 1
                yield audio_chunk
            logger.info(f"[Pipeline] TTS 完成，共 {chunk_count} 個音訊片段")

            # 5. 回應完成，回到待命
            self.state.transition_to(VoiceState.IDLE)

        except Exception as e:
            # 錯誤處理：播放錯誤提示
            logger.error(f"[Pipeline] 處理錯誤: {e}", exc_info=True)
            error_message = "抱歉，處理時發生錯誤，請再試一次。"
            for audio_chunk in self.tts.stream_tts_sync(error_message):
                yield audio_chunk
            self.state.transition_to(VoiceState.IDLE)
            raise e

    def on_interrupt(self) -> None:
        """處理使用者中斷

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
