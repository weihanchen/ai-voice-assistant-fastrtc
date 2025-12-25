"""VoicePipeline 單元測試

測試語音管線狀態轉移與 STT→LLM→TTS 流程。
"""

import numpy as np
import pytest

from voice_assistant.llm.schemas import ChatMessage
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
    def pipeline(self, mock_llm, mock_stt, mock_tts):
        """建立測試用 Pipeline"""
        from voice_assistant.voice.pipeline import VoicePipeline
        from voice_assistant.voice.schemas import VoicePipelineConfig

        return VoicePipeline(
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
        list(pipeline.process_audio(audio))
        mock_stt.stt.assert_called_once()

    def test_process_audio_calls_llm(self, pipeline, mock_llm):
        """處理音訊會呼叫 LLM"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        list(pipeline.process_audio(audio))
        # LLM 被呼叫一次，參數是 ChatMessage list
        mock_llm.chat.assert_called_once()
        call_args = mock_llm.chat.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].content == "這是測試輸入"

    def test_process_audio_yields_tts_output(self, pipeline):
        """處理音訊會產生 TTS 輸出"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        chunks = list(pipeline.process_audio(audio))
        assert len(chunks) == 1
        sample_rate, audio_data = chunks[0]
        assert sample_rate == 24000
        assert isinstance(audio_data, np.ndarray)

    def test_state_transitions_during_processing(self, pipeline):
        """處理過程中狀態正確轉移"""
        audio = (16000, np.zeros(16000, dtype=np.float32))

        # 消耗 generator
        list(pipeline.process_audio(audio))

        # 最終狀態應為 IDLE
        assert pipeline.state.state == VoiceState.IDLE
        assert pipeline.state.turn_count == 1

    def test_empty_input_stays_idle(self, pipeline, mock_stt):
        """空輸入時保持 IDLE"""
        mock_stt.stt.return_value = ""  # 空字串

        audio = (16000, np.zeros(16000, dtype=np.float32))
        chunks = list(pipeline.process_audio(audio))

        # 不應有輸出
        assert len(chunks) == 0
        assert pipeline.state.state == VoiceState.IDLE

    def test_reset_clears_state(self, pipeline):
        """reset 清除狀態"""
        pipeline.state.turn_count = 5
        pipeline.state.last_user_text = "test"

        pipeline.reset()

        assert pipeline.state.turn_count == 0
        assert pipeline.state.last_user_text is None


class TestVoicePipelineInterrupt:
    """測試 VoicePipeline 中斷功能（US2）"""

    @pytest.fixture
    def pipeline_speaking(self, mocker):
        """建立正在說話的 Pipeline"""
        from voice_assistant.voice.pipeline import VoicePipeline
        from voice_assistant.voice.schemas import VoicePipelineConfig

        mock_llm = mocker.MagicMock()
        mock_stt = mocker.MagicMock()
        mock_tts = mocker.MagicMock()

        pipeline = VoicePipeline(
            config=VoicePipelineConfig(),
            llm_client=mock_llm,
            stt=mock_stt,
            tts=mock_tts,
        )
        # 模擬正在說話
        pipeline.state.transition_to(VoiceState.SPEAKING)
        return pipeline

    def test_on_interrupt_transitions_to_interrupted(self, pipeline_speaking):
        """中斷時轉移到 INTERRUPTED 狀態"""
        pipeline_speaking.on_interrupt()
        assert pipeline_speaking.state.state == VoiceState.INTERRUPTED

    def test_on_interrupt_only_when_speaking(self, mocker):
        """只有在 SPEAKING 時才能中斷"""
        from voice_assistant.voice.pipeline import VoicePipeline
        from voice_assistant.voice.schemas import VoicePipelineConfig

        mock_llm = mocker.MagicMock()
        mock_stt = mocker.MagicMock()
        mock_tts = mocker.MagicMock()

        pipeline = VoicePipeline(
            config=VoicePipelineConfig(),
            llm_client=mock_llm,
            stt=mock_stt,
            tts=mock_tts,
        )
        # IDLE 狀態時呼叫 on_interrupt 不應改變狀態
        pipeline.on_interrupt()
        assert pipeline.state.state == VoiceState.IDLE


class TestVoicePipelineEmptyInput:
    """測試 VoicePipeline 空輸入處理（US3）"""

    @pytest.fixture
    def pipeline_with_whitespace_input(self, mocker):
        """建立會回傳空白的 STT"""
        from voice_assistant.voice.pipeline import VoicePipeline
        from voice_assistant.voice.schemas import VoicePipelineConfig

        mock_llm = mocker.MagicMock()
        mock_stt = mocker.MagicMock()
        mock_stt.stt.return_value = "   "  # 只有空白
        mock_tts = mocker.MagicMock()

        return VoicePipeline(
            config=VoicePipelineConfig(),
            llm_client=mock_llm,
            stt=mock_stt,
            tts=mock_tts,
        )

    def test_whitespace_input_stays_idle(self, pipeline_with_whitespace_input):
        """只有空白時保持 IDLE"""
        audio = (16000, np.zeros(16000, dtype=np.float32))
        chunks = list(pipeline_with_whitespace_input.process_audio(audio))

        assert len(chunks) == 0
        assert pipeline_with_whitespace_input.state.state == VoiceState.IDLE
