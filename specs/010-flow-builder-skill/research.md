# 研究紀錄：Flow Builder Agent Skill

**功能**: 010-flow-builder-skill  
**日期**: 2026-02-10

## 研究 1：OpenCode Skill 檔案格式最佳實踐

### 決策
採用現有專案的 SKILL.md 格式：YAML frontmatter + Markdown body。

### 理由
- 專案已有 2 個正常運作的 Skill（`commit`、`spec-driven-development`）
- 格式已驗證可被 OpenCode 正確載入和解析
- YAML frontmatter 提供機器可讀的 metadata（name, description, allowed-tools）
- Markdown body 提供人類可讀的指引和程式碼範例

### 考慮過的替代方案
- JSON 格式：可讀性差，不適合包含大量程式碼模板
- 純 Markdown（無 frontmatter）：缺少結構化 metadata

## 研究 2：程式碼模板設計策略

### 決策
在 SKILL.md 中使用 fenced code blocks 內嵌模板，以佔位符（`<DOMAIN>`、`<NodeName>` 等）標記可替換部分。

### 理由
- 現有 Skill（commit）已使用 fenced code blocks 內嵌程式碼範例
- 佔位符模式簡單直觀，agent 容易理解和替換
- 不需要額外的模板引擎或外部檔案
- 所有資訊集中在單一 SKILL.md 中，降低維護成本

### 考慮過的替代方案
- 外部模板檔案（`.opencode/skills/flow-builder/templates/`）：增加複雜度，需處理檔案路徑解析
- Jinja2 模板語法：需要額外依賴，且 agent 不一定理解 Jinja2 語法
- Cookiecutter 模式：過度設計，專案只需 agent 手動替換

## 研究 3：流程整合策略（子流程 vs 獨立 Executor）

### 決策
Skill 指引 agent 預設產生**獨立的 BaseFlowExecutor 子類別**，僅在流程與現有 main_router 意圖高度相關時才整合為子流程。

### 理由
- 獨立 Executor 對新開發者更容易理解和維護
- 透過 FlowRegistry 註冊即可使用，不需修改現有程式碼
- 避免 main_router.py 過度膨脹
- 符合 OCP（開放封閉原則）

### 考慮過的替代方案
- 總是整合到 main_router：增加現有程式碼的修改風險
- 總是建立新的 FlowMode enum 值：需要修改 config.py，違反 OCP

## 研究 4：節點類型分類

### 決策
Skill 模板涵蓋 3 種節點類型，覆蓋所有常見場景：

1. **LLM 節點**（需要 LLM 推理）：使用 `create_*_node(llm_client)` 工廠模式
2. **工具節點**（調用已註冊工具）：使用 `create_*_node(tool_registry)` 工廠模式
3. **純函式節點**（無外部依賴）：直接定義 `async def node_fn(state) -> dict`

### 理由
- 從現有程式碼中歸納出的 3 種模式完全覆蓋了目前所有節點
- classifier.py = LLM 節點，tool_executor.py = 工具節點，evaluator.py = 純函式節點
- 每種類型有明確不同的依賴注入模式

### 考慮過的替代方案
- 統一所有節點為 class-based：與現有架構不一致
- 只提供一種通用模板：agent 需要更多推理來決定模式

## 研究 5：現有架構模式提取

### 決策
從 009 完成的程式碼中提取以下關鍵模式供模板使用：

| 模式 | 來源檔案 | 模板化重點 |
|------|----------|-----------|
| FlowState TypedDict | `flows/state.py` | `total=False`、子流程巢狀、Pydantic 輔助模型 |
| Node 工廠函式 | `flows/nodes/travel/destination.py` | 閉包注入、`dict[str, Any]` 回傳、錯誤處理 |
| StateGraph 定義 | `flows/graphs/travel_planner.py` | `add_node`、`add_edge`、`add_conditional_edges`、`compile()` |
| BaseFlowExecutor | `flows/tool_calling_executor.py` | `flow_name` property、`execute` async method、`get_visualization`、`_NODE_LABELS` |
| 條件路由函式 | `flows/graphs/main_router.py` | `Literal` 回傳型別、`state.get()` 存取 |

### 理由
直接從已驗證的程式碼提取模式，確保模板與實際架構 100% 一致。
