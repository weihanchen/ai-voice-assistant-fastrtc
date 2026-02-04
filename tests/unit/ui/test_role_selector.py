"""
單元測試：role_selector.py

涵蓋:
- Dropdown／Textbox UI 構造正確
- options、預設選取、callback glue
- （無需實際渲染，mock Gradio 元件）
"""

import importlib
from unittest.mock import Mock, patch

import pytest

role_selector_mod = importlib.import_module("src.voice_assistant.ui.role_selector")


@pytest.fixture
def dummy_roles():
    # {'id': '顯示名稱'}
    return {"user": "用戶", "assistant": "助理", "admin": "管理員"}


def test_create_role_selector_basic(dummy_roles):
    mock_cb = Mock()
    with patch("src.voice_assistant.ui.role_selector.gr.Dropdown") as MDropdown:
        # 配置 Dropdown mock 返回自身
        dd_inst = Mock()
        MDropdown.return_value = dd_inst

        dd = role_selector_mod.create_role_selector(
            available_roles=dummy_roles,
            on_role_change=mock_cb,
            current_role_id="assistant",
            label="測試角色：",
        )
        # choices、value、label 應正確設置
        MDropdown.assert_called_once()
        called_kwargs = MDropdown.call_args.kwargs
        # create_role_selector 只傳遞 keys（不是 tuple 格式）
        assert set(called_kwargs["choices"]) == set(dummy_roles.keys())
        assert called_kwargs["value"] == "assistant"
        assert called_kwargs["label"] == "測試角色："

        # 測試 callback glue
        dd.change.assert_called_once()  # 有安裝 callback
        # 測試 callback function signature
        cb = dd.change.call_args.args[0]
        cb("admin")
        mock_cb.assert_called_with("admin")


def test_create_role_selector_with_status(dummy_roles):
    mock_cb = Mock()
    with (
        patch("src.voice_assistant.ui.role_selector.gr.Dropdown") as MDropdown,
        patch("src.voice_assistant.ui.role_selector.gr.Textbox") as MTextbox,
    ):
        dd_inst = Mock()
        tb_inst = Mock()
        MDropdown.return_value = dd_inst
        MTextbox.return_value = tb_inst

        dd, tb = role_selector_mod.create_role_selector_with_status(
            available_roles=dummy_roles,
            on_role_change=mock_cb,
            current_role_id=None,
            label="選角",
        )
        # choices 為所有角色 id/name
        MDropdown.assert_called_once()
        called_kw = MDropdown.call_args.kwargs
        assert set([o[0] for o in called_kw["choices"]]) == set(dummy_roles.keys())
        # 預設應選第 1 個
        assert called_kw["value"] == next(iter(dummy_roles.keys()))
        # status Textbox 應設正確
        MTextbox.assert_called_once()
        st_kw = MTextbox.call_args.kwargs
        assert st_kw["value"] in [f"目前角色：{v}" for v in dummy_roles.values()]
        assert st_kw["interactive"] is False
        # 測試 dropdown.change glue 可改 textbox
        cb = dd.change.call_args.args[0]
        # status 應根據切換角色內容變動
        val = cb("admin")
        assert "管理員" in val
        mock_cb.assert_called_with("admin")
