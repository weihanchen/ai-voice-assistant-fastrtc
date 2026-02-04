"""語音管線主類別

整合 STT、LLM、TTS 實現完整語音對話流程，支援角色切換。
"""

import asyncio
import json
import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING

import numpy as np
from fastrtc import AdditionalOutputs
from numpy.typing import NDArray

from voice_assistant.agents import MultiAgentExecutor
from voice_assistant.config import FlowMode, get_settings
from voice_assistant.flows import FlowExecutor
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
        loop = asyncio.get_running_loop()
        # 已有執行中的 loop，使用 run_coroutine_threadsafe 正確整合
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    except RuntimeError:
        # 沒有執行中的 loop，直接使用 asyncio.run()
        return asyncio.run(coro)


if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient


class VoicePipeline:
    """語音管線主類別

    整合 STT、LLM、TTS 實現完整語音對話流程，支援角色切換。
    """

    # 預設系統提示詞（當沒有角色時使用）
    DEFAULT_SYSTEM_PROMPT = (
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
        intent_recognizer=None,
        role_registry=None,
        state: ConversationState | None = None,
    ):
        """初始化語音管線

        Args:
            config: 管線配置
            llm_client: LLM 客戶端（來自 000 規格）
            stt: STT 實例（可選，預設自動建立）
            tts: TTS 實例（可選，預設自動建立）
            tool_registry: 工具註冊表（可選，預設使用空註冊表）
            intent_recognizer: 意圖辨識器（008 角色切換）
            role_registry: 角色註冊表（008 角色切換）
            state: 對話狀態（可選，預設自動建立）
        """
        self.config = config
        self.llm_client = llm_client
        self.state = state if state is not None else ConversationState()

        # 008: 角色切換支援
        self.intent_recognizer = intent_recognizer
        self.role_registry = role_registry

        # 初始化 ToolRegistry（由外部注入，Pipeline 不依賴特定工具）
        self.tool_registry = ToolRegistry() if tool_registry is None else tool_registry

        # 取得流程模式設定
        settings = get_settings()
        self.flow_mode = settings.flow_mode
        logger.info(f"[Pipeline] 流程模式: {self.flow_mode.value}")

        # 初始化 FlowExecutor（LangGraph 流程）
        self.flow_executor: FlowExecutor | None = None
        if self.flow_mode == FlowMode.LANGGRAPH:
            self.flow_executor = FlowExecutor(llm_client, self.tool_registry)
            logger.info("[Pipeline] LangGraph 流程已啟用")

        # 初始化 MultiAgentExecutor（多代理協作）
        self.multi_agent_executor: MultiAgentExecutor | None = None
        if self.flow_mode == FlowMode.MULTI_AGENT:
            self.multi_agent_executor = MultiAgentExecutor(
                llm_client, self.tool_registry
            )
            logger.info("[Pipeline] Multi-Agent 流程已啟用")

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

    def switch_role(self, role):
        """切換當前角色

        Args:
            role: 角色物件

        Returns:
            bool: 切換是否成功
        """
        if not role or not hasattr(role, "id"):
            return False
        self.state.current_role_id = role.id
        logger.info(
            f"[Pipeline] 角色已切換為: "
            f"{role.name if hasattr(role, 'name') else role.id}"
        )
        return True

    def _get_current_system_prompt(self) -> str:
        """取得當前角色的 system_prompt

        Returns:
            system_prompt 字串
        """
        if self.role_registry and self.state.current_role_id:
            try:
                current_role = self.role_registry.get(self.state.current_role_id)
                logger.debug(
                    f"[Pipeline] 使用角色 {current_role.name} 的 system_prompt"
                )
                return current_role.system_prompt
            except Exception as e:
                logger.warning(f"[Pipeline] 無法取得當前角色的 system_prompt: {e}")

        return self.DEFAULT_SYSTEM_PROMPT

    async def _process_tool_calls(
        self,
        messages: list[ChatMessage],
        llm_response: ChatMessage,
        tools: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        """處理 LLM 的 Tool Calls 回應

        Args:
            messages: 目前的對話訊息列表
            llm_response: LLM 回應（可能包含 tool_calls）
            tools: 工具定義列表
            system_prompt: 系統提示詞

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
            messages,
            tools=tools,
            system_prompt=system_prompt or self._get_current_system_prompt(),
        )

        return final_response.content or ""

    async def _process_with_flow(self, user_text: str) -> str:
        """使用 LangGraph 流程處理使用者輸入

        Args:
            user_text: 使用者輸入文字

        Returns:
            回應文字
        """
        if self.flow_executor is None:
            raise RuntimeError("FlowExecutor 未初始化")

        logger.info("[Pipeline] 使用 LangGraph 流程處理")
        return await self.flow_executor.execute(user_text)

    async def _process_with_multi_agent(self, user_text: str) -> str:
        """使用 Multi-Agent 流程處理使用者輸入

        Args:
            user_text: 使用者輸入文字

        Returns:
            回應文字
        """
        if self.multi_agent_executor is None:
            raise RuntimeError("MultiAgentExecutor 未初始化")

        logger.info("[Pipeline] 使用 Multi-Agent 流程處理")
        return await self.multi_agent_executor.execute(user_text)

    async def _process_with_legacy(self, user_text: str) -> str:
        """使用舊版 Tool Calling 處理使用者輸入（降級模式）

        Args:
            user_text: 使用者輸入文字

        Returns:
            回應文字
        """
        logger.info("[Pipeline] 使用舊版 Tool Calling 處理")
        user_message = ChatMessage(role="user", content=user_text)
        messages = [user_message]

        # 取得工具定義和當前 system_prompt
        tools = self.tool_registry.get_openai_tools()
        system_prompt = self._get_current_system_prompt()

        # 第一次 LLM 呼叫
        llm_response = await self.llm_client.chat(
            messages, tools=tools, system_prompt=system_prompt
        )

        # 處理 Tool Calls（如果有）
        return await self._process_tool_calls(
            messages, llm_response, tools, system_prompt
        )

    def process_audio_with_outputs(
        self,
        audio: tuple[int, NDArray[np.float32]],
    ) -> Iterator[tuple[int, NDArray[np.float32]] | AdditionalOutputs]:
        """處理音訊輸入，回傳語音回應串流與 UI 更新

        這是支援 AdditionalOutputs 的 FastRTC handler，
        用於同步更新 Gradio UI 元件，並支援角色切換。

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
            logger.debug(f"[Pipeline] STT 結果: '{_truncate_for_log(user_text)}'")

            if not user_text.strip():
                # 無有效輸入，回到待命
                logger.info("[Pipeline] 無有效語音輸入，跳過")
                self.state.transition_to(VoiceState.IDLE)
                yield AdditionalOutputs(
                    self.state.get_gradio_messages(),
                    self.state.get_ui_state().status_text,
                )
                return

            # --------- 008: INTENT 辨識（角色切換） ---------
            if self.intent_recognizer is not None and self.role_registry is not None:
                try:
                    intent = _run_async_safely(
                        self.intent_recognizer.recognize_intent_with_llm(user_text)
                    )
                except Exception as e:
                    logger.error(f"[Pipeline] 辨識意圖失敗：{e}")
                    intent = None

                logger.debug(
                    f"[Intent] 輸入: user_text='{_truncate_for_log(user_text)}' "
                    f"intent={getattr(intent, 'name', None)} "
                    f"params={getattr(intent, 'params', None)}"
                )

                if (
                    intent is not None
                    and getattr(intent, "name", None) == "switch_role"
                    and hasattr(intent, "params")
                ):
                    logger.info("[Pipeline] 偵測到角色切換指令")
                    role_id = intent.params.get("role_id")

                    # 允許用 display_name（如「助理」）自動映射 ID
                    if role_id and role_id not in self.role_registry._roles:
                        mapped_id = self.role_registry.get_id_by_name(role_id)
                        if mapped_id:
                            logger.info(
                                f"[Pipeline] name→ID 映射: {role_id} -> {mapped_id}"
                            )
                            role_id = mapped_id

                    role = self.role_registry.get(role_id) if role_id else None

                    if role:
                        logger.info(
                            f"[Pipeline] 切換到角色: {getattr(role, 'name', role_id)}"
                        )
                        result = self.switch_role(role)

                        if result:
                            # 先嘗試抓角色的歡迎詞，有則優先用；沒有才 fallback
                            welcome_txt = (
                                role.get_welcome_message()
                                if hasattr(role, "get_welcome_message")
                                else None
                            )
                            if welcome_txt:
                                # TTS 播放原始歡迎語（無分隔符）
                                tts_txt = welcome_txt
                                # 對話框顯示時加入視覺分隔，提升辨識度
                                display_txt = f"---\n\n{welcome_txt}"
                                role_name = getattr(role, "name", "未知角色")
                                status_txt = f"🟢 已切換為『{role_name}』模式"
                            else:
                                role_name = getattr(role, "name", "未知角色")
                                tts_txt = f"已切換為『{role_name}』模式, 請繼續提問"
                                display_txt = (
                                    f"---\n\n已切換為『{role_name}』模式, 請繼續提問"
                                )
                                status_txt = f"🟢 已切換為『{role_name}』模式"
                        else:
                            tts_txt = (
                                self.state.last_assistant_text
                                or "角色設定異常，請確認後再試一次。"
                            )
                            display_txt = tts_txt
                            status_txt = f"⚠️ {tts_txt}"
                    else:
                        tts_txt = "查無此角色，請再說一次或從選單切換。"
                        display_txt = tts_txt
                        status_txt = f"⚠️ {tts_txt}"

                    # 播放 TTS 確認訊息（使用無分隔符版本）
                    for audio_chunk in self.tts.stream_tts_sync(tts_txt):
                        yield audio_chunk

                    self.state.last_assistant_text = display_txt
                    self.state.history.add_assistant_message(display_txt)
                    self.state.transition_to(VoiceState.IDLE)
                    yield AdditionalOutputs(
                        self.state.get_gradio_messages(), status_txt
                    )
                    logger.debug("[Pipeline] 角色切換完成，結束處理")
                    return

                # 不是 switch_role intent 時，進入主流程處理
                logger.info("[Pipeline] 進入一般對話流程")

            # T013: STT 完成後更新 history
            self.state.last_user_text = user_text
            self.state.history.add_user_message(user_text)
            self.state.transition_to(VoiceState.PROCESSING)

            # 發送 UI 更新：使用者訊息已加入
            yield AdditionalOutputs(
                self.state.get_gradio_messages(),
                self.state.get_ui_state().status_text,
            )

            # 2. 根據 flow_mode 處理輸入
            logger.debug(f"[Pipeline] 處理輸入: '{_truncate_for_log(user_text)}'")

            # 決定有效的流程模式（角色專屬 > 全域設定）
            effective_flow_mode = self.flow_mode  # 預設使用全域設定
            if self.role_registry and self.state.current_role_id:
                current_role = self.role_registry.get(self.state.current_role_id)
                if (
                    current_role
                    and hasattr(current_role, "preferred_flow_mode")
                    and current_role.preferred_flow_mode
                ):
                    effective_flow_mode = FlowMode(current_role.preferred_flow_mode)
                    logger.info(
                        f"[Pipeline] 使用角色專屬流程模式: {effective_flow_mode.value}"
                    )
                else:
                    logger.info(
                        f"[Pipeline] 使用全域流程模式: {effective_flow_mode.value}"
                    )
            else:
                logger.info(f"[Pipeline] 使用全域流程模式: {effective_flow_mode.value}")

            if effective_flow_mode == FlowMode.MULTI_AGENT:
                # 使用 Multi-Agent 流程
                response = _run_async_safely(self._process_with_multi_agent(user_text))
            elif effective_flow_mode == FlowMode.LANGGRAPH:
                # 使用 LangGraph 流程
                response = _run_async_safely(self._process_with_flow(user_text))
            else:
                # FlowMode.TOOLS - 使用純 Tool Calling
                response = _run_async_safely(self._process_with_legacy(user_text))

            logger.debug(f"[Pipeline] 回應: '{_truncate_for_log(response)}'")

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
