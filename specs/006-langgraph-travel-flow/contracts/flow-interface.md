# Flow Interface Contract

**Date**: 2026-01-04
**Purpose**: 定義流程節點與圖的介面規範

## 節點介面

### 基本節點簽名

所有 LangGraph 節點必須遵循以下簽名：

```python
from typing import TypedDict

def node_function(state: FlowState) -> FlowState:
    """
    同步節點函式

    Args:
        state: 當前流程狀態

    Returns:
        更新後的流程狀態（僅需回傳變更的欄位）
    """
    ...

async def async_node_function(state: FlowState) -> FlowState:
    """
    非同步節點函式（用於 I/O 操作）

    Args:
        state: 當前流程狀態

    Returns:
        更新後的流程狀態
    """
    ...
```

---

## 節點合約

### 1. ClassifierNode（意圖分類節點）

**檔案位置**: `src/voice_assistant/flows/nodes/classifier.py`

**輸入狀態**:
```python
{
    "user_input": str  # 必填：使用者輸入文字
}
```

**輸出狀態**:
```python
{
    "intent": IntentType,      # 分類結果
    "tool_name": str | None,   # Tool 名稱（如適用）
    "tool_args": dict | None   # Tool 參數（如適用）
}
```

**行為規範**:
- 使用 LLM 進行意圖分類
- 對於 weather/exchange/stock 意圖，同時提取 Tool 參數
- 對於 travel 意圖，僅設定 intent，不提取參數

**錯誤處理**:
- LLM 呼叫失敗：設定 `error` 欄位，intent 為 None

---

### 2. ToolExecutorNode（工具執行節點）

**檔案位置**: `src/voice_assistant/flows/nodes/tool_executor.py`

**輸入狀態**:
```python
{
    "tool_name": str,   # 必填：Tool 名稱
    "tool_args": dict   # 必填：Tool 參數
}
```

**輸出狀態**:
```python
{
    "tool_result": dict | None,  # 執行結果
    "error": str | None          # 錯誤訊息（如有）
}
```

**行為規範**:
- 透過 `ToolRegistry.execute()` 呼叫對應 Tool
- 將 `ToolResult` 轉換為狀態格式

**錯誤處理**:
- Tool 不存在：設定 error = "tool_not_found"
- Tool 執行失敗：設定 error = ToolResult.error

---

### 3. ResponseGeneratorNode（回應產生節點）

**檔案位置**: `src/voice_assistant/flows/nodes/response_generator.py`

**輸入狀態**:
```python
{
    "user_input": str,
    "intent": IntentType,
    "tool_result": dict | None,
    "travel_state": TravelPlanState | None,
    "error": str | None
}
```

**輸出狀態**:
```python
{
    "response": str  # 最終回應文字
}
```

**行為規範**:
- 使用 LLM 將結果轉換為口語化繁體中文
- 如有 error，產生友善錯誤訊息
- 回應長度限制 200 字以內（適合語音輸出）

---

## 旅遊規劃子流程節點

### 4. DestinationParserNode（目的地解析節點）

**檔案位置**: `src/voice_assistant/flows/nodes/travel/destination.py`

**輸入狀態**:
```python
{
    "user_input": str  # 使用者輸入
}
```

**輸出狀態**:
```python
{
    "travel_state": {
        "destination": str | None,
        "destination_valid": bool
    }
}
```

**行為規範**:
- 使用 LLM 從使用者輸入中提取目的地城市
- 驗證是否為 TAIWAN_CITIES 支援的城市

---

### 5. WeatherQueryNode（天氣查詢節點）

**檔案位置**: `src/voice_assistant/flows/nodes/travel/weather.py`

**輸入狀態**:
```python
{
    "travel_state": {
        "destination": str  # 必填：已驗證的目的地
    }
}
```

**輸出狀態**:
```python
{
    "travel_state": {
        "weather_data": WeatherInfo
    }
}
```

**行為規範**:
- 呼叫現有 `WeatherTool.execute()`
- 將結果轉換為 `WeatherInfo` 格式

---

### 6. WeatherEvaluatorNode（天氣評估節點）

**檔案位置**: `src/voice_assistant/flows/nodes/travel/evaluator.py`

**輸入狀態**:
```python
{
    "travel_state": {
        "weather_data": WeatherInfo
    }
}
```

**輸出狀態**:
```python
{
    "travel_state": {
        "weather_suitable": bool
    }
}
```

**行為規範**:
- 根據天氣條件判斷是否適合出遊
- 判斷邏輯見 data-model.md

---

### 7. RecommenderNode（建議產生節點）

**檔案位置**: `src/voice_assistant/flows/nodes/travel/recommender.py`

