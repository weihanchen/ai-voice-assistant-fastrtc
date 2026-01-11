# Quickstart: Multi-Agent Collaboration

**Feature**: 007-multi-agent-collaboration
**Date**: 2025-01-11

## 快速體驗

### 1. 設定環境變數

```bash
# .env
OPENAI_API_KEY=your-api-key
FLOW_MODE=multi_agent  # 啟用多代理模式
```

### 2. 啟動服務

```bash
uv run python -m voice_assistant.main
```

### 3. 測試多代理協作

開啟瀏覽器 http://localhost:7860，嘗試以下對話：

| 場景 | 語音輸入 | 預期行為 |
|------|----------|----------|
| 並行查詢 | 「查台積電股價和美金匯率」 | Finance Agent 並行查詢兩項資訊 |
| 旅遊規劃 | 「我想去台中玩」 | Weather + Travel Agent 協作 |
| 出差助理 | 「明天去東京出差」 | Weather + Finance Agent 協作 |
| 單一查詢 | 「台北天氣如何」 | 僅 Weather Agent 處理 |
| 閒聊 | 「你好」 | General Agent 回應 |

---

## 切換模式

### 模式比較

| 模式 | 環境變數 | 說明 |
|------|----------|------|
| **tools** | `FLOW_MODE=tools` | 純 Tool 呼叫，最簡單 |
| **langgraph** | `FLOW_MODE=langgraph` | LangGraph 流程，單一路由 |
| **multi_agent** | `FLOW_MODE=multi_agent` | 多代理協作，並行處理 |

### 切換方式

```bash
# 方式 1：修改 .env
echo "FLOW_MODE=langgraph" >> .env

# 方式 2：命令列指定
FLOW_MODE=tools uv run python -m voice_assistant.main
```

---

## 程式碼使用範例

### 直接使用 MultiAgentExecutor

```python
from voice_assistant.agents.executor import MultiAgentExecutor
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools.registry import ToolRegistry

# 初始化
llm_client = LLMClient()
tool_registry = ToolRegistry()
executor = MultiAgentExecutor(llm_client, tool_registry)

# 執行
response = await executor.execute("查台積電股價和美金匯率")
print(response)
# 輸出: "台積電目前股價 580 元，今日上漲 1.2%。美金兌台幣匯率為 31.5。"
```

### 直接使用 LangGraph

```python
from voice_assistant.agents.graph import create_multi_agent_graph

# 建立流程圖
graph = create_multi_agent_graph(llm_client, tool_registry)

# 執行
result = await graph.ainvoke({
    "user_input": "台北和高雄今天天氣如何"
})

print(result["final_response"])
# 輸出: "台北今天 25 度晴天，高雄 28 度多雲..."
```

### 單獨使用 Agent

```python
from voice_assistant.agents.weather import WeatherAgent
from voice_assistant.agents.state import AgentTask, AgentType

# 初始化
agent = WeatherAgent(tool_registry)

# 建立任務
task = AgentTask(
    agent_type=AgentType.WEATHER,
    description="查詢台北天氣",
    parameters={"city": "台北"}
)

# 執行
result = await agent.execute(task)
print(result.data)
# 輸出: {"city": "台北", "temperature": 25.0, "weather": "晴天", ...}
```

---

## 測試

### 執行所有測試

```bash
uv run pytest tests/ -v
```

### 僅執行 Agent 相關測試

```bash
uv run pytest tests/unit/agents/ -v
uv run pytest tests/integration/test_multi_agent_flow.py -v
```

### 效能測試

```bash
# 測試並行執行效能
uv run pytest tests/integration/test_multi_agent_flow.py::test_parallel_execution_time -v
```

---

## 疑難排解

### 問題：Agent 執行逾時

**現象**: 回應中出現「執行逾時」錯誤

**解決方案**:
1. 檢查網路連線
2. 確認外部 API 是否正常
3. 可調整 Agent 的 timeout 屬性（預設 10 秒）

### 問題：任務未正確拆解

**現象**: 複合查詢只回傳部分結果

**解決方案**:
1. 檢查 Supervisor 的 LLM 回應
2. 確認 OpenAI API Key 有效
3. 查看 logs 中的 TaskDecomposition 內容

### 問題：模式切換無效

**現象**: 修改 FLOW_MODE 後行為未改變

**解決方案**:
1. 確認重新啟動服務
2. 檢查環境變數是否正確載入
3. 確認 .env 檔案格式正確（無空格）
