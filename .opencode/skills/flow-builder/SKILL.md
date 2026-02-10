---
name: flow-builder
description: 建立 LangGraph 流程。當使用者說「建立流程」、「新增 flow」、「設計工作流」、「create flow」時使用。
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
---

# Flow Builder Skill

基於 009 架構（BaseFlowExecutor + FlowRegistry + 節點工廠模式），引導開發者從自然語言描述產生完整的 LangGraph 流程程式碼。

## 觸發條件

當使用者的訊息包含以下任一關鍵字時，載入此 Skill：

- 「建立流程」、「新增流程」
- 「新增 flow」、「建立 flow」
- 「設計工作流」、「設計一個工作流」
- 「create flow」、「add flow」、「new flow」
- 「建立一個 ... 流程」

## 架構參考

本專案的流程架構基於 Spec 009 重構，核心元件如下：

| 元件 | 路徑 | 說明 |
|------|------|------|
| `BaseFlowExecutor` | `src/voice_assistant/flows/base.py` | 流程執行器抽象基底類別（ABC） |
| `FlowRegistry` | `src/voice_assistant/flows/registry.py` | 流程執行器註冊表，集中管理所有流程 |
| `FlowState` | `src/voice_assistant/flows/state.py` | LangGraph 主流程狀態（TypedDict） |
| `NodeChangeCallback` | `src/voice_assistant/flows/base.py` | 節點狀態變更回呼型別 |
| 節點工廠函式 | `src/voice_assistant/flows/nodes/` | `create_*_node()` 閉包注入模式 |
| StateGraph 定義 | `src/voice_assistant/flows/graphs/` | LangGraph 有向圖定義 |

### 關鍵設計模式

1. **工廠函式 + 閉包注入**: 節點透過 `create_*_node(dependency)` 工廠函式建立，依賴透過閉包捕獲
2. **TypedDict `total=False`**: 所有 FlowState 使用 `total=False`，允許部分更新
3. **FlowRegistry 自動註冊**: 新流程透過 `flow_registry.register(executor)` 註冊，不需修改核心邏輯
4. **Mermaid 視覺化**: 每個 Executor 可提供 `get_visualization()` 回傳 Mermaid 圖表

---

## 工作流程（10 步驟）

### 步驟 1：需求解析

**輸入**: 使用者的自然語言流程描述
**動作**: 從描述中提取以下資訊：
- 流程目標（這個流程要解決什麼問題？）
- 流程步驟（有哪些主要步驟？）
- 資料流（步驟之間傳遞什麼資料？）
- 外部依賴（需要呼叫哪些外部 API 或工具？）

**輸出**: 結構化的流程需求摘要

**注意**: 若描述過於模糊（如只說「建立一個流程」），請詢問開發者以下問題：
1. 這個流程的主要目標是什麼？
2. 預期有哪些步驟或階段？
3. 需要查詢哪些外部資料？（天氣、匯率、其他 API？）
4. 最終要產生什麼樣的回應給使用者？

### 步驟 2：現有工具盤點

**輸入**: 步驟 1 的需求摘要
**動作**:
1. 掃描 `src/voice_assistant/tools/` 目錄，列出所有已實作的工具
2. 讀取 `ToolRegistry` 中已註冊的工具清單
3. 比對需求中的外部資料查詢需求與現有工具

**輸出**: 可重用工具清單 + 需要新建的工具清單

```bash
# 查詢現有工具
ls src/voice_assistant/tools/
# 查看已註冊的工具
grep -r "class.*Tool.*BaseTool" src/voice_assistant/tools/
```

### 步驟 3：整合策略判斷

**輸入**: 步驟 1 的需求 + 步驟 2 的工具盤點結果
**動作**: 判斷新流程應採用哪種整合方式

**決策規則**:
- **獨立 Executor**（預設）：流程與現有意圖無關，建立新的 `BaseFlowExecutor` 子類別
- **子流程整合**：流程與現有 `main_router` 的意圖高度相關，整合到既有 StateGraph 中

**輸出**: 整合策略決策（獨立 Executor 或 子流程）

