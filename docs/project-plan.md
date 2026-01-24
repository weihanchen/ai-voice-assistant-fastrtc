# AI 語音助理專案規劃方案

## 專案概述

| 項目 | 內容 |
|------|------|
| **專案名稱** | AI Voice Assistant (FastRTC) |
| **技術棧** | Python 3.13 / uv / FastRTC / OpenAI API / LangGraph / Gradio / Docker |
| **開發方法** | Spec-Driven Development (GitHub Spec-Kit) |

---

## 一、架構設計

### 1.1 基礎架構（Phase 1-5 已完成）

```
┌─────────────────────────────────────────────────────────┐
│                    Gradio WebRTC UI                      │
│                  (內建於 FastRTC)                         │
└─────────────────────┬───────────────────────────────────┘
                      │ Audio Stream
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   FastRTC Stream                         │
│              (ReplyOnPause Handler)                      │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌─────────┐
   │   ASR   │  │   LLM    │  │   TTS   │
   │ Whisper │  │ ChatGPT  │  │ Kokoro  │
   │ (中文)  │  │  + Tools │  │ (中文)  │
   └─────────┘  └────┬─────┘  └─────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ 天氣API │  │ 匯率API │  │ 股價API │
   │  (免費) │  │  (免費) │  │  (免費) │
   └─────────┘  └─────────┘  └─────────┘
```

### 1.2 LangGraph 流程架構（Phase 6 已完成）

```
┌──────────────────────────────────────────────────────────────────┐
│                    LangGraph 流程路由                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [START] ──▶ 意圖分類 ──┬──▶ 天氣查詢 (Tool) ──▶ [END]          │
│                         │                                        │
│                         ├──▶ 匯率查詢 (Tool) ──▶ [END]          │
│                         │                                        │
│                         ├──▶ 股票查詢 (Tool) ──▶ [END]          │
│                         │                                        │
│                         └──▶ 旅遊規劃 (SubGraph) ──▶ [END]      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  旅遊規劃子流程 (SubGraph)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [進入] ──▶ 解析目的地 ──▶ 查詢天氣 ──▶ 評估天氣               │
│                                          │                      │
│                                    ┌─────┴─────┐                │
│                                  適合         不適合             │
│                                    │            │                │
│                                    ▼            ▼                │
│                              產生推薦      建議備案              │
│                                    │            │                │
│                                    └─────┬──────┘                │
│                                          ▼                      │
│                                    回應使用者 ──▶ [離開]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 多代理協作架構（Phase 7 已完成）

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Agent 協作流程                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [START] ──▶ Supervisor Agent ──▶ 任務拆解與分派               │
│                     │                                           │
│         ┌───────────┼───────────┬───────────┐                  │
│         ▼           ▼           ▼           ▼                  │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│    │ Weather │ │ Finance │ │ Travel  │ │ General │            │
│    │  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │            │
│    │ (天氣)  │ │(匯率+股)│ │ (旅遊)  │ │ (閒聊)  │            │
│    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘            │
│         │           │           │           │                  │
│         └───────────┴─────┬─────┴───────────┘                  │
│                           ▼                                     │
│                    Aggregator（彙整結果）                        │
│                           │                                     │
│                           ▼                                     │
│                      [END] 回應使用者                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

特點：
• 一次請求可觸發多個 Agent 並行協作
• 各 Agent 重用現有 Tool（不重寫）
• Supervisor 負責任務拆解與結果彙整
```

### 1.4 角色切換架構（Phase 8 規劃中）

```
┌─────────────────────────────────────────────────────────────────┐
│                     角色切換系統架構                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [START] ──▶ 意圖分析 ──┬──▶ 一般對話 (現有流程)              │
│                        │                                       │
│                        ├──▶ 角色切換 ──▶ RoleManager             │
│                        │                                       │
│                        │                    │                    │
│                        │                    ▼                    │
│                        │            ┌─────────────┐              │
│                        │            │  Interviewer │              │
│                        │            │  Role Config │              │
│                        │            └──────┬──────┘              │
│                        │                   │                    │
│                        │            ┌──────┴──────┐              │
│                        │            │系統提示詞注入│              │
│                        │            │  LLM 調用    │              │
│                        │            └──────┬──────┘              │
│                        │                   │                    │
│                        │            ┌──────┴──────┐              │
│                        │            │ 追問模板生成 │              │
│                        │            └──────┬──────┘              │
│                        │                   │                    │
│                        └──────────────────┴────────────────────┘
│                                                                 │
│ UI 層：                                                          │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │  角色選擇器（Radio Button）    [預設] [面試官]              │   │
│ │  當前角色標籤：🏷️ 面試官模式                               │   │
│ │  語音對話介面 + 即時狀態顯示                              │   │
│ └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

特點：
• 動態系統提示詞切換，不改變核心架構
• 面試官角色具備深度追問能力
• 支援語音指令自動切換（「切換到面試官」）
• UI 即時顯示當前角色狀態
```

