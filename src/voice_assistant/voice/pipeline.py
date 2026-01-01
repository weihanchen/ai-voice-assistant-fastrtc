"""語音管線主類別

整合 STT、LLM、TTS 實現完整語音對話流程。
"""

import asyncio
import concurrent.futures
import json
import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING

import numpy as np
from fastrtc import AdditionalOutputs
from numpy.typing import NDArray

from voice_assistant.llm.schemas import ChatMessage
from voice_assistant.tools.registry import ToolRegistry
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

# Log 敏感資料最大長度（避免洩露 PII）
_LOG_MAX_TEXT_LEN = 50


def _truncate_for_log(text: str, max_len: int = _LOG_MAX_TEXT_LEN) -> str:
    """截斷文字用於 log，避免敏感資料外洩"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _run_async_safely(coro):
    """安全地執行 async coroutine，處理 nested event loop 情況

    在 Gradio/FastRTC 環境中可能已有 event loop 執行中，
    此函式會偵測並使用適當的方式執行 coroutine。
    """
    try:
        asyncio.get_running_loop()
        # 已有執行中的 loop，使用 thread pool 避免 nested loop 錯誤
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # 沒有執行中的 loop，直接使用 asyncio.run()
        return asyncio.run(coro)


if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient


class VoicePipeline:
    """語音管線主類別

    整合 STT、LLM、TTS 實現完整語音對話流程。
    """

    # 系統提示詞
    SYSTEM_PROMPT = (
        "你是一個友善的 AI 語音助理。"
        "請用繁體中文回答，回答要簡潔、口語化，適合語音輸出。"
        "當使用者詢問天氣相關問題時，請使用 get_weather 工具查詢天氣資訊。"
        "當使用者詢問匯率或貨幣換算（例如：美金匯率、100 美金換台幣）時，"
        "請使用 get_exchange_rate 工具查詢匯率或換算結果。"
        "當使用者詢問股票價格或股價（例如：台積電股價、Apple 多少錢）時，"
        "請使用 get_stock_price 工具查詢股票報價。"
        "根據工具回傳的資料，用自然的口語回應使用者。"
    )

    def __init__(
        self,
        config: VoicePipelineConfig,
        llm_client: "LLMClient",
        stt: WhisperSTT | None = None,
        tts: KokoroTTS | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        """初始化語音管線

        Args:
            config: 管線配置
            llm_client: LLM 客戶端（來自 000 規格）
            stt: STT 實例（可選，預設自動建立）
            tts: TTS 實例（可選，預設自動建立）
            tool_registry: 工具註冊表（可選，預設使用空註冊表）
        """
        self.config = config
        self.llm_client = llm_client
        self.state = ConversationState()

        # 初始化 ToolRegistry（由外部注入，Pipeline 不依賴特定工具）
        self.tool_registry = ToolRegistry() if tool_registry is None else tool_registry

        # 初始化 STT
        self.stt = stt or WhisperSTT(
            model_size=config.stt.model_size,
            model_path=config.stt.model_path,
            device=config.stt.device,
            language=config.stt.language,
            beam_size=config.stt.beam_size,
            vad_filter=config.stt.vad_filter,
            min_silence_duration_ms=config.vad.min_silence_duration_ms,
        )

        # 初始化 TTS（model_path 為 HF_HOME 快取目錄）
        self.tts = tts or KokoroTTS(
            model_path=config.tts.model_path,
            voice=config.tts.voice,
            speed=config.tts.speed,
        )

    async def _process_tool_calls(
        self,
        messages: list[ChatMessage],
        llm_response: ChatMessage,
        tools: list[dict],
    ) -> str:
        """處理 LLM 的 Tool Calls 回應

        Args:
            messages: 目前的對話訊息列表
            llm_response: LLM 回應（可能包含 tool_calls）
            tools: 工具定義列表

        Returns:
            最終的文字回應
        """
        # 如果沒有 tool_calls，直接回傳內容
        if not llm_response.tool_calls:
            return llm_response.content or ""

        logger.info(
            f"[Pipeline] LLM 要求呼叫工具: "
            f"{[tc.function['name'] for tc in llm_response.tool_calls]}"
        )

        # 加入 assistant 訊息（包含 tool_calls）
        messages.append(llm_response)

        # 執行每個 tool call
        for tool_call in llm_response.tool_calls:
            tool_name = tool_call.function["name"]
            try:
                arguments = json.loads(tool_call.function["arguments"])
            except json.JSONDecodeError as e:
                # JSON 解析失敗時，回傳錯誤訊息給 LLM
                logger.warning(f"[Pipeline] 工具參數 JSON 解析失敗: {e}")
                tool_message = ChatMessage(
                    role="tool",
                    content="Error: 無法解析工具參數",
                    tool_call_id=tool_call.id,
                )
                messages.append(tool_message)
                continue

            logger.info(f"[Pipeline] 執行工具 {tool_name}")

            # 執行工具
            result = await self.tool_registry.execute(tool_name, arguments)
            logger.info("[Pipeline] 工具執行完成")

            # 加入 tool 結果訊息
            tool_message = ChatMessage(
                role="tool",
                content=result.to_content(),
                tool_call_id=tool_call.id,
            )
            messages.append(tool_message)

        # 再次呼叫 LLM 產生最終回應
        final_response = await self.llm_client.chat(
            messages, tools=tools, system_prompt=self.SYSTEM_PROMPT
        )

        return final_response.content or ""

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
        logger.info(
            f"[Pipeline] 收到音訊: sample_rate={sample_rate}, "
            f"shape={audio_array.shape}, dtype={audio_array.dtype}"
        )

        try:
            # 1. 語音轉文字
            logger.info("[Pipeline] 開始 STT 辨識...")
            user_text = self.stt.stt(audio)
            logger.info(f"[Pipeline] STT 結果: '{_truncate_for_log(user_text)}'")

            if not user_text.strip():
                # 無有效輸入，回到待命
                logger.info("[Pipeline] 無有效語音輸入，跳過")
                self.state.transition_to(VoiceState.IDLE)
                return

            self.state.last_user_text = user_text

            # 2. LLM 處理（含 Tool Calling）
            logger.info(f"[Pipeline] 呼叫 LLM: '{_truncate_for_log(user_text)}'")
            user_message = ChatMessage(role="user", content=user_text)
            messages = [user_message]

            # 取得工具定義
            tools = self.tool_registry.get_openai_tools()

            # 第一次 LLM 呼叫
            llm_response = _run_async_safely(
                self.llm_client.chat(
                    messages, tools=tools, system_prompt=self.SYSTEM_PROMPT
                )
            )

            # 處理 Tool Calls（如果有）
            response = _run_async_safely(
                self._process_tool_calls(messages, llm_response, tools)
            )
            logger.info(f"[Pipeline] LLM 回應: '{_truncate_for_log(response)}'")
            self.state.last_assistant_text = response

            # 3. 更新狀態為回應中
            self.state.transition_to(VoiceState.SPEAKING)
            self.state.turn_count += 1

            # 4. TTS 串流輸出
            logger.info("[Pipeline] 開始 TTS 串流...")
            chunk_count = 0
            interrupted = False
            for audio_chunk in self.tts.stream_tts_sync(response):
                # 檢查是否被中斷（僅當 can_interrupt 啟用時）
                if (
                    self.config.can_interrupt
                    and self.state.state == VoiceState.INTERRUPTED
                ):
                    logger.info("[Pipeline] TTS 被中斷，停止輸出")
                    interrupted = True
                    break
                chunk_count += 1
                yield audio_chunk

            if interrupted:
                logger.info(f"[Pipeline] TTS 中斷於第 {chunk_count} 個音訊片段")
            else:
                logger.info(f"[Pipeline] TTS 完成，共 {chunk_count} 個音訊片段")

            # 5. 回應完成，回到待命
            self.state.transition_to(VoiceState.IDLE)

        except Exception as e:
            # 錯誤處理：播放錯誤提示，不再重新拋出以維持串流
            logger.error(f"[Pipeline] 處理錯誤: {e}", exc_info=True)
            error_message = "抱歉，處理時發生錯誤，請再試一次。"
            try:
                for audio_chunk in self.tts.stream_tts_sync(error_message):
                    yield audio_chunk
            except Exception as tts_error:
                logger.error(f"[Pipeline] 錯誤訊息 TTS 失敗: {tts_error}")
            finally:
                self.state.transition_to(VoiceState.IDLE)

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

    def process_audio_with_outputs(
        self,
        audio: tuple[int, NDArray[np.float32]],
    ) -> Iterator[tuple[int, NDArray[np.float32]] | AdditionalOutputs]:
        """處理音訊輸入，回傳語音回應串流與 UI 更新

        這是支援 AdditionalOutputs 的 FastRTC handler，
        用於同步更新 Gradio UI 元件。

        Args:
            audio: (sample_rate, audio_array) 使用者語音

        Yields:
            - AdditionalOutputs(history, status): UI 更新
            - (sample_rate, audio_chunk): 助理語音回應
        """
        # 更新狀態為處理中
        self.state.transition_to(VoiceState.PROCESSING)
        sample_rate, audio_array = audio
        logger.info(
            f"[Pipeline] 收到音訊: sample_rate={sample_rate}, "
            f"shape={audio_array.shape}, dtype={audio_array.dtype}"
        )

        # 發送初始狀態更新
        yield AdditionalOutputs(
            self.state.get_gradio_messages(),
            self.state.get_ui_state().status_text,
        )

        try:
            # 1. 語音轉文字
            logger.info("[Pipeline] 開始 STT 辨識...")
            user_text = self.stt.stt(audio)
            logger.info(f"[Pipeline] STT 結果: '{_truncate_for_log(user_text)}'")

            if not user_text.strip():
                # 無有效輸入，回到待命
                logger.info("[Pipeline] 無有效語音輸入，跳過")
                self.state.transition_to(VoiceState.IDLE)
                yield AdditionalOutputs(
                    self.state.get_gradio_messages(),
                    self.state.get_ui_state().status_text,
                )
                return

            # T013: STT 完成後更新 history
            self.state.last_user_text = user_text
            self.state.history.add_user_message(user_text)

            # 發送 UI 更新：使用者訊息已加入
            yield AdditionalOutputs(
                self.state.get_gradio_messages(),
                "⏳ 處理中...",
            )

            # 2. LLM 處理（含 Tool Calling）
            logger.info(f"[Pipeline] 呼叫 LLM: '{_truncate_for_log(user_text)}'")
            user_message = ChatMessage(role="user", content=user_text)
            messages = [user_message]

            # 取得工具定義
            tools = self.tool_registry.get_openai_tools()

            # 第一次 LLM 呼叫
            llm_response = _run_async_safely(
                self.llm_client.chat(
                    messages, tools=tools, system_prompt=self.SYSTEM_PROMPT
                )
            )

            # 處理 Tool Calls（如果有）
            response = _run_async_safely(
                self._process_tool_calls(messages, llm_response, tools)
            )
            logger.info(f"[Pipeline] LLM 回應: '{_truncate_for_log(response)}'")

            # T014: LLM 回應後更新 history
            self.state.last_assistant_text = response
            self.state.history.add_assistant_message(response)

            # 3. 更新狀態為回應中
            self.state.transition_to(VoiceState.SPEAKING)
            self.state.turn_count += 1

            # 發送 UI 更新：助理回應已加入
            yield AdditionalOutputs(
                self.state.get_gradio_messages(),
                self.state.get_ui_state().status_text,
            )

            # 4. TTS 串流輸出
            logger.info("[Pipeline] 開始 TTS 串流...")
            chunk_count = 0
            interrupted = False
            for audio_chunk in self.tts.stream_tts_sync(response):
                # 檢查是否被中斷（僅當 can_interrupt 啟用時）
                if (
                    self.config.can_interrupt
                    and self.state.state == VoiceState.INTERRUPTED
                ):
                    logger.info("[Pipeline] TTS 被中斷，停止輸出")
                    interrupted = True
                    break
                chunk_count += 1
                yield audio_chunk

            if interrupted:
                logger.info(f"[Pipeline] TTS 中斷於第 {chunk_count} 個音訊片段")
                yield AdditionalOutputs(
                    self.state.get_gradio_messages(),
                    "⏸️ 已中斷",
                )
            else:
                logger.info(f"[Pipeline] TTS 完成，共 {chunk_count} 個音訊片段")

            # 5. 回應完成，回到待命
            self.state.transition_to(VoiceState.IDLE)
            yield AdditionalOutputs(
                self.state.get_gradio_messages(),
                self.state.get_ui_state().status_text,
            )

        except Exception as e:
            # 錯誤處理：播放錯誤提示
            logger.error(f"[Pipeline] 處理錯誤: {e}", exc_info=True)
            error_message = "抱歉，處理時發生錯誤，請再試一次。"

            # 發送錯誤狀態
            yield AdditionalOutputs(
                self.state.get_gradio_messages(),
                "❌ 發生錯誤",
            )

            try:
                for audio_chunk in self.tts.stream_tts_sync(error_message):
                    yield audio_chunk
            except Exception as tts_error:
                logger.error(f"[Pipeline] 錯誤訊息 TTS 失敗: {tts_error}")
            finally:
                self.state.transition_to(VoiceState.IDLE)
                yield AdditionalOutputs(
                    self.state.get_gradio_messages(),
                    self.state.get_ui_state().status_text,
                )