### 步驟 4：設計 FlowState

**輸入**: 步驟 1 的需求摘要
**動作**:
1. 識別流程中需要的所有狀態欄位
2. 決定是否需要 Pydantic 輔助模型（結構化的子狀態）
3. 設計 TypedDict 結構（使用 `total=False`）

**輸出**: FlowState 設計文件（欄位名稱、型別、用途）

### 步驟 5：設計節點

**輸入**: 步驟 1 的步驟清單 + 步驟 2 的工具盤點
**動作**:
1. 將每個流程步驟對應到一個節點
2. 為每個節點選擇類型：
   - **LLM 節點**: 需要 LLM 推理（如意圖分類、內容生成）
   - **工具節點**: 調用已註冊工具（如天氣查詢、匯率換算）
   - **純函式節點**: 無外部依賴的邏輯處理（如條件判斷、資料轉換）
3. 確定每個節點的依賴注入需求

**輸出**: 節點設計清單（名稱、類型、依賴、輸入/輸出）

### 步驟 6：設計 StateGraph

**輸入**: 步驟 5 的節點清單
**動作**:
1. 定義節點之間的邊（無條件邊 vs 條件邊）
2. 設計條件路由函式（使用 `Literal` 型別標註）
3. 決定入口點和結束點
4. 繪製流程圖（心智模型）

**輸出**: StateGraph 設計（節點、邊、條件路由）

### 步驟 7：產生 FlowState 程式碼

**輸入**: 步驟 4 的設計
**動作**: 依照 FlowState 模板產生程式碼，寫入 `src/voice_assistant/flows/state.py`（修改既有檔案新增子流程 State）

**輸出**: FlowState TypedDict 程式碼

### 步驟 8：產生節點程式碼

**輸入**: 步驟 5 的設計
**動作**:
1. 建立 `src/voice_assistant/flows/nodes/<domain>/` 目錄
2. 依照節點模板產生每個節點的工廠函式
3. 建立 `__init__.py`

**輸出**: 節點工廠函式程式碼（每個節點一個檔案）

### 步驟 9：產生 Graph + Executor 程式碼

**輸入**: 步驟 6 的設計
**動作**:
1. 依照 StateGraph 模板產生圖定義，寫入 `src/voice_assistant/flows/graphs/<domain>.py`
2. 依照 Executor 模板產生 BaseFlowExecutor 子類別，寫入 `src/voice_assistant/flows/<domain>_executor.py`
3. 在 composition root 中新增 `flow_registry.register()` 呼叫

**輸出**: StateGraph + Executor 程式碼

### 步驟 10：產生測試 + 驗證

**輸入**: 步驟 7-9 產生的程式碼
**動作**:
1. 依照測試模板產生 pytest 測試，寫入 `tests/unit/flows/test_<domain>.py`
2. 執行驗證命令：

```bash
uv run ruff check src/voice_assistant/flows/
uv run ruff format src/voice_assistant/flows/
uv run pytest tests/unit/flows/test_<domain>.py -v
```

3. 若有錯誤，依照常見錯誤檢查清單修復

**輸出**: 測試程式碼 + 驗證結果

---

## 程式碼模板

### 模板 1：FlowState TypedDict

```python
"""<DOMAIN> 流程狀態定義。"""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel


class <DomainInfo>(BaseModel):
    """<DOMAIN> 資訊結構。"""

    <field_1>: <type_1>
    <field_2>: <type_2>
    <field_3>: <type_3> | None = None


class <DomainState>(TypedDict, total=False):
    """<DOMAIN> 子流程狀態。"""

    <state_field_1>: str | None
    <state_field_2>: <DomainInfo> | None
    <state_field_3>: bool | None
    <state_field_4>: list[str]
```

**佔位符說明**：
- `<DOMAIN>`: 流程領域名稱（如 `food_recommend`、`stock_query`）
- `<DomainInfo>`: Pydantic 輔助模型名稱（如 `FoodInfo`、`StockInfo`）
- `<DomainState>`: 子流程狀態名稱（如 `FoodRecommendState`）
- `<field_*>` / `<type_*>`: 模型欄位與型別
- `<state_field_*>`: 狀態欄位

