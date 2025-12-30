# syntax=docker/dockerfile:1

# AI Voice Assistant - Production Dockerfile
# 使用多階段建構優化映像大小

# ============================================
# Stage 1: Builder - 安裝依賴
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# 安裝建構所需的系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 複製依賴定義檔
COPY pyproject.toml uv.lock ./

# 建立虛擬環境並安裝依賴（不含開發依賴）
RUN uv sync --frozen --no-dev --no-editable

# ============================================
# Stage 2: Runtime - 最終映像
# ============================================
FROM python:3.13-slim AS runtime

WORKDIR /app

# 安裝運行時系統依賴
# - ffmpeg: 音訊處理
# - libsndfile1: soundfile 套件需要
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 從 builder 階段複製虛擬環境
COPY --from=builder /app/.venv /app/.venv

# 設定環境變數
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 複製應用程式碼
COPY src/ ./src/
COPY pyproject.toml ./

# 建立非 root 使用者
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# 建立模型快取目錄
RUN mkdir -p /app/models

# 暴露 Gradio 預設埠
EXPOSE 7860

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860')" || exit 1

# 啟動應用
CMD ["python", "-m", "voice_assistant.main"]
