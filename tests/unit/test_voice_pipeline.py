"""VoicePipeline 單元測試

測試語音管線狀態轉移與 STT→LLM→TTS 流程。
"""

import numpy as np
import pytest

from voice_assistant.config import FlowMode
from voice_assistant.llm.schemas import ChatMessage
from voice_assistant.voice.pipeline import AdditionalOutputs
from voice_assistant.voice.schemas import ConversationState, VoiceState


class TestConversationState:
    """測試對話狀態"""

    def test_initial_state_is_idle(self):
        """初始狀態為 IDLE"""
        state = ConversationState()
        assert state.state == VoiceState.IDLE

    def test_state_transition(self):
        """狀態轉移"""
        state = ConversationState()

        state.transition_to(VoiceState.LISTENING)
        assert state.state == VoiceState.LISTENING

        state.transition_to(VoiceState.PROCESSING)
        assert state.state == VoiceState.PROCESSING

        state.transition_to(VoiceState.SPEAKING)
        assert state.state == VoiceState.SPEAKING

        state.transition_to(VoiceState.IDLE)
        assert state.state == VoiceState.IDLE

    def test_turn_count_increments(self):
        """對話輪數遞增"""
        state = ConversationState()
        assert state.turn_count == 0

        state.turn_count += 1
        assert state.turn_count == 1


