"""流程視覺化 UI 元件測試

測試 create_flow_visualization、update_flow_visualization
與 additional_outputs_handler。
"""

import gradio as gr

from voice_assistant.voice.ui.blocks import (
    _EMPTY_FLOW_HTML,
    _MERMAID_HTML_TEMPLATE,
    additional_outputs_handler,
    create_flow_visualization,
    update_flow_visualization,
)


class TestCreateFlowVisualization:
    """測試 create_flow_visualization"""

    def test_returns_gr_html(self):
        """回傳 gr.HTML 元件"""
        component = create_flow_visualization()
        assert isinstance(component, gr.HTML)

    def test_default_value_is_empty_state(self):
        """預設值為空狀態 HTML"""
        component = create_flow_visualization()
        assert component.value == _EMPTY_FLOW_HTML

    def test_has_label(self):
        """元件有標籤"""
        component = create_flow_visualization()
        assert component.label == "流程圖"


class TestUpdateFlowVisualization:
    """測試 update_flow_visualization"""

    def test_none_returns_empty_html(self):
        """mermaid_code 為 None 時回傳空狀態 HTML"""
        result = update_flow_visualization(None)
        assert result == _EMPTY_FLOW_HTML

    def test_empty_string_returns_empty_html(self):
        """mermaid_code 為空字串時回傳空狀態 HTML"""
        result = update_flow_visualization("")
        assert result == _EMPTY_FLOW_HTML

    def test_valid_mermaid_code_returns_html_with_mermaid(self):
        """有效的 mermaid_code 會嵌入 HTML 模板"""
        mermaid_code = "graph TD\n    A[Start] --> B[End]"
        result = update_flow_visualization(mermaid_code)

        assert "mermaid" in result
        assert mermaid_code in result
        assert "<iframe" in result

    def test_html_contains_mermaid_js_cdn(self):
        """HTML 包含 mermaid.js CDN"""
        result = update_flow_visualization("graph TD\n    A --> B")
        assert "cdn.jsdelivr.net/npm/mermaid" in result

    def test_html_contains_css_classes(self):
        """HTML 包含節點狀態 CSS 類別"""
        result = update_flow_visualization("graph TD\n    A --> B")
        assert ".node.running" in result
        assert ".node.completed" in result
        assert ".node.failed" in result
        assert ".node.pending" in result

    def test_template_format(self):
        """模板格式正確（mermaid_code 被正確插入）"""
        code = "graph LR\n    X[Hello] --> Y[World]"
        result = update_flow_visualization(code)
        # update_flow_visualization 會跳脫單引號後再嵌入模板
        safe_code = code.replace("'", "&#39;")
        expected = _MERMAID_HTML_TEMPLATE.format(mermaid_code=safe_code)
        assert result == expected


class TestAdditionalOutputsHandler:
    """測試 additional_outputs_handler（3 輸出模式）"""

    def test_returns_new_values(self):
        """正常情況下回傳新的值"""
        old_chatbot = [{"role": "user", "content": "舊訊息"}]
        old_status = "🟢 待命"
        old_flow_viz = "<div>舊流程圖</div>"
        new_history = [
            {"role": "user", "content": "舊訊息"},
            {"role": "assistant", "content": "新回應"},
        ]
        new_status = "🔵 處理中"
        new_flow_viz = "<div>新流程圖</div>"

        result = additional_outputs_handler(
            old_chatbot,
            old_status,
            old_flow_viz,
            new_history,
            new_status,
            new_flow_viz,
        )

        assert result == (new_history, new_status, new_flow_viz)

    def test_returns_tuple_of_three(self):
        """回傳值為 3 元素 tuple"""
        result = additional_outputs_handler(
            [],
            "old",
            "<div>old</div>",
            [{"role": "user", "content": "hi"}],
            "new",
            "<div>new</div>",
        )
        assert len(result) == 3

    def test_empty_inputs(self):
        """空輸入時正常運作"""
        result = additional_outputs_handler(
            [],
            "",
            "",
            [],
            "",
            "",
        )
        assert result == ([], "", "")

    def test_flow_viz_html_passed_through(self):
        """flow_viz HTML 被正確傳遞"""
        flow_html = update_flow_visualization("graph TD\n    A --> B")
        result = additional_outputs_handler(
            [],
            "",
            "",
            [],
            "🟢",
            flow_html,
        )
        assert result[2] == flow_html
        assert "mermaid" in result[2]
