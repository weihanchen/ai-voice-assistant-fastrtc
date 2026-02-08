---
完整計畫：Flow Builder Agent Skill + 架構重構
一、現有架構問題評估
經過完整閱讀所有原始碼後，我發現以下需要重構的架構局限性：
問題 1：Composition Root 過度膨脹與硬編碼
voice/handlers/reply_on_pause.py 的 create_voice_stream() 是唯一的組裝點，所有工具、代理、角色都硬編碼在這裡。新增任何元件都需要修改這個檔案。
影響：無法動態發現和註冊工具/代理，Skill 產生的程式碼也需要手動修改 composition root。
問題 2：三種 Flow Mode 缺乏統一抽象
VoicePipeline.process_audio_with_outputs() 裡用 if/elif 分支處理 TOOLS、LANGGRAPH、MULTI_AGENT 三種模式。新增流程模式需要修改 VoicePipeline 核心邏輯，違反 OCP（開放封閉原則）。
影響：Skill 產生新流程後，開發者還得手動在 VoicePipeline 裡加 elif。
問題 3：Flow/Graph 無統一註冊機制
FlowExecutor 和 MultiAgentExecutor 是獨立的類別，沒有共同介面。新增的 LangGraph 流程（如 Skill 產生的流程）沒有標準方式被系統發現和使用。
影響：每個新流程都是獨立孤島，無法組合，也無法讓系統自動路由。
問題 4：Agent 與 Tool 缺乏自動發現
目前所有 Agent 都在 agents/graph.py 裡硬編碼到 agents_dict 中。Tool 也在 composition root 手動 register()。
影響：Skill 產生新 Agent 或 Tool 後，開發者需要手動在多處程式碼中註冊。
問題 5：視覺化僅限於靜態 Mermaid
flows/visualization.py 只能產生靜態 Mermaid 圖。沒有即時執行狀態追蹤，也未整合到 Gradio UI 中。
影響：無法滿足 Gradio UI 即時視覺化的需求。
---
二、重構計畫
按照 spec-driven-development 流程，建議分為 兩個 spec：
Spec 009：Flow Architecture Refactoring（架構重構）
目標：讓系統具備「新增流程只需新增檔案，不需修改核心程式碼」的能力。
User Story P1：統一 FlowExecutor 介面
作為開發者，我希望所有流程模式（tools/langgraph/multi_agent/自定義）都實作同一個介面，
讓 VoicePipeline 不需要知道具體實作細節。
- 建立 BaseFlowExecutor Protocol/ABC：
    class BaseFlowExecutor(ABC):
      @abstractmethod
      async def execute(self, user_input: str, **kwargs) -> str: ...
      
      @abstractmethod
      def get_flow_name(self) -> str: ...
      
      def get_visualization(self) -> str | None: ...  # optional
  - 將現有 FlowExecutor、MultiAgentExecutor 和 legacy tools 模式都適配到這個介面
- VoicePipeline 只依賴 BaseFlowExecutor，消除 if/elif 分支
User Story P2：Flow Registry + 自動發現
作為開發者，我希望新增一個流程只需要在 flows/ 目錄下新增一個 Python 模組，
系統能自動發現並註冊它。
- 建立 FlowRegistry（類似 ToolRegistry 的模式）
- 自動掃描或裝飾器註冊機制
- Role 的 preferred_flow_mode 改為指向已註冊的 flow name
User Story P3：Tool/Agent 自動註冊
作為開發者，我希望新增 Tool 或 Agent 只需要新增檔案，
不需要修改 composition root。
- ToolRegistry 支援自動掃描 tools/ 目錄下所有 BaseTool 子類別
- agents/ 目錄下的 BaseAgent 子類別也能被自動發現
- Composition root 簡化為：auto_register_tools(), auto_register_agents()
User Story P4：即時視覺化基礎建設
作為使用者，我希望在 Gradio UI 中能看到目前流程的即時執行狀態圖。
- BaseFlowExecutor 增加 get_visualization() 方法
- 定義 FlowVisualization 資料模型（Mermaid 圖 + 目前節點高亮）
- Gradio UI 新增視覺化面板（可用 gr.HTML 或 gr.Plot 渲染 Mermaid）
- 流程執行時透過 callback 更新當前節點狀態
---
Spec 010：Flow Builder Agent Skill（程式碼產生技能）
目標：開發者用自然語言描述流程，OpenCode 自動產生完整的 LangGraph 程式碼。
Skill 使用情境
開發者：「幫我建立一個『美食推薦流程』：
  1. 先確認使用者的位置城市
  2. 查詢該城市天氣
  3. 根據天氣推薦室內或戶外餐廳
  4. 顯示餐廳評價和距離」
