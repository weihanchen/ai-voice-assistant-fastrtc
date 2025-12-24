"""Main entry point for AI Voice Assistant."""

from __future__ import annotations

import sys


def main() -> None:
    """啟動 AI Voice Assistant。"""
    try:
        from voice_assistant.config import Settings

        settings = Settings()
        print("AI Voice Assistant 已啟動")
        print(f"使用模型: {settings.openai_model}")
    except Exception as e:
        error_msg = str(e)
        if "openai_api_key" in error_msg.lower():
            print("錯誤: 請設定 OPENAI_API_KEY 環境變數")
            print("提示: 複製 .env.example 為 .env 並填入您的 API Key")
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
