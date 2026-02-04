"""
整合測試：UI 角色切換狀態同步
情境：用戶操作下拉選單時，callback 被呼叫、狀態 textbox UI 隨之更新。
"""

import importlib
from unittest.mock import Mock, patch

import pytest

role_selector_mod = importlib.import_module("src.voice_assistant.ui.role_selector")


@pytest.fixture
def dummy_roles():
    # {'id': '顯示名稱'}
    return {"user": "用戶", "assistant": "助理", "admin": "管理員"}


def test_role_switch_interaction(dummy_roles):
    callback_hits = []

    def fake_on_role_change(new_role_id):
        callback_hits.append(new_role_id)

    # patch gradio 元件
    with (
        patch("src.voice_assistant.ui.role_selector.gr.Dropdown") as MDropdown,
        patch("src.voice_assistant.ui.role_selector.gr.Textbox") as MTextbox,
    ):
        dd_inst = Mock()
        tb_inst = Mock()
        # 令 gr.Textbox.value 存初始文字 & 設定 set_text 模擬 UI 更新
        tb_inst.value = f"目前角色：{dummy_roles['user']}"

        def set_status_text(val):
            tb_inst.value = val

        tb_inst.set_text = set_status_text
        MDropdown.return_value = dd_inst
        MTextbox.return_value = tb_inst
        # 實例化 UI
        dd, tb = role_selector_mod.create_role_selector_with_status(
            available_roles=dummy_roles,
            on_role_change=fake_on_role_change,
            current_role_id="user",
            label="切換角色",
        )
        # 用戶於下拉選單操作切換
        cb = dd.change.call_args.args[0]  # 取得 callback glue
        # 切換到 assistant
        status1 = cb("assistant")
        # 狀態框內容會變
        assert "助理" in status1
        # callback 被呼叫
        assert callback_hits[-1] == "assistant"
        # 再切 admin
        status2 = cb("admin")
        assert "管理員" in status2
        assert callback_hits[-1] == "admin"
        # 切到不存在的 id，狀態不變
        status3 = cb("ghost")
        # 允許 fallback 狀態文本為 "目前角色：" 開頭即可
        assert status3.startswith("目前角色：")