**整合方式**: 將上述程式碼新增到 `src/voice_assistant/flows/state.py`，並在 `FlowState` 中新增子流程狀態欄位：

```python
class FlowState(TypedDict, total=False):
    # ... 既有欄位 ...
    <domain>_state: <DomainState> | None  # 新增
```

### 模板 2：Node 工廠函式

#### 2a. LLM 節點（需要 LLM 推理）

```python
"""<DOMAIN> <NODE_NAME> 節點。

<節點功能簡述>。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from voice_assistant.flows.state import FlowState
from voice_assistant.llm.client import LLMClient

logger = logging.getLogger(__name__)

<NODE_SYSTEM_PROMPT> = """<SYSTEM_PROMPT_CONTENT>"""


def create_<node_name>_node(llm_client: LLMClient) -> Any:
    """建立 <NODE_NAME> 節點。

    Args:
        llm_client: LLM 客戶端實例。

    Returns:
        LangGraph 節點函式。
    """

    async def <node_function>(state: FlowState) -> dict[str, Any]:
        """<節點功能描述>。"""
        user_input = state.get("user_input", "")

        try:
            response = await llm_client.chat(
                messages=[
                    {"role": "system", "content": <NODE_SYSTEM_PROMPT>},
                    {"role": "user", "content": user_input},
                ],
            )

            content = response.choices[0].message.content or ""
            # 移除可能的 markdown 程式碼區塊標記
            content = content.strip().removeprefix("```json").removesuffix("```").strip()
            result = json.loads(content)

            return {
                "<state_field>": result.get("<key>"),
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("<NODE_NAME> 解析失敗: %s", e)
            return {"error": "<NODE_NAME> 處理失敗"}
        except Exception:
            logger.exception("<NODE_NAME> 執行失敗")
            return {"error": "<NODE_NAME> 執行時發生錯誤"}

    return <node_function>
```

#### 2b. 工具節點（調用已註冊工具）

```python
"""<DOMAIN> <NODE_NAME> 節點。

調用 <TOOL_NAME> 工具執行 <功能描述>。
"""

from __future__ import annotations

import logging
from typing import Any

from voice_assistant.flows.state import FlowState
from voice_assistant.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def create_<node_name>_node(tool_registry: ToolRegistry) -> Any:
    """建立 <NODE_NAME> 節點。

    Args:
        tool_registry: 工具註冊表實例。

    Returns:
        LangGraph 節點函式。
    """

    async def <node_function>(state: FlowState) -> dict[str, Any]:
        """調用 <TOOL_NAME> 工具。"""
        <domain>_state = state.get("<domain>_state") or {}
        <param> = <domain>_state.get("<param_field>")

        if not <param>:
            return {"error": "缺少必要參數: <param_field>"}

        try:
            tool = tool_registry.get("<tool_name>")
            result = await tool.execute({<tool_args>})

            return {
                "<domain>_state": {
                    **<domain>_state,
                    "<result_field>": result.data,
                },
            }
        except Exception:
            logger.exception("<TOOL_NAME> 工具呼叫失敗")
            return {"error": "<TOOL_NAME> 查詢失敗，請稍後再試"}

    return <node_function>
```

#### 2c. 純函式節點（無外部依賴）

```python
"""<DOMAIN> <NODE_NAME> 節點。

<節點功能簡述>。
"""

from __future__ import annotations

import logging
from typing import Any

from voice_assistant.flows.state import FlowState

logger = logging.getLogger(__name__)


async def <node_function>(state: FlowState) -> dict[str, Any]:
    """<節點功能描述>。"""
    <domain>_state = state.get("<domain>_state") or {}
    <input_field> = <domain>_state.get("<input_field>")

    # 純邏輯處理（無外部依賴）
    <result> = <pure_logic>(<input_field>)

    return {
        "<domain>_state": {
            **<domain>_state,
            "<output_field>": <result>,
        },
    }
```

**注意**: 純函式節點不需要工廠函式包裝，直接定義 `async def` 即可。

