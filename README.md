# Podcast-to-Summary Automation Project (macOS)

## Quick start
1. Install deps:
   ```zsh
   brew install ffmpeg
   python3 -m pip install -U faster-whisper feedparser requests openai
   ```
2. Open `config/feeds.json` and put your feeds.
3. Run the pipeline:
   ```zsh
   python3 automation/pipeline.py
   ```
4. Results go into `data/transcripts`, `data/cleaned`, `data/summaries`.

Environment variables (optional):
- `OPENAI_API_KEY` for cleaning and summaries.
