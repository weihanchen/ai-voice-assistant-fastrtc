"""流程視覺化單元測試。"""

from __future__ import annotations

from voice_assistant.flows.visualization import (
    FlowVisualization,
    NodeStatus,
    apply_node_labels,
    render_mermaid_with_status,
)


class TestNodeStatus:
    """測試 NodeStatus 列舉。"""

    def test_has_four_statuses(self) -> None:
        """NodeStatus 有四種狀態。"""
        assert len(NodeStatus) == 4

    def test_status_values(self) -> None:
        """NodeStatus 的值正確。"""
        assert NodeStatus.PENDING.value == "pending"
        assert NodeStatus.RUNNING.value == "running"
        assert NodeStatus.COMPLETED.value == "completed"
        assert NodeStatus.FAILED.value == "failed"


class TestFlowVisualization:
    """測試 FlowVisualization Pydantic 模型。"""

    def test_create_with_defaults(self) -> None:
        """建立預設的 FlowVisualization。"""
        viz = FlowVisualization(mermaid_code="graph TD\nA-->B")
        assert viz.mermaid_code == "graph TD\nA-->B"
        assert viz.node_statuses == {}

    def test_create_with_statuses(self) -> None:
        """建立含狀態的 FlowVisualization。"""
        statuses = {
            "A": NodeStatus.COMPLETED,
            "B": NodeStatus.RUNNING,
        }
        viz = FlowVisualization(
            mermaid_code="graph TD\nA-->B",
            node_statuses=statuses,
        )
        assert viz.node_statuses["A"] == NodeStatus.COMPLETED
        assert viz.node_statuses["B"] == NodeStatus.RUNNING

    def test_serialization(self) -> None:
        """FlowVisualization 可正確序列化。"""
        viz = FlowVisualization(
            mermaid_code="graph TD",
            node_statuses={"node1": NodeStatus.PENDING},
        )
        data = viz.model_dump()
        assert data["mermaid_code"] == "graph TD"
        assert data["node_statuses"]["node1"] == "pending"


class TestRenderMermaidWithStatus:
    """測試 render_mermaid_with_status() 函式。"""

    def test_empty_statuses_returns_original(self) -> None:
        """空 node_statuses 時回傳原始 Mermaid。"""
        mermaid = "graph TD\nA[Start]-->B[End]"
        result = render_mermaid_with_status(mermaid, {})
        assert result == mermaid

    def test_none_statuses_returns_original(self) -> None:
        """None node_statuses 時回傳原始 Mermaid。"""
        mermaid = "graph TD\nA[Start]-->B[End]"
        result = render_mermaid_with_status(mermaid, None)
        assert result == mermaid

    def test_injects_running_class(self) -> None:
        """注入 running CSS class。"""
        mermaid = "graph TD\nA[Start]-->B[Process]-->C[End]"
        statuses = {"B": NodeStatus.RUNNING}
        result = render_mermaid_with_status(mermaid, statuses)
        assert "B[Process]:::running" in result

    def test_injects_completed_class(self) -> None:
        """注入 completed CSS class。"""
        mermaid = "graph TD\nA[Start]-->B[End]"
        statuses = {"A": NodeStatus.COMPLETED}
        result = render_mermaid_with_status(mermaid, statuses)
        assert "A[Start]:::completed" in result

    def test_injects_failed_class(self) -> None:
        """注入 failed CSS class。"""
        mermaid = "graph TD\nA[Start]-->B[End]"
        statuses = {"B": NodeStatus.FAILED}
        result = render_mermaid_with_status(mermaid, statuses)
        assert "B[End]:::failed" in result

    def test_injects_multiple_statuses(self) -> None:
        """同時注入多個節點狀態。"""
        mermaid = "graph TD\nA[Start]-->B[Process]-->C[End]"
        statuses = {
            "A": NodeStatus.COMPLETED,
            "B": NodeStatus.RUNNING,
            "C": NodeStatus.PENDING,
        }
        result = render_mermaid_with_status(mermaid, statuses)
        assert "A[Start]:::completed" in result
        assert "B[Process]:::running" in result
        assert "C[End]:::pending" in result

    def test_preserves_unmatched_nodes(self) -> None:
        """未在 statuses 中的節點保持不變。"""
        mermaid = "graph TD\nA[Start]-->B[End]"
        statuses = {"A": NodeStatus.COMPLETED}
        result = render_mermaid_with_status(mermaid, statuses)
        # B 應保持不變
        assert "B[End]" in result
        assert "B[End]:::" not in result

    def test_handles_round_brackets(self) -> None:
        """支援圓括號節點格式。"""
        mermaid = "graph TD\nA(Start)-->B(End)"
        statuses = {"A": NodeStatus.RUNNING}
        result = render_mermaid_with_status(mermaid, statuses)
        assert "A(Start):::running" in result

    def test_nonexistent_node_no_change(self) -> None:
        """不存在的節點名稱不影響結果。"""
        mermaid = "graph TD\nA[Start]-->B[End]"
        statuses = {"Z": NodeStatus.RUNNING}
        result = render_mermaid_with_status(mermaid, statuses)
        assert result == mermaid


