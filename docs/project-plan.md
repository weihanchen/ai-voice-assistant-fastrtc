# AI 語音助理專案規劃方案

## 專案概述

| 項目 | 內容 |
|------|------|
| **專案名稱** | AI Voice Assistant (FastRTC) |
| **技術棧** | Python 3.14+ / uv / FastRTC / OpenAI API / Gradio / Docker |
| **開發方法** | Spec-Driven Development (GitHub Spec-Kit) |

---

## 一、架構設計

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
   │Moonshine│  │ ChatGPT  │  │ Kokoro  │
   │ (內建)  │  │  + Tools │  │ (內建)  │
   └─────────┘  └────┬─────┘  └─────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ 天氣API │  │ 匯率API │  │ 股價API │
   │  (免費) │  │  (免費) │  │  (免費) │
   └─────────┘  └─────────┘  └─────────┘
```

---

## 二、技術選型

| 層級 | 技術選擇 | 說明 |
|------|----------|------|
| **套件管理** | uv + venv | 快速、現代化的 Python 套件管理 |
| **容器化** | Docker + Compose v2 | 一致的開發/部署環境 |
| **語音輸入 (ASR)** | FastRTC 內建 Moonshine | 本地 CPU 推理，免費 |
| **語音輸出 (TTS)** | FastRTC 內建 Kokoro | 本地 CPU 推理，免費 |
| **LLM** | OpenAI GPT-4o-mini | 支援 function calling，成本低 |
| **UI** | Gradio (FastRTC 內建) | 一行啟動 WebRTC UI |
| **外部 API** | 免費公開 API | 詳見下方 |

### 外部 API 選擇

| 功能 | API | 說明 |
|------|-----|------|
| **天氣** | [Open-Meteo](https://open-meteo.com/) | 免費，無需 API Key |
| **匯率** | [Frankfurter](https://www.frankfurter.app/) | 免費，無需 API Key |
| **股價** | [yfinance](https://pypi.org/project/yfinance/) | 免費 Python 套件 |

---

## 三、Specs 規格結構

### 總覽

| 編號 | Spec 名稱 | 類型 | 說明 |
|------|-----------|------|------|
| **000** | `ai-voice-assistant` | 核心架構 | 專案骨架、LLM 整合、Tool 框架 |
| **001** | `fastrtc-voice-pipeline` | 功能模組 | FastRTC + ASR + TTS 語音管線 |
| **002** | `weather-query` | Tool | 天氣查詢工具 |
| **003** | `exchange-rate-query` | Tool | 匯率換算工具 |
| **004** | `stock-price-query` | Tool | 股價查詢工具 |

### 各 Spec 規格範圍

#### 000 - AI Voice Assistant (核心架構)

- 專案目標與使用者故事
- 能力範圍與限制
- 非功能需求 (延遲、可靠性)
- LLM Client 與 Tool Registry 架構設計
- 資料結構定義 (ToolResult、ChatMessage)

#### 001 - FastRTC Voice Pipeline (語音管線)

- ASR/TTS 需求與品質標準
- ReplyOnPause 行為定義
- Moonshine/Kokoro 配置需求
- Gradio UI 整合需求

#### 002 - Weather Query (天氣查詢)

- 使用者故事與查詢情境
- 支援城市範圍與名稱標準化
- Open-Meteo API 整合需求
- 錯誤處理與成功指標

#### 003 - Exchange Rate Query (匯率查詢)

- 使用者故事與換算情境
- 支援貨幣種類與代碼標準化
- Frankfurter API 整合需求
- 換算邏輯與成功指標

#### 004 - Stock Price Query (股價查詢)

- 使用者故事與查詢情境
- 支援市場 (台股/美股)
- yfinance 整合需求
- 股票名稱對應與成功指標

---

## 四、目錄結構

```
ai-voice-assistant-fastrtc/
├── .specify/                    # Spec-Kit 配置
├── specs/                       # 規格文件 (由 spec-kit 生成)
├── src/
│   └── voice_assistant/
│       ├── main.py              # 入口點 (FastRTC Stream)
│       ├── llm/                 # LLM 客戶端模組
│       ├── tools/               # 查詢工具模組
│       └── utils/               # 工具函式
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
000 核心架構
 ↓
001 語音管線
 ↓
002 天氣 ─┐
003 匯率 ─┼─ (可並行開發)
004 股價 ─┘
 ↓
整合測試
```

### Phase 對應

| Phase | 對應 Spec | 產出 |
|-------|-----------|------|
| **Phase 0** | 000 (部分) | 環境建置、pyproject.toml |
| **Phase 1** | 001 | FastRTC + ASR + TTS 基本對話 |
| **Phase 2** | 000 (完成) | LLM Client + Tool Registry |
| **Phase 3** | 002, 003, 004 | 三個查詢工具 |
| **Phase 4** | - | 端對端整合測試 |

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
FROM python:3.14-slim

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

- [GitHub Spec-Kit](https://github.com/github/spec-kit) - 規格驅動開發工具
- [Spec-Driven Development 介紹](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [FastRTC 官網](https://fastrtc.org/) - 實時通訊框架
- [FastRTC GitHub](https://github.com/gradio-app/fastrtc) - 原始碼與範例
- [Open-Meteo API](https://open-meteo.com/) - 天氣 API
- [Frankfurter API](https://www.frankfurter.app/) - 匯率 API
- [yfinance](https://pypi.org/project/yfinance/) - 股價查詢套件
- [Docker Compose v2](https://docs.docker.com/compose/) - 容器編排工具