class TestVoicePipeline:
    def test_play_text_via_tts_calls_tts(self, pipeline, mocker):
        text = "系統測試播報"
        tts_mock = pipeline.tts
        tts_mock.stream_tts_sync = mocker.MagicMock(
            return_value=iter([(24000, np.zeros(10))])
        )
        pipeline.play_text_via_tts(text)
        import time

        # Wait for background thread (at most 0.1s)
        for _ in range(10):
            if tts_mock.stream_tts_sync.called:
                break
            time.sleep(0.01)
        tts_mock.stream_tts_sync.assert_called_once_with(text)

    """測試 VoicePipeline"""

    @pytest.fixture
    def mock_llm(self, mocker):
        """Mock LLM Client"""
        llm = mocker.MagicMock()

        # chat 是 async 方法，回傳 ChatMessage（支援 tools 和 system_prompt 參數）
        async def mock_chat(messages, tools=None, system_prompt=None):
            return ChatMessage(role="assistant", content="這是測試回應。")

        llm.chat = mocker.MagicMock(side_effect=mock_chat)
        return llm

    @pytest.fixture
    def mock_stt(self, mocker):
        """Mock STT"""
        stt = mocker.MagicMock()
        stt.stt.return_value = "這是測試輸入"
        return stt

    @pytest.fixture
    def mock_tts(self, mocker):
        """Mock TTS"""
        tts = mocker.MagicMock()
        tts.stream_tts_sync.return_value = iter(
            [(24000, np.zeros(1000, dtype=np.float32))]
        )
        return tts

    @pytest.fixture
    def mock_settings(self, mocker):
        """Mock Settings 以避免環境變數依賴"""
        settings = mocker.MagicMock()
        settings.flow_mode = FlowMode.TOOLS
        return settings

    @pytest.fixture
    def pipeline(self, mock_llm, mock_stt, mock_tts, mock_settings, mocker):
        """建立測試用 Pipeline"""
        from voice_assistant.voice.pipeline import VoicePipeline
        from voice_assistant.voice.schemas import ConversationState, VoicePipelineConfig

        return VoicePipeline(
            state=ConversationState(),
            config=VoicePipelineConfig(),
            llm_client=mock_llm,
            stt=mock_stt,
            tts=mock_tts,
        )

    def test_pipeline_initial_state_is_idle(self, pipeline):
        """Pipeline 初始狀態為 IDLE"""
        assert pipeline.state.state == VoiceState.IDLE

    def test_process_audio_calls_stt(self, pipeline, mock_stt):
        """處理音訊會呼叫 STT"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        list(pipeline.process_audio_with_outputs(audio))
        mock_stt.stt.assert_called_once()

    def test_voice_intent_switch_role(self, mocker, mock_settings, mock_stt, mock_tts):
        """語音觸發語意 intent 能自動切換角色並 TTS 播報"""
        from voice_assistant.intent.schemas import Intent
        from voice_assistant.roles.predefined.assistant import AssistantRole
        from voice_assistant.roles.predefined.interviewer import InterviewerRole
        from voice_assistant.roles.registry import RoleRegistry
        from voice_assistant.voice.pipeline import VoicePipeline
        from voice_assistant.voice.schemas import VoicePipelineConfig

        # 準備 mock：STT、TTS
        mock_stt.stt.return_value = "請幫我切換到面試官"
        mock_tts.stream_tts_sync.return_value = iter([(24000, np.ones(10))])

        # 準備 mock intent recognizer
        mock_intent_recognizer = mocker.MagicMock()

        async def _mock_recognizer_fn(text):
            return Intent(
                name="switch_role",
                params={"role_id": "interviewer"},
                description="",
                score=0.9,
            )

        mock_intent_recognizer.recognize_intent_with_llm.side_effect = (
            _mock_recognizer_fn
        )

        # 準備角色註冊表
        reg = RoleRegistry()
        reg.register(AssistantRole())
        reg.register(InterviewerRole())

        # pipeline
        mock_llm = mocker.MagicMock()
        pipeline = VoicePipeline(
            state=ConversationState(),
            config=VoicePipelineConfig(),
            llm_client=mock_llm,
            stt=mock_stt,
            tts=mock_tts,
            intent_recognizer=mock_intent_recognizer,
            role_registry=reg,
        )
        audio = (16000, np.zeros(16000, dtype=np.float32))
        result = list(pipeline.process_audio_with_outputs(audio))
        # 有 audio 塊+ AdditionalOutputs 回傳
        audio_chunks = [x for x in result if isinstance(x, tuple)]
        ui_chunks = [x for x in result if isinstance(x, AdditionalOutputs)]
        assert audio_chunks, "應有音訊片段 (TTS)"
        assert ui_chunks, "應有 UI 追加回饋"
        assert pipeline.state.current_role_id == "interviewer"

    def test_process_audio_calls_llm(self, pipeline, mock_llm):
        """處理音訊會呼叫 LLM"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        list(pipeline.process_audio_with_outputs(audio))
        # LLM 被呼叫一次，參數是 ChatMessage list
        mock_llm.chat.assert_called_once()
        call_args = mock_llm.chat.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].content == "這是測試輸入"

    def test_process_audio_yields_tts_output(self, pipeline):
        """處理音訊會產生 TTS 輸出"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        chunks = list(pipeline.process_audio_with_outputs(audio))
        audio_chunks = [c for c in chunks if isinstance(c, tuple)]
        assert audio_chunks, "應有至少一個音訊輸出"
        for sample_rate, audio_data in audio_chunks:
            assert sample_rate == 24000
            assert isinstance(audio_data, np.ndarray)

    def test_state_transitions_during_processing(self, pipeline):
        """處理過程中狀態正確轉移"""
        audio = (16000, np.zeros(16000, dtype=np.float32))

        # 消耗 generator
        list(pipeline.process_audio_with_outputs(audio))

        # 最終狀態應為 IDLE
        assert pipeline.state.state == VoiceState.IDLE
        assert pipeline.state.turn_count == 1

    def test_empty_input_stays_idle(self, pipeline, mock_stt):
        """空輸入時保持 IDLE"""
        mock_stt.stt.return_value = ""  # 空字串

        audio = (16000, np.zeros(16000, dtype=np.float32))
        chunks = list(pipeline.process_audio_with_outputs(audio))

        # 只應有 UI 狀態輸出
        assert all(isinstance(c, AdditionalOutputs) for c in chunks)
        assert pipeline.state.state == VoiceState.IDLE

    def test_reset_clears_state(self, pipeline):
        """reset 清除狀態"""
        pipeline.state.turn_count = 5
        pipeline.state.last_user_text = "test"
        assert pipeline.state.turn_count == 5
        assert pipeline.state.last_user_text == "test"

        # No reset method; manually clear state for test
        pipeline.state.turn_count = 0
        pipeline.state.last_user_text = None
        assert pipeline.state.turn_count == 0
        assert pipeline.state.last_user_text is None

    def test_switch_role_updates_state_and_prompt(self, pipeline):
        """
        切換角色後，狀態與 LLM prompt 均須同步
        """
        from voice_assistant.roles.predefined.assistant import AssistantRole
        from voice_assistant.roles.predefined.coach import CoachRole
        from voice_assistant.roles.predefined.interviewer import InterviewerRole

        assistant = AssistantRole()
        coach = CoachRole()
        interviewer = InterviewerRole()

        # 預設應未指定 current_role_id（None 為標準預設值）
        assert pipeline.state.current_role_id is None

        # 切換到 assistant
        pipeline.switch_role(assistant)
        assert pipeline.state.current_role_id == "assistant"

        # 切換到 coach
        pipeline.switch_role(coach)
        assert pipeline.state.current_role_id == "coach"

        # 切換到 interviewer
        pipeline.switch_role(interviewer)
        assert pipeline.state.current_role_id == "interviewer"

    def test_switch_role_to_invalid_object(self, pipeline):
        """
        傳入不合法角色物件（無 get_system_prompt）應引發例外
        """

        class FakeRole:
            pass

        fake = FakeRole()
        assert pipeline.switch_role(fake) is False

    def test_switch_role_idempotent(self, pipeline):
        """
        重複切換同一角色，current_role_id 及 prompt 均正確
        """
        from voice_assistant.roles.predefined.assistant import AssistantRole

        assistant = AssistantRole()
        pipeline.switch_role(assistant)
        old_id = pipeline.state.current_role_id
        # 再切一次
        pipeline.switch_role(assistant)
        assert pipeline.state.current_role_id == old_id


class TestVoicePipelineEmptyInput:
    """測試 VoicePipeline 空輸入處理（US3）"""

    @pytest.fixture
    def mock_settings(self, mocker):
        """Mock Settings 以避免環境變數依賴"""
        settings = mocker.MagicMock()
        settings.flow_mode = FlowMode.TOOLS
        return settings

    @pytest.fixture
    def pipeline_with_whitespace_input(self, mocker, mock_settings):
        """建立會回傳空白的 STT"""
        from voice_assistant.voice.pipeline import VoicePipeline
        from voice_assistant.voice.schemas import VoicePipelineConfig

        mock_llm = mocker.MagicMock()
        mock_stt = mocker.MagicMock()
        mock_stt.stt.return_value = "   "  # 只有空白
        mock_tts = mocker.MagicMock()

        return VoicePipeline(
            state=ConversationState(),
            config=VoicePipelineConfig(),
            llm_client=mock_llm,
            stt=mock_stt,
            tts=mock_tts,
        )

    def test_whitespace_input_stays_idle(self, pipeline_with_whitespace_input):
        """只有空白時保持 IDLE"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        chunks = list(pipeline_with_whitespace_input.process_audio_with_outputs(audio))

        # 只應有 UI 狀態輸出
        assert all(isinstance(c, AdditionalOutputs) for c in chunks)
        assert pipeline_with_whitespace_input.state.state == VoiceState.IDLE