class TestApplyNodeLabels:
    """測試 apply_node_labels() 函式。"""

    def test_replaces_bracket_label(self) -> None:
        """替換方括號標籤。"""
        mermaid = "graph TD\n    classifier[classifier]\n    classifier --> end_node"
        result = apply_node_labels(mermaid, {"classifier": "意圖分類"})
        assert "classifier[意圖分類]" in result

    def test_replaces_langgraph_start_end(self) -> None:
        """替換 LangGraph __start__/__end__ 格式。"""
        mermaid = (
            "graph TD\n"
            "\t__start__([<p>__start__</p>])\n"
            "\t__end__([<p>__end__</p>])\n"
            "\t__start__ --> node1\n"
            "\tnode1 --> __end__"
        )
        result = apply_node_labels(
            mermaid,
            {
                "__start__": "開始",
                "__end__": "結束",
            },
        )
        assert "__start__([開始])" in result
        assert "__end__([結束])" in result

    def test_replaces_round_bracket_label(self) -> None:
        """替換圓括號標籤。"""
        mermaid = "graph TD\n    my_node(some label)"
        result = apply_node_labels(mermaid, {"my_node": "我的節點"})
        assert "my_node([我的節點])" in result

    def test_empty_label_map_returns_original(self) -> None:
        """空映射表時回傳原始碼。"""
        mermaid = "graph TD\nA[Start]-->B[End]"
        result = apply_node_labels(mermaid, {})
        assert result == mermaid

    def test_preserves_unmatched_nodes(self) -> None:
        """未匹配的節點保持不變。"""
        mermaid = "graph TD\nA[Start]-->B[End]"
        result = apply_node_labels(mermaid, {"A": "開始"})
        assert "A[開始]" in result
        assert "B[End]" in result

    def test_multiple_labels(self) -> None:
        """同時替換多個標籤。"""
        mermaid = (
            "graph TD\n"
            "    supervisor_decompose[supervisor_decompose]\n"
            "    execute_agent[execute_agent]\n"
            "    aggregate[aggregate]\n"
        )
        labels = {
            "supervisor_decompose": "任務分解",
            "execute_agent": "代理執行",
            "aggregate": "結果彙整",
        }
        result = apply_node_labels(mermaid, labels)
        assert "supervisor_decompose[任務分解]" in result
        assert "execute_agent[代理執行]" in result
        assert "aggregate[結果彙整]" in result

    def test_works_with_render_mermaid_with_status(self) -> None:
        """apply_node_labels 產出可被 render_mermaid_with_status 正確處理。"""
        mermaid = "graph TD\n    node1[原始標籤]\n    node1 --> node2[End]"
        labeled = apply_node_labels(mermaid, {"node1": "中文節點"})
        result = render_mermaid_with_status(labeled, {"node1": NodeStatus.RUNNING})
        assert "node1[中文節點]:::running" in result
