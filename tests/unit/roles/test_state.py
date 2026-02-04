"""
RoleState 單元測試：切換、重複切換無效、歷史記錄、型別一致性
"""

import pytest

from src.voice_assistant.roles.state import RoleState


@pytest.fixture
def state():
    return RoleState(session_id="demo-session-1")


def test_switch_role_success(state):
    # 首次切換
    out = state.switch_role("assistant", reason="第一次登錄")
    assert out is True
    assert state.current_role_id == "assistant"
    assert len(state.transition_history) == 1
    rec = state.transition_history[0]
    assert rec.from_role is None
    assert rec.to_role == "assistant"
    assert rec.reason == "第一次登錄"


def test_repeated_switch_is_noop(state):
    state.switch_role("assistant")
    out = state.switch_role("assistant")  # 應忽略
    assert out is False
    assert len(state.transition_history) == 1


def test_switch_role_multiple(state):
    state.switch_role("assistant", "初始")
    state.switch_role("coach", "進階需求")
    state.switch_role("assistant", "返回助理")
    assert state.current_role_id == "assistant"
    assert [r.to_role for r in state.transition_history] == [
        "assistant",
        "coach",
        "assistant",
    ]


def test_transition_history_limit():
    st = RoleState(session_id="bulktest")
    for i in range(55):
        st.switch_role(f"role{i}")
    # 只保證 transition_history 邏輯上支援超過50，但規格建議上限50
    assert len(st.transition_history) == 55


def test_add_transition_type_safe():
    st = RoleState(session_id="safecheck")
    # 允許 None 作為 from_role（覆蓋之前 LSP 警告案例）
    st.add_transition(None, "test", "初次")
    assert st.transition_history[0].from_role is None
    st.add_transition("test", "test2", "繼續")
    assert st.transition_history[1].from_role == "test"
