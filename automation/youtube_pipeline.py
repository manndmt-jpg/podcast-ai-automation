# automation/youtube_pipeline.py

import os
import re
import json
import sys
import pathlib
import time
from datetime import datetime

# Make "scripts" and "utils" importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.download_youtube import download_youtube_audio
from scripts.extract_youtube_metadata import get_youtube_metadata
from scripts.transcribe import transcribe_file
from scripts.translate import translate_transcript
from scripts.summarise_with_quotes import summarise_with_sonnet
from scripts.push_to_notion import main as push_to_notion_main
from utils.cost_tracker import CostTracker
from utils.date_utils import to_iso_date

# Import auto-tagging function from main pipeline
from automation.pipeline import generate_auto_tags_from_summary, log_with_timestamp

DATA = ROOT / "data"
AUDIO_DIR = DATA / "audio"
TRANS_DIR = DATA / "transcripts"
SUM_DIR = DATA / "summaries"
YOUTUBE_LINKS_FILE = ROOT / "config" / "youtube_links.txt"
SEEN_FILE = DATA / "seen.json"


def slugify(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")[:120]


def load_seen() -> dict:
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen: dict) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2)


# Removed: Now using utils.date_utils.to_iso_date()


def process_youtube_video(url: str, cost_tracker: CostTracker) -> None:
    """Process a single YouTube video through the pipeline"""

    log_with_timestamp(f"== Processing YouTube video ==")
    log_with_timestamp(f"URL: {url}")

    # 1) Extract metadata first
    try:
        metadata = get_youtube_metadata(url)
    except Exception as e:
        log_with_timestamp(f"ERROR: Failed to extract metadata: {e}")
        return

    video_id = metadata.get("id")
    title = metadata.get("title", "Untitled")
    channel = metadata.get("channel", "Unknown Channel")

    # Convert upload date to ISO format
    upload_date = metadata.get("upload_date", "")
    if upload_date:
        try:
            upload_date = to_iso_date(upload_date)
        except ValueError:
            log_with_timestamp(f"Warning: Could not parse date '{upload_date}', using as-is")

    log_with_timestamp(f"Video: {title}")
    log_with_timestamp(f"Channel: {channel}")
    log_with_timestamp(f"Published: {upload_date}")

    # Check if already processed
    seen = load_seen()
    youtube_key = "YouTube"
    seen_ids = set(seen.get(youtube_key, []))

    if video_id in seen_ids:
        log_with_timestamp(f"Skipping. Already processed: {title}")
        return

    # 2) Download audio
    base = f"{slugify(channel)}__{slugify(title)}"
    try:
        mp3_path = download_youtube_audio(url, str(AUDIO_DIR), base)
        log_with_timestamp(f"Audio: {mp3_path}")
    except Exception as e:
        log_with_timestamp(f"ERROR: Failed to download audio: {e}")
        return

    # 3) Transcribe
    try:
        txt_path, audio_duration = transcribe_file(mp3_path, str(TRANS_DIR), model_size="small")
        log_with_timestamp(f"Transcript: {txt_path} ({audio_duration:.1f} min)")

        # Track Whisper cost
        cost_tracker.log_whisper_cost(audio_duration, title)
    except Exception as e:
        log_with_timestamp(f"ERROR: Failed to transcribe: {e}")
        return

    # 4) Translate if needed
    try:
        final_txt_path, translation_usage = translate_transcript(txt_path, str(TRANS_DIR))
        if final_txt_path != txt_path:
            log_with_timestamp(f"Translation: {final_txt_path}")
            if translation_usage:
                cost_tracker.log_claude_cost(
                    "claude-3-5-haiku-20241022",
                    translation_usage.input_tokens,
                    translation_usage.output_tokens,
                    "Translation",
                    title
                )
    except Exception as e:
        log_with_timestamp(f"ERROR: Failed to translate: {e}")
        return

    # 5) Summarise with Sonnet
    try:
        out_path, summary_usage = summarise_with_sonnet(final_txt_path, str(SUM_DIR))
        log_with_timestamp(f"Summary: {out_path}")
        if summary_usage:
            cost_tracker.log_claude_cost(
                "claude-sonnet-4-20250514",
                summary_usage.input_tokens,
                summary_usage.output_tokens,
                "Summary",
                title
            )
    except Exception as e:
        log_with_timestamp(f"ERROR: Failed to summarize: {e}")
        return

    # 6) Generate auto tags from the summary
    try:
        auto_tags = generate_auto_tags_from_summary(out_path, max_tags=6, cost_tracker=cost_tracker, episode_name=title)
        combined_tags = sorted(set(["YouTube", "video"] + (auto_tags or [])))
    except Exception as e:
        log_with_timestamp(f"WARNING: Auto-tagging failed: {e}")
        combined_tags = ["YouTube", "video"]

    # 7) Save metadata
    meta = {
        "podcast": channel,  # Channel name as "podcast"
        "episode": title,
        "published": upload_date,
        "link": metadata.get("url"),
        "tags": combined_tags,
        "source": "YouTube"
    }
    meta_path = out_path.replace("_summary.txt", "_summary.meta.json")
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2)
    log_with_timestamp(f"Meta saved: {meta_path}")

    # 8) Push to Notion
    try:
        sys.argv = ["push_to_notion.py", out_path]
        push_to_notion_main()
    except Exception as e:
        log_with_timestamp(f"WARNING: Failed to push to Notion: {e}")

    # Log episode cost total
    total_cost = cost_tracker.log_episode_total(f"{channel}: {title}")
    if total_cost:
        log_with_timestamp(f"Video cost: ${total_cost:.3f}")

    # Mark as seen
    seen_ids.add(video_id)
    seen[youtube_key] = list(seen_ids)
    save_seen(seen)
    log_with_timestamp("Marked as processed.")


def read_youtube_links() -> list[str]:
    """Read URLs from config/youtube_links.txt, skip empty lines and comments"""
    if not YOUTUBE_LINKS_FILE.exists():
        return []

    with open(YOUTUBE_LINKS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    urls = []
    for line in lines:
        line = line.strip()
        # Skip empty lines and comments
        if line and not line.startswith("#"):
            urls.append(line)

    return urls


def main():
    log_with_timestamp("=== YouTube video processing pipeline started ===")

    # Initialize cost tracker
    cost_tracker = CostTracker()

    # Read URLs from file
    urls = read_youtube_links()

    if not urls:
        log_with_timestamp(f"No URLs found in {YOUTUBE_LINKS_FILE}")
        log_with_timestamp("Add YouTube URLs (one per line) and run again.")
        return

    log_with_timestamp(f"Found {len(urls)} URL(s) to process")

    # Process each URL
    for url in urls:
        try:
            process_youtube_video(url, cost_tracker)
        except Exception as e:
            log_with_timestamp(f"ERROR: Failed to process {url}: {e}")
            continue

    # Print cost summary at the end
    log_with_timestamp("\n" + cost_tracker.get_summary())
    log_with_timestamp("=== YouTube video processing pipeline completed ===")


if __name__ == "__main__":
    main()
