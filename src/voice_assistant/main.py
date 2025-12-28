"""Main entry point for AI Voice Assistant."""

from __future__ import annotations

import atexit
import os
import signal
import sys
import threading

# 全域變數用於 signal handler
_stream = None
_shutdown_event = threading.Event()


def _force_exit() -> None:
    """強制結束程式（用於 atexit）"""
    os._exit(0)


def _signal_handler(sig: int, frame: object) -> None:
    """處理終止信號，確保程式能正確關閉。"""
    print("\n正在關閉 AI Voice Assistant...")
    _shutdown_event.set()

    if _stream is not None and hasattr(_stream, "ui"):
        try:
            _stream.ui.close()
        except Exception:
            pass

    # 強制結束，避免 WebRTC 執行緒卡住
    print("程式已關閉")
    os._exit(0)


def main() -> None:
    """啟動 AI Voice Assistant。"""
    global _stream

    # 註冊 signal handlers
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # 註冊 atexit 確保清理
    atexit.register(_force_exit)

    try:
        from pathlib import Path

        from dotenv import load_dotenv

        # 載入 .env 環境變數（必須在任何 HuggingFace import 前執行）
        # 這確保 HF_HUB_OFFLINE=1 等設定被正確載入
        load_dotenv()

        from voice_assistant.config import get_settings

        settings = get_settings()

        # 設定 HF_HOME（必須在 import kokoro 前設定）
        # 這確保 TTS 模型從正確的目錄載入
        tts_model_path = Path(settings.tts_model_path).resolve()
        os.environ["HF_HOME"] = str(tts_model_path)

        from voice_assistant.voice.handlers import create_voice_stream

        print("AI Voice Assistant 啟動中...")
        print(f"LLM 模型: {settings.openai_model}")
        print(f"ASR 模型: faster-whisper ({settings.whisper_model_size})")
        print(f"TTS 音色: {settings.tts_voice}")

        # 建立語音串流
        _stream = create_voice_stream(settings)

        # 啟動 Gradio UI
        print(f"啟動 Gradio UI: http://{settings.server_host}:{settings.server_port}")
        print("按 Ctrl+C 可關閉程式")
        _stream.ui.launch(
            server_name=settings.server_host,
            server_port=settings.server_port,
            share=False,
        )
    except Exception as e:
        error_msg = str(e)
        if "openai_api_key" in error_msg.lower():
            print("錯誤: 請設定 OPENAI_API_KEY 環境變數")
            print("提示: 複製 .env.example 為 .env 並填入您的 API Key")
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