**輸入狀態**:
```python
{
    "travel_state": {
        "destination": str,
        "weather_suitable": bool
    }
}
```

**輸出狀態**:
```python
{
    "travel_state": {
        "recommendation_type": RecommendationType,
        "recommendations": list[str]
    }
}
```

**行為規範**:
- 根據 `weather_suitable` 選擇 outdoor 或 indoor 建議
- 從 `CITY_RECOMMENDATIONS` 取得景點清單
- 最多回傳 3 個建議

---

## 路由函式合約

### IntentRouter（意圖路由）

**檔案位置**: `src/voice_assistant/flows/graphs/main_router.py`

```python
def route_by_intent(state: FlowState) -> str:
    """
    根據意圖分類結果決定下一個節點

    Args:
        state: 包含 intent 的流程狀態

    Returns:
        下一個節點名稱：
        - "weather_tool" | "exchange_tool" | "stock_tool"
        - "travel_subgraph"
        - END（如果有錯誤）
    """
```

### WeatherConditionRouter（天氣條件路由）

**檔案位置**: `src/voice_assistant/flows/graphs/travel_planner.py`

```python
def route_by_weather(state: FlowState) -> str:
    """
    根據天氣評估結果決定建議類型

    Args:
        state: 包含 travel_state.weather_suitable 的狀態

    Returns:
        下一個節點名稱：
        - "recommend_outdoor"（天氣適合）
        - "recommend_indoor"（天氣不適合）
    """
```

---

## 流程圖合約

### MainRouterGraph（主路由流程）

**檔案位置**: `src/voice_assistant/flows/graphs/main_router.py`

```python
def create_main_router_graph(
    llm_client: LLMClient,
    tool_registry: ToolRegistry
) -> CompiledGraph:
    """
    建立主路由流程圖

    Args:
        llm_client: LLM 客戶端實例
        tool_registry: Tool 註冊表實例

    Returns:
        編譯後的 StateGraph
    """
```

**節點結構**:
```
START → classifier → [conditional: route_by_intent]
                     ├→ weather_tool → response_generator → END
                     ├→ exchange_tool → response_generator → END
                     ├→ stock_tool → response_generator → END
                     └→ travel_subgraph → response_generator → END
```

### TravelPlannerGraph（旅遊規劃子流程）

**檔案位置**: `src/voice_assistant/flows/graphs/travel_planner.py`

```python
def create_travel_planner_graph(
    tool_registry: ToolRegistry
) -> CompiledGraph:
    """
    建立旅遊規劃子流程圖

    Args:
        tool_registry: Tool 註冊表（用於呼叫 WeatherTool）

    Returns:
        編譯後的 StateGraph
    """
```

**節點結構**:
```
START → parse_destination → [conditional: valid?]
                            ├→ query_weather → evaluate_weather → [conditional: suitable?]
                            │                                     ├→ recommend_outdoor → END
                            │                                     └→ recommend_indoor → END
                            └→ error_handler → END
```

---

## 視覺化輸出合約

### FlowVisualizer

**檔案位置**: `src/voice_assistant/flows/visualization.py`

```python
def get_mermaid_diagram(graph: CompiledGraph) -> str:
    """
    產生流程圖的 Mermaid 原始碼

    Args:
        graph: 編譯後的 LangGraph

    Returns:
        Mermaid 格式字串
    """

def save_mermaid_png(graph: CompiledGraph, output_path: str) -> None:
    """
    將流程圖儲存為 PNG 圖片

    Args:
        graph: 編譯後的 LangGraph
        output_path: 輸出檔案路徑
    """
```

---

## 整合介面

### FlowExecutor（流程執行器）

**檔案位置**: `src/voice_assistant/flows/__init__.py`

```python
class FlowExecutor:
    """LangGraph 流程執行器"""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry
    ) -> None:
        """初始化流程執行器"""

    async def execute(self, user_input: str) -> str:
        """
        執行對話流程

        Args:
            user_input: 使用者輸入文字

        Returns:
            回應文字
        """

    def get_visualization(self) -> str:
        """
        取得流程視覺化 Mermaid 圖

        Returns:
            Mermaid 格式字串
        """
```

**與 VoicePipeline 整合**:
```python
# voice/pipeline.py
class VoicePipeline:
    def __init__(
        self,
        ...
        flow_executor: FlowExecutor | None = None  # 新增參數
    ):
        self.flow_executor = flow_executor

    async def _process_with_flow(self, user_text: str) -> str:
        """使用 LangGraph 流程處理"""
        if self.flow_executor:
            return await self.flow_executor.execute(user_text)
        else:
            # 降級為原有 Tool 呼叫邏輯
            return await self._process_with_tools(user_text)
```
