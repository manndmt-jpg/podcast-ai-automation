import os
import sys
from faster_whisper import WhisperModel

def transcribe_file(audio_path: str, out_dir: str, model_size: str = "small"):
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    txt_path = os.path.join(out_dir, base + ".txt")

    model = WhisperModel(model_size, device="auto", compute_type="int8")
    # Auto-detect language instead of forcing English
    segments, info = model.transcribe(audio_path)

    # Print detected language info
    print(f"Detected language: {info.language} (confidence: {info.language_probability:.2f})")

    # Track duration for cost calculation
    duration_seconds = 0
    with open(txt_path, "w", encoding="utf-8") as f:
        for s in segments:
            line = f"[{s.start:.2f} --> {s.end:.2f}] {s.text.strip()}"
            print(line)
            f.write(line + "\n")
            duration_seconds = max(duration_seconds, s.end)

    # Return both path and duration in minutes
    return txt_path, duration_seconds / 60.0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/transcribe.py <AUDIO_PATH> <OUT_DIR> [model_size]")
        sys.exit(1)
    audio_path = sys.argv[1]
    out_dir = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "small"
    out, duration = transcribe_file(audio_path, out_dir, model_size)
    print(f"Saved: {out} (Duration: {duration:.1f} minutes)")