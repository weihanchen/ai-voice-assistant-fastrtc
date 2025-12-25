#!/usr/bin/env python
"""預先下載 TTS 模型

將 Kokoro 中文模型下載到指定目錄，供離線使用。

Usage:
    uv run python scripts/download_models.py

模型會下載到 TTS_MODEL_PATH 指定的目錄（預設：models/）
"""

import os
import sys
from pathlib import Path

# 確保可以 import 專案模組
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    from voice_assistant.config import get_settings

    settings = get_settings()
    cache_dir = Path(settings.tts_model_path).resolve()

    print("=" * 60)
    print("Kokoro TTS 中文模型下載")
    print("=" * 60)
    print(f"模型快取目錄: {cache_dir}")
    print()

    # 設定 HF_HOME
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_dir)

    print("正在下載模型（約 327MB）...")
    print("來源: hexgrad/Kokoro-82M-v1.1-zh")
    print()

    # 載入 KPipeline 會觸發模型下載
    from kokoro import KPipeline

    pipeline = KPipeline(
        lang_code="z",
        repo_id="hexgrad/Kokoro-82M-v1.1-zh",
    )

    print()
    print("=" * 60)
    print("下載完成！")
    print("=" * 60)
    print()
    print("模型已快取至:", cache_dir)
    print()
    print("離線使用方式:")
    print("  設定環境變數 HF_HUB_OFFLINE=1")
    print("  或在 .env 加入: HF_HUB_OFFLINE=1")
    print()

    # 測試生成
    print("測試語音合成...")
    for _gs, _ps, audio in pipeline("你好", voice="zf_xiaobei", speed=1.0):
        print(f"  生成音訊: {len(audio)} samples, {len(audio)/24000:.2f}s")

    print()
    print("測試成功！模型可正常使用。")


if __name__ == "__main__":
    main()
