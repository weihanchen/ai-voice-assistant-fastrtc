#!/usr/bin/env python
"""預先下載 TTS、ASR 和 VAD 模型

將 Kokoro 中文模型、faster-whisper 模型和 Silero VAD 模型下載到指定目錄，供離線使用。

Usage:
    uv run python scripts/download_models.py

模型會下載到 models/ 目錄：
- TTS: models/hub/ (HuggingFace cache)
- ASR: models/whisper/
- VAD: models/hub/ (Silero VAD，由 faster-whisper 自動下載)
"""

import os
import sys
from pathlib import Path

# 確保下載時不使用離線模式（必須在 import huggingface_hub 前設定）
os.environ.pop("HF_HUB_OFFLINE", None)

# 確保可以 import 專案模組
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def download_tts_model(cache_dir: Path) -> None:
    """下載 TTS 模型"""
    print("=" * 60)
    print("1. Kokoro TTS 中文模型下載")
    print("=" * 60)
    print(f"模型快取目錄: {cache_dir}")
    print()

    # 設定快取目錄
    cache_dir.mkdir(parents=True, exist_ok=True)
    hub_cache = cache_dir / "hub"
    hub_cache.mkdir(parents=True, exist_ok=True)

    print("正在下載模型（約 327MB）...")
    print("來源: hexgrad/Kokoro-82M-v1.1-zh")
    print()

    # 使用 huggingface_hub API 直接下載到指定目錄
    from huggingface_hub import snapshot_download

    repo_id = "hexgrad/Kokoro-82M-v1.1-zh"
    snapshot_download(
        repo_id=repo_id,
        cache_dir=str(hub_cache),
    )

    print("TTS 模型下載完成！")
    print()


def download_asr_model(cache_dir: Path, model_size: str = "tiny") -> None:
    """下載 ASR 模型"""
    print("=" * 60)
    print("2. faster-whisper ASR 模型下載")
    print("=" * 60)
    print(f"模型快取目錄: {cache_dir}")
    print(f"模型大小: {model_size}")
    print()

    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"正在下載 whisper-{model_size} 模型...")

    from faster_whisper import WhisperModel

    # 下載模型
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        download_root=str(cache_dir),
    )

    print("測試語音辨識模型載入...")
    print(f"  模型已載入: {model_size}")

    print("ASR 模型下載完成！")
    print()


def download_vad_model(cache_dir: Path) -> None:
    """下載 VAD 模型 (Silero VAD via HuggingFace)"""
    print("=" * 60)
    print("3. Silero VAD 模型下載")
    print("=" * 60)
    print(f"模型快取目錄: {cache_dir}")
    print()

    hub_cache = cache_dir / "hub"
    hub_cache.mkdir(parents=True, exist_ok=True)

    print("正在下載 Silero VAD 模型...")
    print("來源: freddyaboulton/silero-vad")
    print()

    # 使用 huggingface_hub API 下載 VAD 模型
    from huggingface_hub import snapshot_download

    repo_id = "freddyaboulton/silero-vad"
    snapshot_download(
        repo_id=repo_id,
        cache_dir=str(hub_cache),
    )

    print("VAD 模型下載完成！")
    print()


def main():
    from voice_assistant.config import get_settings

    settings = get_settings()

    # get_settings() 會讀取 .env，其中可能有 HF_HUB_OFFLINE=1
    # 下載時必須移除離線模式
    os.environ.pop("HF_HUB_OFFLINE", None)

    tts_cache_dir = Path(settings.tts_model_path).resolve()
    asr_cache_dir = Path(settings.whisper_model_path).resolve()

    print()
    print("=" * 60)
    print("AI Voice Assistant 模型下載")
    print("=" * 60)
    print()

    # 下載 TTS 模型
    download_tts_model(tts_cache_dir)

    # 下載 ASR 模型
    download_asr_model(asr_cache_dir, settings.whisper_model_size)

    # 下載 VAD 模型（與 TTS 共用 HF cache）
    download_vad_model(tts_cache_dir)

    print("=" * 60)
    print("所有模型下載完成！")
    print("=" * 60)
    print()
    print("模型位置:")
    print(f"  TTS: {tts_cache_dir}/hub/")
    print(f"  ASR: {asr_cache_dir}")
    print(f"  VAD: {tts_cache_dir}/hub/")
    print()
    print("離線使用方式:")
    print("  設定環境變數 HF_HUB_OFFLINE=1")
    print("  或在 .env 加入: HF_HUB_OFFLINE=1")
    print()


if __name__ == "__main__":
    main()
