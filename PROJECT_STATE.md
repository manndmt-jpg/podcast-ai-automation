# 📌 Podcast Summary Project — Current State

## ✅ What Works
- **Feed fetching**: pulls latest episode info from multiple RSS feeds (9 feeds configured).
- **Audio download**: MP3s saved into `data/audio/`.
- **Language detection**: Whisper auto-detects spoken language during transcription.
- **Transcription**: local faster-whisper (`small` model) in original language (FREE).
- **Translation**: Claude 3.5 Haiku automatically translates non-English transcripts to English (32k token limit for long episodes).
- **YouTube processing**: Parallel pipeline for on-demand YouTube video processing via text file input.
- **Chapter extraction**: AI-generated topic-based chapters for episodes 45+ minutes.
- **Quote integration**: Inline memorable quotes embedded within relevant summary sections.
- **Summarisation**: Claude Sonnet 4 generates structured summaries with quotes from English text.
- **Auto-tagging**: Claude generates topical tags from summaries, merged with static feed tags.
- **Cost tracking**: Comprehensive monitoring of all AI service costs with detailed breakdowns.
- **Metadata**: sidecar `.meta.json` files with podcast name, episode title, published date, URL, and combined tags.
- **Seen log**: processed episodes tracked in `data/seen.json` to avoid duplicates.
- **Push to Notion**: summaries + metadata create pages in Notion with formatting and tags.
- **Cron automation**: runs every 2 hours automatically via `run_cron.sh`.
- **Evaluation suite**: 9 comprehensive monitoring scripts for health, quality, and performance analysis.
- **Automated evaluations**: daily evaluation suite runs at 10 AM via cron.

## ✅ Recently Completed
- **YouTube pipeline**: Built parallel processing system for YouTube videos with simple text file input (config/youtube_links.txt).
- **Translation fix**: Increased max_tokens from 8k to 32k to handle long German podcasts (Doppelgänger Tech Talk).
- **YouTube integration**: Reuses 90% of existing codebase - only download and metadata extraction are new.
- **Feed expansion**: Added "The Diary of a CEO" to RSS feed list (9 total feeds).
- **Chapter extraction**: AI-generated topic-based chapters for episodes 45+ minutes (timestamps removed for simplicity).
- **Quote integration**: Inline quotes embedded within relevant summary sections with proper formatting.
- **Cost tracking system**: Comprehensive monitoring of AI service costs with detailed breakdowns.
- **Free local Whisper**: Updated to reflect $0.00 cost for local faster-whisper transcription.
- **Evaluation suite**: Built comprehensive monitoring system with 9 scripts for health, quality, cost, and performance analysis.

## 🚀 Next Steps
1. Add export options (e.g. Readwise, Obsidian).
2. Experiment with **cheaper/faster models** for cost optimization.
3. Consider AI agent integration for advanced automation.  

## 📂 Structure
- `automation/pipeline.py` → orchestrates RSS feed workflow.
- `automation/youtube_pipeline.py` → orchestrates YouTube video workflow.
- `scripts/` → modular helpers:
  - `fetch_feed.py` → RSS feed parsing
  - `download_audio.py` → MP3 downloading
  - `download_youtube.py` → YouTube audio extraction via yt-dlp
  - `extract_youtube_metadata.py` → YouTube metadata extraction
  - `transcribe.py` → local faster-whisper transcription with language detection
  - `translate.py` → Claude-powered translation (32k token limit)
  - `extract_chapters.py` → AI chapter generation for long episodes
  - `summarise_with_quotes.py` → Claude Sonnet 4 summarization with inline quotes
  - `push_to_notion.py` → Notion integration
- `utils/cost_tracker.py` → AI service cost monitoring and reporting
- `config/feeds.json` → 9 podcast feeds with static tags (EN/DE).
- `config/youtube_links.txt` → YouTube URLs for on-demand processing.
- `data/` → storage for audio, transcripts, translations, summaries, metadata, seen.json.
- `run_cron.sh` → cron job wrapper script for RSS feeds.
- `process_youtube.sh` → convenience script for YouTube processing.
- `evals/` → comprehensive evaluation scripts:
  - `feed_health.py` → RSS feed monitoring
  - `quality_check.py` → content quality analysis
  - `processing_stats.py` → performance metrics
  - `view_costs.py` → enhanced cost reporting
  - `duplicate_analysis.py` → duplicate detection
  - `eval_runner.py` → centralized evaluation runner
  - `view_eval_logs.py` → evaluation log viewer
  - `explain_warnings.py` → issue troubleshooting
  - `test_cost_tracking.py` → cost tracking validation
- `logs/cron.log` → pipeline execution logs.
- `logs/costs.log` → detailed AI service cost breakdowns.
- `logs/eval_*.log` → evaluation results and health monitoring.

## 💰 Cost Tracking
- **Whisper Transcription**: FREE (local faster-whisper)
- **Claude Translation**: ~$1 per 1M input tokens (Haiku)
- **Claude Summarization**: ~$3 per 1M input tokens (Sonnet 4)
- **Claude Auto-tagging**: ~$1 per 1M input tokens (Haiku)
- **Daily/monthly reporting**: Automated cost summaries and episode breakdowns
- **Current month**: $3.16 (9 episodes processed)
- **Daily average**: ~$0.22 (2 episodes typical)

## 🌍 Supported Languages
**Primary**: English, German
**Full Support**: French, Spanish, Italian, Portuguese, Dutch, Polish, Russian, Japanese, Korean, Chinese, Arabic, Hindi

## 🤖 Automation Status
- **RSS pipeline**: Running every 2 hours via cron (✅ Working)
- **YouTube pipeline**: On-demand via `process_youtube.sh` (✅ Working)
- **Daily evaluations**: Running at 10 AM via cron (✅ Working)
- **Feed health**: All 9 feeds healthy and operational
- **Processing efficiency**: 100% success rate for available episodes
- **Translation quality**: Fixed German podcast truncation issue (32k token limit)
- **System status**: Production-ready with comprehensive monitoring

## 📺 YouTube Processing
- **Input**: Add URLs to `config/youtube_links.txt` (one per line)
- **Run**: `~/podcast_summary_project/process_youtube.sh`
- **Features**: Auto-skips processed videos, handles any language, full cost tracking
- **Tested**: 2 videos successfully processed (18 min and 100 min)

---

_Last updated: October 4, 2025_