### 模板 3：StateGraph 定義

```python
"""<DOMAIN> 流程圖定義。

定義 <DOMAIN> 流程的 LangGraph StateGraph。
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from voice_assistant.flows.state import FlowState
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools.registry import ToolRegistry

# 匯入節點工廠函式
from voice_assistant.flows.nodes.<domain>.<node_1> import create_<node_1>_node
from voice_assistant.flows.nodes.<domain>.<node_2> import create_<node_2>_node
from voice_assistant.flows.nodes.<domain>.<node_3> import <node_3_function>


def _route_by_<condition>(state: FlowState) -> Literal["<option_a>", "<option_b>"]:
    """依 <condition> 條件路由。"""
    <domain>_state = state.get("<domain>_state") or {}
    <field> = <domain>_state.get("<field>")

    if <field>:
        return "<option_a>"
    return "<option_b>"


def create_<domain>_graph(
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
) -> CompiledStateGraph:
    """建立 <DOMAIN> 流程圖。

    Args:
        llm_client: LLM 客戶端實例。
        tool_registry: 工具註冊表實例。

    Returns:
        編譯後的 StateGraph。
    """
    builder = StateGraph(FlowState)

    # 建立節點
    <node_1>_fn = create_<node_1>_node(llm_client)
    <node_2>_fn = create_<node_2>_node(tool_registry)

    # 新增節點
    builder.add_node("<node_1>", <node_1>_fn)
    builder.add_node("<node_2>", <node_2>_fn)
    builder.add_node("<node_3>", <node_3_function>)

    # 設定入口點
    builder.set_entry_point("<node_1>")

    # 新增邊（無條件）
    builder.add_edge("<node_2>", "<node_3>")

    # 新增條件邊
    builder.add_conditional_edges(
        "<node_1>",
        _route_by_<condition>,
        {
            "<option_a>": "<node_2>",
            "<option_b>": END,
        },
    )

    # 終點
    builder.add_edge("<node_3>", END)

    return builder.compile()
```

### 模板 4：BaseFlowExecutor 子類別

```python
"""<DOMAIN> 流程執行器。

提供 <DOMAIN> 流程的完整執行介面。
"""

from __future__ import annotations

import logging

from voice_assistant.flows.base import BaseFlowExecutor, NodeChangeCallback
from voice_assistant.flows.graphs.<domain> import create_<domain>_graph
from voice_assistant.llm.client import LLMClient
from voice_assistant.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class <Domain>FlowExecutor(BaseFlowExecutor):
    """<DOMAIN> 流程執行器。

    繼承 BaseFlowExecutor，封裝 <DOMAIN> 的 LangGraph StateGraph。
    """

    # 節點 ID → 顯示名稱 對照表（用於視覺化）
    _NODE_LABELS: dict[str, str] = {
        "<node_1>": "<節點 1 顯示名稱>",
        "<node_2>": "<節點 2 顯示名稱>",
        "<node_3>": "<節點 3 顯示名稱>",
    }

    _MERMAID_DIAGRAM = """graph TD
    <node_1>[<節點 1 顯示名稱>] --> <node_2>[<節點 2 顯示名稱>]
    <node_2> --> <node_3>[<節點 3 顯示名稱>]
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
    ) -> None:
        self._graph = create_<domain>_graph(llm_client, tool_registry)

    @property
    def flow_name(self) -> str:
        """流程名稱。"""
        return "<domain>"

    async def execute(
        self,
        user_input: str,
        on_node_change: NodeChangeCallback | None = None,
    ) -> str:
        """執行 <DOMAIN> 流程。

        Args:
            user_input: 使用者輸入文字。
            on_node_change: 節點狀態變更回呼。

        Returns:
            流程產生的回應文字。
        """
        initial_state: dict = {"user_input": user_input}

        result = await self._graph.ainvoke(initial_state)

        if error := result.get("error"):
            return f"處理過程中發生錯誤：{error}"

        return result.get("response", "抱歉，無法產生回應。")

    def get_visualization(self) -> str | None:
        """取得 Mermaid 視覺化圖表。"""
        return self._MERMAID_DIAGRAM
```

