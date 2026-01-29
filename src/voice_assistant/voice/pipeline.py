import logging
from collections.abc import Iterator

from fastrtc import AdditionalOutputs
from numpy.typing import NDArray

from voice_assistant.voice.schemas import VoiceState

logger = logging.getLogger(__name__)


class VoicePipeline:
    def __init__(
        self,
        state,
        stt,
        tts,
        intent_recognizer=None,
        role_registry=None,
        config=None,
        llm_client=None,
        tool_registry=None,
    ):
        self.state = state
        self.stt = stt
        self.tts = tts
        self.intent_recognizer = intent_recognizer
        self.role_registry = role_registry
        self.config = config
        self.llm_client = llm_client
        self.tool_registry = tool_registry

    def switch_role(self, role):
        if not role or not hasattr(role, "id"):
            return False
        self.state.current_role_id = role.id
        return True

    def process_audio_with_outputs(
        self, audio: tuple[int, NDArray]
    ) -> Iterator[tuple[int, NDArray] | AdditionalOutputs]:
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
            logger.debug(f"[Pipeline] STT 結果: '{user_text}'")
            if not user_text.strip():
                # 無有效語音輸入，回到待命
                logger.info("[Pipeline] 無有效語音輸入，跳過")
                self.state.transition_to(VoiceState.IDLE)
                yield AdditionalOutputs(
                    self.state.get_gradio_messages(),
                    self.state.get_ui_state().status_text,
                )
                logger.debug("[Pipeline] generator exit: no valid STT input")
                return
            # --------- INTENT 辨識（如支援） ---------
            if self.intent_recognizer is not None and self.role_registry is not None:
                import asyncio

                try:
                    intent = asyncio.run(
                        self.intent_recognizer.recognize_intent_with_llm(user_text)
                    )
                except Exception as e:
                    logger.error(f"[Pipeline] 辨識意圖失敗：{e}")
                    intent = None
                logger.critical(
                    f"[Intent偵錯] 輸入: user_text='{user_text}' "
                    f"intent={getattr(intent, 'name', None)} "
                    f"params={getattr(intent, 'params', None)}"
                )
                if (
                    intent is not None
                    and getattr(intent, "name", None) == "switch_role"
                    and hasattr(intent, "params")
                ):
                    logger.info("[Pipeline] Triggering role switch branch...")
                    role_id = intent.params.get("role_id")
                    # 新增：允許用 display_name（如「助理」）自動映射 ID
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
                            f"[Pipeline] Switching to role: "
                            f"{getattr(role, 'name', role_id)}"
                        )
                        result = self.switch_role(role)
                        if result:
                            role_name = getattr(role, "name", "未知角色")
                            reply_txt = f"已切換為『{role_name}』模式, 請繼續提問"
                            status_txt = f"🟢 {reply_txt}"
                        else:
                            reply_txt = (
                                self.state.last_assistant_text
                                or "角色設定異常，請確認後再試一次。"
                            )
                            status_txt = f"⚠️ {reply_txt}"
                    else:
                        reply_txt = "查無此角色，請再說一次或從選單切換。"
                        status_txt = f"⚠️ {reply_txt}"
                    for audio_chunk in self.tts.stream_tts_sync(reply_txt):
                        yield audio_chunk
                    self.state.last_assistant_text = reply_txt
                    self.state.history.add_assistant_message(reply_txt)
                    self.state.transition_to(VoiceState.IDLE)
                    yield AdditionalOutputs(
                        self.state.get_gradio_messages(), status_txt
                    )
                    logger.debug(
                        "[Pipeline] generator exit: role switch intent handled"
                    )
                    return
                # 不是 switch_role intent 時，進入主流程處理
                logger.info("[Pipeline] Normal conversation branch.")

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
            logger.debug(f"[Pipeline] 處理輸入: '{user_text}'")
            import asyncio

            from voice_assistant.llm.schemas import ChatMessage

            if self.llm_client:
                messages = [ChatMessage(role="user", content=user_text)]

                # 取得當前角色的 system_prompt
                current_system_prompt = None
                if self.role_registry and self.state.current_role_id:
                    try:
                        current_role = self.role_registry.get(
                            self.state.current_role_id
                        )
                        current_system_prompt = current_role.system_prompt
                        logger.debug(
                            f"[Pipeline] 使用角色 {current_role.name} 的 system_prompt"
                        )
                    except Exception as e:
                        logger.warning(
                            f"[Pipeline] 無法取得當前角色的 system_prompt: {e}"
                        )

                try:
                    response_msg = asyncio.run(
                        self.llm_client.chat(
                            messages,
                            tools=self.tool_registry.get_openai_tools()
                            if self.tool_registry
                            else None,
                            system_prompt=current_system_prompt,
                        )
                    )
                    response = response_msg.content or ""
                except Exception as e:
                    logger.error(f"LLM 回應失敗: {e}")
                    response = "（系統）語言模型回應失敗。"
            else:
                response = "（系統）未設定 LLM Client，無法回應。"

            # 防禦性檢查：確保回應不為空
            if not response or not response.strip():
                logger.warning("[Pipeline] LLM 回應為空，使用預設訊息")
                response = "抱歉，我暫時無法回應。請再說一次。"

            logger.debug(f"[Pipeline] 回應: '{response}'")
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
                    self.config
                    and self.config.can_interrupt
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
                return
            else:
                logger.info(f"[Pipeline] TTS 完成，共 {chunk_count} 個音訊片段")
            # 5. 回應完成，回到待命
            self.state.transition_to(VoiceState.IDLE)
            yield AdditionalOutputs(
                self.state.get_gradio_messages(),
                self.state.get_ui_state().status_text,
            )
            return
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
                return
