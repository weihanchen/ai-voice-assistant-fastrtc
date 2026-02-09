"""MultiAgentExecutor.get_visualization() 診斷測試。

驗證 multi_agent 流程的視覺化功能能正確回傳有效的 Mermaid 程式碼。
"""

from __future__ import annotations

from unittest.mock import MagicMock

from voice_assistant.agents.executor import MultiAgentExecutor


class TestMultiAgentExecutorVisualization:
    """測試 MultiAgentExecutor 的視覺化功能。"""

    def _make_executor(self) -> MultiAgentExecutor:
        """建立 MultiAgentExecutor 實例。"""
        llm_client = MagicMock()
        tool_registry = MagicMock()
        return MultiAgentExecutor(llm_client, tool_registry)

    def test_get_visualization_returns_string(self) -> None:
        """get_visualization() 應回傳字串。"""
        executor = self._make_executor()
        result = executor.get_visualization()
        assert isinstance(result, str)

    def test_get_visualization_not_empty(self) -> None:
        """get_visualization() 不應回傳空字串。"""
        executor = self._make_executor()
        result = executor.get_visualization()
        assert result.strip() != ""

    def test_get_visualization_contains_graph_keyword(self) -> None:
        """get_visualization() 應包含 Mermaid 圖表關鍵字（如 graph）。"""
        executor = self._make_executor()
        result = executor.get_visualization()
        # Mermaid 流程圖通常以 graph 或 flowchart 或 stateDiagram 開頭
        mermaid_keywords = ["graph", "flowchart", "stateDiagram"]
        has_keyword = any(kw in result.lower() for kw in mermaid_keywords)
        assert has_keyword, f"Mermaid 輸出不包含預期關鍵字: {result[:200]}"

    def test_get_visualization_contains_node_names(self) -> None:
        """get_visualization() 應包含流程圖的節點 ID。"""
        executor = self._make_executor()
        result = executor.get_visualization()
        # 流程圖應包含已定義的節點 ID
        expected_nodes = ["supervisor_decompose", "execute_agent", "aggregate"]
        for node in expected_nodes:
            assert node in result, f"Mermaid 輸出缺少節點 '{node}': {result[:200]}"

    def test_get_visualization_contains_chinese_labels(self) -> None:
        """get_visualization() 應包含使用者友善的中文標籤。"""
        executor = self._make_executor()
        result = executor.get_visualization()
        expected_labels = ["任務分解", "代理執行", "結果彙整", "開始", "結束"]
        for label in expected_labels:
            assert label in result, (
                f"Mermaid 輸出缺少中文標籤 '{label}': {result[:300]}"
            )

    def test_flow_name_is_multi_agent(self) -> None:
        """flow_name 應為 'multi_agent'。"""
        executor = self._make_executor()
        assert executor.flow_name == "multi_agent"