---

## 二、技術選型

| 層級 | 技術選擇 | 說明 |
|------|----------|------|
| **套件管理** | uv + venv | 快速、現代化的 Python 套件管理 |
| **容器化** | Docker + Compose v2 | 一致的開發/部署環境 |
| **語音輸入 (ASR)** | faster-whisper (small) | 本地 CPU 推理，支援中文 |
| **語音輸出 (TTS)** | Kokoro (kokoro + misaki[zh]) | 本地 CPU 推理，中文模型 |
| **LLM** | OpenAI GPT-4o-mini | 支援 function calling，成本低 |
| **流程編排** | LangGraph | 狀態機流程、視覺化、可擴展 |
| **UI** | Gradio (FastRTC 內建) | 一行啟動 WebRTC UI |
| **外部 API** | 免費公開 API | 詳見下方 |

### 外部 API 選擇

| 功能 | API | 說明 |
|------|-----|------|
| **天氣** | [Open-Meteo](https://open-meteo.com/) | 免費，無需 API Key |
| **匯率** | [ExchangeRate-API](https://www.exchangerate-api.com/) | 免費方案 1,500 次/月，支援 TWD |
| **股價** | [yfinance](https://pypi.org/project/yfinance/) | 免費 Python 套件 |

---

## 三、Specs 規格結構

### 總覽

| 編號 | Spec 名稱 | 類型 | 狀態 | 說明 |
|------|-----------|------|------|------|
| **000** | `ai-voice-assistant` | 核心架構 | ✅ 完成 | 專案骨架、LLM 整合、Tool 框架 |
| **001** | `fastrtc-voice-pipeline` | 功能模組 | ✅ 完成 | FastRTC + ASR + TTS 語音管線 |
| **002** | `weather-query` | Tool | ✅ 完成 | 天氣查詢工具 |
| **003** | `exchange-rate-query` | Tool | ✅ 完成 | 匯率換算工具 |
| **004** | `stock-price-query` | Tool | ✅ 完成 | 股價查詢工具 |
| **005** | `realtime-conversation-ui` | UI 增強 | ✅ 完成 | 即時對話顯示介面 |
| **006** | `langgraph-travel-flow` | 流程編排 | ✅ 完成 | LangGraph 旅遊規劃流程 |
| **007** | `multi-agent-collaboration` | 多代理 | ✅ 完成 | 多代理協作系統 |
| **008** | `role-switching-interviewer` | 角色系統 | 📋 規劃中 | 角色切換與面試官模式 |

### 各 Spec 規格範圍

#### 000 - AI Voice Assistant (核心架構)

- 專案目標與使用者故事
- 能力範圍與限制
- 非功能需求 (延遲、可靠性)
- LLM Client 與 Tool Registry 架構設計
- 資料結構定義 (ToolResult、ChatMessage)
- 此階段並非完整功能實作， 僅專案能夠長出骨架並啟動為原則

#### 001 - FastRTC Voice Pipeline (語音管線)

- FastRTC 語音管線，整合 faster-whisper ASR 與 Kokoro TTS（中文）
- ASR/TTS 需求與品質標準
- ReplyOnPause 行為定義（0.5 秒停頓閾值）
- faster-whisper/Kokoro 配置需求
- Gradio UI 整合需求

#### 002 - Weather Query (天氣查詢)

- 使用者故事與查詢情境
- 支援城市範圍與名稱標準化
- Open-Meteo API 整合需求
- 錯誤處理與成功指標

#### 003 - Exchange Rate Query (匯率查詢)

- 使用者故事與換算情境
- 支援貨幣種類與代碼標準化
- ExchangeRate-API 整合需求
- 換算邏輯與成功指標

#### 004 - Stock Price Query (股價查詢)

- 使用者故事與查詢情境
- 支援市場 (台股/美股)
- yfinance 整合需求
- 股票名稱對應與成功指標

#### 005 - Realtime Conversation UI (即時對話顯示)

- 使用者故事：即時查看語音辨識與回應文字
- 對話歷史顯示區（類似聊天介面）
- 當前狀態指示（閒置/聆聯/處理中/回應中）
- ASR 辨識文字即時顯示
- AI 回應文字即時顯示
- 與現有 Gradio WebRTC UI 整合

#### 006 - LangGraph Travel Flow (旅遊規劃流程)

- **目標**：展示 LangGraph 流程編排能力，同時保留現有 Tool 功能
- **核心功能**：
  - LangGraph StateGraph 整合
  - 意圖分類路由（天氣/匯率/股票/旅遊）
  - 旅遊規劃多步驟流程（SubGraph）
  - 流程視覺化輸出（Mermaid 圖）
- **旅遊規劃流程**：
  - 解析目的地城市
  - 查詢目的地天氣（整合現有 WeatherTool）
  - 根據天氣條件分支：適合出遊 vs 建議備案
  - 產生旅遊建議回應
- **設計原則**：
  - 100% 保留現有 Tool 功能
  - 增量式引入 LangGraph
  - 清楚對比 Tool vs Flow 的使用時機

#### 007 - Multi-Agent Collaboration (多代理協作)

- **目標**：展示多代理協作能力，實現複雜任務的自動拆解與並行處理
- **核心功能**：
  - Supervisor Agent：任務理解、拆解、分派與結果彙整
  - 專家 Agent 群：Weather / Finance / Travel / General
  - Agent 間通訊協定與狀態管理
  - 並行執行與結果聚合
- **Demo 場景**：
  - 智慧旅遊規劃：「我下週想去台中玩」→ 同時查天氣 + 規劃行程
  - 個人財務助理：「查台積電股價和美金匯率」→ 並行查詢兩個資訊
  - 出差行程助理：「後天去東京出差」→ 天氣 + 匯率 + 注意事項
- **設計原則**：
  - 100% 保留現有流程（006 的 main_router 不動）
  - 重用所有現有 Tool（Agent 只是包裝層）
  - 可透過設定切換流程模式（tools / langgraph / multi_agent）

#### 008 - Role Switching: Interviewer (角色切換系統)

- **目標**：實現動態角色切換功能，以面試官為 MVP 展示 Prompt Engineering 應用
- **核心功能**：
  - Role 基礎架構與註冊機制
  - 面試官角色配置（正式語氣、深度追問）
  - 意圖識別支援角色切換指令
  - Gradio UI 角色選擇器與即時狀態顯示
- **場景展示**：
  - 使用者對麥克風練習自我介紹
  - AI 針對回答內容進行深度追問（具體細節、問題解決過程）
  - 語音指令「切換到面試官」自動切換模式
- **設計原則**：
  - 最小侵入性：重用現有 LLMClient.system_prompt 參數
  - 擴展性：為未來新角色保留接口（不實作自定義角色）
  - 語言一致性：以繁體中文為主，無需多語言支援
  - 無持久化需求：單次對話內的角色切換即可

---

## 四、目錄結構

```
ai-voice-assistant-fastrtc/
├── .specify/                    # Spec-Kit 配置
├── specs/                       # 規格文件 (由 spec-kit 生成)
├── src/
│   └── voice_assistant/
│       ├── main.py              # 入口點 (FastRTC Stream)
│       ├── config.py            # 環境變數配置
│       ├── llm/                 # LLM 客戶端模組
│       ├── tools/               # 查詢工具模組
│       ├── flows/               # LangGraph 流程模組 (006)
│       │   ├── state.py         # FlowState 定義
│       │   ├── graphs/          # 流程圖
│       │   │   ├── main_router.py    # 主路由流程
│       │   │   └── travel_planner.py # 旅遊規劃子流程
│       │   └── nodes/           # 流程節點
│       ├── agents/              # 多代理模組 (007)
│       │   ├── __init__.py
│       │   ├── base.py          # Agent 基底類別
│       │   ├── supervisor.py    # Supervisor Agent
│       │   ├── weather.py       # Weather Agent
│       │   ├── finance.py       # Finance Agent (匯率+股票)
│       │   ├── travel.py        # Travel Agent
│       │   └── graph.py         # 多代理協作流程圖
│       ├── roles/               # 🆕 角色系統模組 (008)
│       │   ├── __init__.py
│       │   ├── base.py          # Role 基底類別
│       │   ├── registry.py      # 角色註冊中心
│       │   ├── interviewer.py    # 面試官角色
│       │   └── manager.py       # 角色管理器
│       └── voice/               # 語音管線模組
├── tests/
├── Dockerfile
├── compose.yaml
├── pyproject.toml
└── .env.example
```

---

## 五、開發流程與階段

### Spec-Kit 標準流程

每個 Spec 依序執行：

```
/speckit.specify  →  撰寫 spec.md (定義 What & Why)
        ↓
/speckit.plan     →  撰寫 plan.md (定義 How)
        ↓
/speckit.tasks    →  撰寫 tasks.md (拆解可執行任務)
        ↓
/speckit.implement →  逐一實作任務
```

### 開發順序

```
000 核心架構        ✅
 ↓
001 語音管線        ✅
 ↓
002 天氣 ─┐
003 匯率 ─┼─ ✅ (可並行開發)
004 股價 ─┘
 ↓
005 即時對話 UI     ✅
 ↓
整合測試            ✅
 ↓
006 LangGraph 流程  ✅
  ↓
007 多代理協作      ✅ 完成
  ↓
008 角色切換系統      📋 規劃中
```

### Phase 對應

| Phase | 對應 Spec | 產出 | 狀態 |
|-------|-----------|------|------|
| **Phase 0** | 000 (部分) | 環境建置、pyproject.toml | ✅ 完成 |
| **Phase 1** | 001 | FastRTC + ASR + TTS 基本對話 | ✅ 完成 |
| **Phase 2** | 000 (完成) | LLM Client + Tool Registry | ✅ 完成 |
| **Phase 3** | 002, 003, 004 | 三個查詢工具 | ✅ 完成 |
| **Phase 4** | - | 端對端整合測試 | ✅ 完成 |
| **Phase 5** | 005 | 即時對話 UI 顯示 | ✅ 完成 |
| **Phase 6** | 006 | LangGraph 流程編排 + 旅遊規劃 | ✅ 完成 |
| **Phase 7** | 007 | 多代理協作系統 | ✅ 完成 |
| **Phase 8** | 008 | 角色切換系統 | 📋 規劃中 |

### 教學文章對應

本專案設計為漸進式教學範例，各篇章對應不同架構層級：

| 篇章 | 主題 | 對應 Spec | 核心概念 |
|------|------|-----------|----------|
| **第一篇** | 標準 Tool 呼叫 | 000-004 | LLM + Function Calling |
| **第二篇** | LangGraph Flow | 006 | StateGraph + 意圖路由 + SubGraph |
| **第三篇** | 多代理協作 | 007 | Supervisor + 專家 Agent + 並行處理 |
| **第四篇** | 角色切換 | 008 | Prompt Engineering + 動態角色管理 |

**切換模式**（規劃中）：
```python
# .env 或 config.py
FLOW_MODE = "tools"        # 第一篇：純 Tool 呼叫
FLOW_MODE = "langgraph"    # 第二篇：LangGraph 流程
FLOW_MODE = "multi_agent"  # 第三篇：多代理協作
```

---

### 四、目錄結構

---

## 六、快速開始

### 1. 初始化專案環境

```bash
# 建立虛擬環境
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安裝 spec-kit CLI
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# 初始化 spec-kit
specify init . --ai claude
```

### 2. 執行 Spec-Kit 流程

```bash
# 在 Claude Code 中依序執行：
/speckit.constitution    # 定義專案原則
/speckit.specify         # 撰寫需求規格
/speckit.plan            # 技術計畫
/speckit.tasks           # 生成任務
/speckit.implement       # 開始實作
```

### 3. Docker 啟動 (生產環境)

```bash
# 使用 Docker Compose v2 啟動
docker compose up -d

# 查看日誌
docker compose logs -f

# 停止服務
docker compose down
```

---

## 七、Docker 配置範例

### Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# 安裝系統依賴 (音訊處理所需)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 複製專案檔案
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

# 暴露 Gradio 預設埠
EXPOSE 7860

# 啟動應用
CMD ["uv", "run", "python", "-m", "voice_assistant.main"]
```

### compose.yaml

```yaml
services:
  voice-assistant:
    build: .
    ports:
      - "7860:7860"
    env_file:
      - .env
    environment:
      - GRADIO_SERVER_NAME=0.0.0.0
    volumes:
      - ./src:/app/src:ro  # 開發時熱載入 (可選)
    restart: unless-stopped
```

---

## 八、參考資源

### 核心框架

- [GitHub Spec-Kit](https://github.com/github/spec-kit) - 規格驅動開發工具
- [Spec-Driven Development 介紹](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [FastRTC 官網](https://fastrtc.org/) - 實時通訊框架
- [FastRTC GitHub](https://github.com/gradio-app/fastrtc) - 原始碼與範例

### LangGraph 流程編排

- [LangGraph 官方文件](https://langchain-ai.github.io/langgraph/) - 流程編排框架
- [LangGraph Workflows and Agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) - 工作流與代理設計
- [LangGraph Visualization](https://kitemetric.com/blogs/visualizing-langgraph-workflows-with-get-graph) - 流程視覺化

### 外部 API

- [Open-Meteo API](https://open-meteo.com/) - 天氣 API
- [ExchangeRate-API](https://www.exchangerate-api.com/) - 匯率 API (支援 TWD)
- [yfinance](https://pypi.org/project/yfinance/) - 股價查詢套件

### 部署工具

- [Docker Compose v2](https://docs.docker.com/compose/) - 容器編排工具
