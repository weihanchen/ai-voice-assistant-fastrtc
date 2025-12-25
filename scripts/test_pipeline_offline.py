#!/usr/bin/env python
"""離線測試語音管線

使用預先生成的音訊或 TTS 合成音訊來測試整個 STT → LLM → TTS 流程，
無需麥克風即可驗證系統。

Usage:
    # 使用 TTS 生成測試音訊並測試完整流程
    uv run python scripts/test_pipeline_offline.py

    # 只生成測試音訊檔案
    uv run python scripts/test_pipeline_offline.py --generate-only

    # 使用現有音訊檔案測試
    uv run python scripts/test_pipeline_offline.py --audio-file path/to/audio.wav
"""

import argparse
import sys
from pathlib import Path

import numpy as np

# 確保可以 import 專案模組
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def generate_test_audio(text: str = "你好") -> tuple[int, np.ndarray]:
    """使用 TTS 生成測試音訊

    Args:
        text: 要合成的文字

    Returns:
        (sample_rate, audio_array) tuple
    """
    from voice_assistant.config import get_settings
    from voice_assistant.voice.tts.kokoro import KokoroTTS

    settings = get_settings()

    print(f"[生成] 使用 Kokoro TTS 合成: '{text}'")
    print("[生成] 首次執行會從 HuggingFace 下載中文模型（約 327MB）...")
    tts = KokoroTTS(
        voice=settings.tts_voice,
        speed=settings.tts_speed,
    )

    sample_rate, audio = tts.tts(text)
    print(f"[生成] 完成: sample_rate={sample_rate}, duration={len(audio)/sample_rate:.2f}s")

    return sample_rate, audio


def save_audio(audio: tuple[int, np.ndarray], path: Path) -> None:
    """儲存音訊到 WAV 檔案"""
    import wave

    sample_rate, audio_array = audio

    # 轉換為 int16
    if audio_array.dtype == np.float32:
        audio_int16 = (audio_array * 32767).astype(np.int16)
    else:
        audio_int16 = audio_array.astype(np.int16)

    path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(audio_int16.tobytes())

    print(f"[儲存] 音訊已儲存至: {path}")


def load_audio(path: Path) -> tuple[int, np.ndarray]:
    """從 WAV 檔案載入音訊"""
    import wave

    with wave.open(str(path), "rb") as wav:
        sample_rate = wav.getframerate()
        n_frames = wav.getnframes()
        audio_bytes = wav.readframes(n_frames)

    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
    print(f"[載入] 音訊: {path}, sample_rate={sample_rate}, duration={len(audio_array)/sample_rate:.2f}s")

    return sample_rate, audio_array


def resample_audio(
    audio: tuple[int, np.ndarray], target_sample_rate: int = 48000
) -> tuple[int, np.ndarray]:
    """重新取樣音訊到目標取樣率

    FastRTC 預設使用 48kHz，所以需要將 TTS 輸出（通常是 24kHz）轉換。
    """
    from scipy import signal

    sample_rate, audio_array = audio

    if sample_rate == target_sample_rate:
        return audio

    # 計算重新取樣的比例
    num_samples = int(len(audio_array) * target_sample_rate / sample_rate)
    resampled = signal.resample(audio_array, num_samples)

    print(f"[重新取樣] {sample_rate}Hz → {target_sample_rate}Hz")

    return target_sample_rate, resampled.astype(audio_array.dtype)


def test_pipeline(audio: tuple[int, np.ndarray]) -> None:
    """測試完整語音管線

    Args:
        audio: (sample_rate, audio_array) 測試音訊
    """
    from voice_assistant.config import get_settings
    from voice_assistant.llm.client import LLMClient
    from voice_assistant.voice.pipeline import VoicePipeline
    from voice_assistant.voice.schemas import VoicePipelineConfig

    settings = get_settings()

    print("\n" + "=" * 60)
    print("測試語音管線")
    print("=" * 60)

    # 初始化元件
    print("\n[初始化] 建立 LLM Client...")
    llm_client = LLMClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )

    print("[初始化] 建立 VoicePipeline...")
    config = VoicePipelineConfig(
        stt={
            "model_size": settings.whisper_model_size,
            "language": settings.whisper_language,
            "device": settings.whisper_device,
        },
        tts={"voice": settings.tts_voice, "speed": settings.tts_speed},
        vad={
            "pause_threshold_ms": settings.vad_pause_threshold_ms,
            "min_speech_duration_ms": settings.vad_min_speech_duration_ms,
            "speech_threshold": settings.vad_speech_threshold,
        },
    )

    pipeline = VoicePipeline(config=config, llm_client=llm_client)

    # 準備音訊（確保格式正確）
    sample_rate, audio_array = audio

    # 轉換為 int16（模擬 FastRTC 輸入）
    if audio_array.dtype == np.float32:
        audio_array = (audio_array * 32767).astype(np.int16)

    # 加入 batch 維度（模擬 FastRTC 格式）
    if audio_array.ndim == 1:
        audio_array = audio_array.reshape(1, -1)

    test_audio = (sample_rate, audio_array)

    print(f"\n[測試] 輸入音訊: sample_rate={sample_rate}, shape={audio_array.shape}")
    print("[測試] 開始處理...\n")

    # 執行管線
    output_chunks = []
    for chunk in pipeline.process_audio(test_audio):
        output_chunks.append(chunk)

    print(f"\n[結果] 共產生 {len(output_chunks)} 個音訊片段")

    if output_chunks:
        total_samples = sum(len(chunk[1]) for chunk in output_chunks)
        sample_rate = output_chunks[0][0]
        duration = total_samples / sample_rate
        print(f"[結果] 總時長: {duration:.2f} 秒")

        # 儲存輸出音訊
        output_path = Path("tests/fixtures/audio_samples/pipeline_output.wav")
        combined_audio = np.concatenate([chunk[1] for chunk in output_chunks])
        save_audio((sample_rate, combined_audio), output_path)
    else:
        print("[結果] 無音訊輸出（可能是 STT 沒有辨識到有效語音）")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="離線測試語音管線")
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="只生成測試音訊，不執行管線測試",
    )
    parser.add_argument(
        "--audio-file",
        type=Path,
        help="使用指定的音訊檔案進行測試",
    )
    parser.add_argument(
        "--text",
        type=str,
        default="你好，請問今天天氣怎麼樣？我想出門散步。",
        help="要合成的測試文字（預設：較長句子以通過 VAD）",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=48000,
        help="目標取樣率（預設：48000，與 FastRTC 相同）",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("離線語音管線測試工具")
    print("=" * 60)

    if args.audio_file:
        # 使用現有音訊檔案
        if not args.audio_file.exists():
            print(f"錯誤: 找不到音訊檔案 {args.audio_file}")
            sys.exit(1)
        audio = load_audio(args.audio_file)
    else:
        # 生成測試音訊
        audio = generate_test_audio(args.text)

        # 儲存生成的音訊
        output_path = Path(f"tests/fixtures/audio_samples/test_{args.text}.wav")
        save_audio(audio, output_path)

    # 重新取樣到目標取樣率
    audio = resample_audio(audio, args.sample_rate)

    if args.generate_only:
        print("\n已生成測試音訊，跳過管線測試。")
        return

    # 測試管線
    test_pipeline(audio)


if __name__ == "__main__":
    main()