**註冊方式**: 在 composition root（如 `main.py` 或初始化模組）中新增：

```python
from voice_assistant.flows.<domain>_executor import <Domain>FlowExecutor

executor = <Domain>FlowExecutor(llm_client, tool_registry)
flow_registry.register(executor)
```

### 模板 5：pytest 測試

```python
"""<DOMAIN> 流程測試。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voice_assistant.flows.state import FlowState


class TestCreate<NodeName>Node:
    """<NODE_NAME> 節點測試。"""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """模擬 LLM 客戶端。"""
        client = MagicMock()
        client.chat = AsyncMock()
        return client

    @pytest.fixture
    def mock_tool_registry(self) -> MagicMock:
        """模擬工具註冊表。"""
        registry = MagicMock()
        return registry

    @pytest.mark.asyncio
    async def test_<node_name>_正常情境(self, mock_llm_client: MagicMock) -> None:
        """測試 <NODE_NAME> 節點的正常執行。"""
        from voice_assistant.flows.nodes.<domain>.<node_name> import (
            create_<node_name>_node,
        )

        # 設定 mock 回傳值
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"<key>": "<value>"}'
        mock_llm_client.chat.return_value = mock_response

        # 建立節點並執行
        node_fn = create_<node_name>_node(mock_llm_client)
        state: FlowState = {"user_input": "<測試輸入>"}
        result = await node_fn(state)

        # 驗證
        assert "<expected_field>" in result
        assert result["<expected_field>"] == "<expected_value>"

    @pytest.mark.asyncio
    async def test_<node_name>_異常情境(self, mock_llm_client: MagicMock) -> None:
        """測試 <NODE_NAME> 節點的錯誤處理。"""
        from voice_assistant.flows.nodes.<domain>.<node_name> import (
            create_<node_name>_node,
        )

        # 設定 mock 拋出例外
        mock_llm_client.chat.side_effect = Exception("LLM 呼叫失敗")

        node_fn = create_<node_name>_node(mock_llm_client)
        state: FlowState = {"user_input": "<測試輸入>"}
        result = await node_fn(state)

        # 驗證錯誤處理
        assert "error" in result


class Test<Domain>FlowExecutor:
    """<DOMAIN> 流程執行器測試。"""

    @pytest.mark.asyncio
    async def test_flow_name(self) -> None:
        """測試 flow_name 屬性。"""
        from voice_assistant.flows.<domain>_executor import <Domain>FlowExecutor

        executor = <Domain>FlowExecutor(
            llm_client=MagicMock(),
            tool_registry=MagicMock(),
        )
        assert executor.flow_name == "<domain>"

    @pytest.mark.asyncio
    async def test_get_visualization(self) -> None:
        """測試 Mermaid 視覺化。"""
        from voice_assistant.flows.<domain>_executor import <Domain>FlowExecutor

        executor = <Domain>FlowExecutor(
            llm_client=MagicMock(),
            tool_registry=MagicMock(),
        )
        viz = executor.get_visualization()
        assert viz is not None
        assert "graph TD" in viz
```

---

## 工具整合指引

### 查詢現有工具

執行以下命令盤點可重用的工具：

```bash
# 列出所有工具檔案
ls src/voice_assistant/tools/

# 查看所有繼承 BaseTool 的工具類別
grep -r "class.*Tool.*BaseTool" src/voice_assistant/tools/

# 查看工具的 tool_definition（了解工具接受的參數）
grep -A 20 "def tool_definition" src/voice_assistant/tools/*.py
```

### 目前可用的工具

| 工具 | 類別 | 功能 |
|------|------|------|
| `WeatherTool` | `src/voice_assistant/tools/weather.py` | 查詢城市天氣（Open-Meteo API） |
| `ExchangeRateTool` | `src/voice_assistant/tools/exchange_rate.py` | 查詢匯率換算（ExchangeRate-API） |

### 在節點中調用工具

