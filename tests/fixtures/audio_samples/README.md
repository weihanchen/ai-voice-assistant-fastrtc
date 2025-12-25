# Audio Samples for Testing

This directory contains audio samples for testing the voice pipeline.

## Sample Files

For integration testing, you can add:

- `hello_zh.wav` - Chinese "你好" greeting (16kHz, mono, 16-bit PCM)
- `silence.wav` - 1 second of silence for noise filtering tests
- `background_noise.wav` - Background noise for VAD testing

## Creating Test Samples

You can create test samples using:

```bash
# Generate 1 second of silence
ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 1 silence.wav

# Convert existing audio to correct format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav
```

## Usage in Tests

```python
import numpy as np
import soundfile as sf

# Load test audio
audio, sample_rate = sf.read("tests/fixtures/audio_samples/hello_zh.wav")
audio_tuple = (sample_rate, audio.astype(np.float32))
```

## Notes

- All audio files should be 16kHz mono for STT compatibility
- Use PCM format (.wav) for consistent behavior
- Audio files are not committed to git (too large)