OpenCode（使用 flow-builder Skill）自動產生：
  ├── src/voice_assistant/flows/nodes/food/
  │   ├── location.py        # 城市確認節點
  │   ├── weather_check.py   # 天氣查詢節點
  │   ├── restaurant.py      # 餐廳推薦節點
  │   └── display.py         # 結果展示節點
  ├── src/voice_assistant/flows/graphs/food_recommender.py  # StateGraph 定義
  ├── src/voice_assistant/flows/state.py  # 新增 FoodRecommenderState
  ├── tests/unit/flows/test_food_recommender.py  # 測試
  └── Mermaid 流程圖預覽
Skill 內容（.opencode/skills/flow-builder/SKILL.md）
Skill 檔案將包含：
1. 觸發條件：當使用者說「建立流程」、「新增 flow」、「設計一個工作流」等關鍵字
2. 工作流程：
   - Step 1：解析自然語言，萃取流程步驟和節點
   - Step 2：識別需要使用的現有工具（WeatherTool、ExchangeRateTool 等）
   - Step 3：決定是否需要新工具
   - Step 4：產生 FlowState（TypedDict）
   - Step 5：產生各節點函式（遵循現有 nodes 慣例）
   - Step 6：產生 StateGraph 定義（含條件路由）
   - Step 7：產生 FlowExecutor 子類別（符合 BaseFlowExecutor 介面）
   - Step 8：產生 unit tests
   - Step 9：產生 Mermaid 流程圖
   - Step 10：將新流程註冊到 FlowRegistry
3. 程式碼模板：內含各類型節點、graph、state 的程式碼模板
4. 品質規則：
   - 遵循專案 SOLID 原則
   - 使用 Pydantic 驗證
   - 繁體中文註解
   - 自動產生 pytest 測試
5. 驗證步驟：
   - uv run ruff check .
   - uv run ruff format .
   - uv run pytest 新產生的測試
---
三、執行順序建議
Phase 1: Spec 009 — 架構重構（建議 5 個 User Story，約 30-40 tasks）
    ├── P1: BaseFlowExecutor 統一介面
    ├── P2: FlowRegistry + 自動發現
    ├── P3: Tool/Agent 自動註冊
    └── P4: Gradio UI 即時視覺化
Phase 2: Spec 010 — Flow Builder Skill（基於重構後的新架構）
    ├── P1: Skill 基礎框架（SKILL.md + 程式碼模板）
    ├── P2: 節點/Graph/State 程式碼產生邏輯
    └── P3: 驗證與測試產生
四、流程視覺化方案
在 Gradio UI 中即時顯示流程圖的技術方案：
- 使用 LangGraph 內建的 Mermaid 輸出 + gr.HTML 元件
- 利用 mermaid.js (https://mermaid.js.org/) 在瀏覽器端渲染 SVG
- 執行時透過 LangGraph 的 streaming callback 追蹤當前節點
- 用 CSS class 高亮目前正在執行的節點（綠色=完成、黃色=執行中、灰色=待執行）
- 透過 Gradio 的 yield 機制即時更新
---
五、風險與注意事項
| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| 重構影響現有 200+ 測試 | 高 | 先確保所有測試通過，逐步重構，每步驗證 |
| 自動發現機制可能引入循環 import | 中 | 使用 importlib 延遲載入 |
| Gradio UI 即時視覺化增加複雜度 | 中 | 先做靜態展示，再做即時高亮 |
| Skill 產生的程式碼品質不穩定 | 中 | 內建嚴格的程式碼模板和 lint 驗證 |
---
要我按照 spec-driven-development 流程開始嗎？先從 /speckit.specify 建立 Spec 009 的規格文件開始？