```python
# 透過 ToolRegistry 取得工具
tool = tool_registry.get("weather")  # 使用工具名稱
result = await tool.execute({"city": "台北"})

# result 為 ToolResult 物件
if result.success:
    data = result.data  # 工具回傳的資料
else:
    error = result.error  # 錯誤訊息
```

### 需要新工具時

若流程需要的功能不在現有工具中：

1. **通知開發者**: 明確告知「此流程需要 `<功能>` 工具，但目前尚未實作」
2. **建議先建立工具**: 新工具應繼承 `BaseTool`，放置在 `src/voice_assistant/tools/` 目錄
3. **不要在節點中直接呼叫外部 API**: 遵循 Tool-First Architecture 原則

---

## 驗證與品質保證

### 驗證步驟

產生程式碼後，依序執行以下驗證：

```bash
# 1. 程式碼檢查
uv run ruff check src/voice_assistant/flows/

# 2. 程式碼格式化
uv run ruff format src/voice_assistant/flows/

# 3. 執行測試
uv run pytest tests/unit/flows/test_<domain>.py -v

# 4. 型別檢查（可選）
uv run pyright src/voice_assistant/flows/
```

### 常見錯誤檢查清單

產生程式碼後，逐一檢查以下常見問題：

- [ ] **import 路徑**: 確認所有 import 路徑正確（`voice_assistant.flows.` 前綴）
- [ ] **型別標註**: 所有函式參數和回傳值都有型別標註
- [ ] **`async/await`**: 所有呼叫 LLM 或工具的函式都使用 `async def`，呼叫時使用 `await`
- [ ] **`total=False`**: TypedDict 使用 `total=False`，允許部分更新
- [ ] **`dict[str, Any]` 回傳**: 節點函式回傳 `dict[str, Any]`，不是完整的 FlowState
- [ ] **閉包注入**: 工廠函式正確捕獲依賴（`llm_client`、`tool_registry`）
- [ ] **`state.get()`**: 使用 `.get()` 存取狀態欄位，避免 `KeyError`
- [ ] **`Literal` 型別**: 條件路由函式的回傳型別使用 `Literal[...]`
- [ ] **`from __future__ import annotations`**: 每個檔案開頭包含此 import
- [ ] **logging**: 使用 `logger = logging.getLogger(__name__)` 而非 `print()`
- [ ] **繁體中文**: 所有 docstring 和註解以繁體中文撰寫

### 自動修復常見問題

```bash
# Ruff 自動修復可修復的問題
uv run ruff check --fix src/voice_assistant/flows/

# 重新格式化
uv run ruff format src/voice_assistant/flows/
```

---

## Edge Case 處理

### 功能重疊

若開發者描述的流程與現有流程功能重疊（如已有 `travel_planner`，又要建「旅遊推薦」）：
- 提醒開發者現有流程已涵蓋類似功能
- 建議擴展現有流程而非建立新流程

### 節點數量過多

若流程包含超過 10 個節點：
- 建議拆分為多個子流程
- 每個子流程負責一個獨立的功能區塊
- 透過主流程串接子流程

### 語言規範

所有產生的程式碼、docstring、註解皆以**繁體中文**為主要語言。技術專有名詞（如 `StateGraph`、`BaseFlowExecutor`）保持英文原文。

---

## 完成後回報格式

所有程式碼產生完成後，以下列格式回報：

```
## 流程產生完成

### 產生的檔案

| 檔案 | 說明 |
|------|------|
| `src/voice_assistant/flows/state.py` | 新增 <DomainState> 子流程狀態 |
| `src/voice_assistant/flows/nodes/<domain>/` | <N> 個節點工廠函式 |
| `src/voice_assistant/flows/graphs/<domain>.py` | StateGraph 定義 |
| `src/voice_assistant/flows/<domain>_executor.py` | BaseFlowExecutor 子類別 |
| `tests/unit/flows/test_<domain>.py` | pytest 測試 |

### 驗證結果

- [ ] Ruff check 通過
- [ ] Ruff format 通過
- [ ] pytest 測試通過
- [ ] 已註冊到 FlowRegistry

### 下一步

1. 審查產生的程式碼
2. 依需求調整業務邏輯
3. 補充整合測試
```
