# automation/pipeline.py

import os
import re
import json
import sys
import pathlib
import time
import anthropic
from datetime import datetime

def log_with_timestamp(message: str):
    """Print message with timestamp for cron logs"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def generate_auto_tags_from_summary(summary_path: str, max_tags: int = 6, cost_tracker=None, episode_name="") -> list[str]:
    """
    Reads the SUMMARY file and asks Claude for concise topical tags.
    Rate-limit friendly: truncates input and retries on 429.
    Uses ANTHROPIC_TAG_MODEL if set (default: claude-haiku-3-20240307).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("No ANTHROPIC_API_KEY set, skipping auto-tagging")
        return []

    tag_model = os.getenv("ANTHROPIC_TAG_MODEL", "claude-3-5-haiku-20241022")
    max_chars = int(os.getenv("TAG_MAX_CHARS", "6000"))

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            full_text = f.read()
        text = full_text[:max_chars]

        client = anthropic.Anthropic(api_key=api_key)

        prompt = (
            "You are a precise tag generator. Read the podcast summary below and return ONLY a JSON array "
            f"of {max(3, min(max_tags, 6))} concise topical tags. Each tag should be 1-3 words, no emojis, no punctuation. "
            "Avoid generic words like podcast or episode. Focus on themes, domains, or concrete topics.\n\n"
            "Summary:\n\n" + text + "\n\nReturn JSON only, like: [\"AI coding tools\", \"developer productivity\", \"Apple Watch\"]"
        )

        attempts = 0
        while attempts < 3:
            try:
                resp = client.messages.create(
                    model=tag_model,
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.content[0].text.strip()

                # Track tagging cost if cost_tracker provided
                if cost_tracker and hasattr(resp, 'usage'):
                    cost_tracker.log_claude_cost(
                        tag_model,
                        resp.usage.input_tokens,
                        resp.usage.output_tokens,
                        "Auto-tagging",
                        episode_name
                    )

                import json as _json
                try:
                    arr = _json.loads(raw)
                    if isinstance(arr, list):
                        return [str(t).strip() for t in arr if str(t).strip()]
                except Exception:
                    return [t.strip() for t in raw.split(",") if t.strip()]
            except Exception as e:
                msg = str(e)
                if "429" in msg or "rate limit" in msg.lower():
                    attempts += 1
                    sleep_s = 10 * attempts
                    print(f"Auto-tagging hit rate limit, retry {attempts}/3 after {sleep_s}s")
                    time.sleep(sleep_s)
                    continue
                print("Auto-tagging failed:", e)
                break
    except Exception as e:
        print("Auto-tagging failed:", e)

    return []

# Make "scripts" importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.fetch_feed import get_latest_episode
from scripts.download_audio import download_mp3
from scripts.transcribe import transcribe_file
from scripts.translate import translate_transcript
from scripts.summarise_with_quotes import summarise_with_sonnet
from scripts.push_to_notion import main as push_to_notion_main
from utils.cost_tracker import CostTracker
from utils.date_utils import to_iso_date

DATA = ROOT / "data"
AUDIO_DIR = DATA / "audio"
TRANS_DIR = DATA / "transcripts"
SUM_DIR = DATA / "summaries"
CFG = ROOT / "config" / "feeds.json"
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


def process_feed(feed: dict, cost_tracker: CostTracker) -> None:
    name = feed["name"]
    rss = feed["rss"]
    tags = feed.get("tags", ["podcast"])

    log_with_timestamp(f"== {name} ==")
    item = get_latest_episode(rss)
    if not item:
        log_with_timestamp("No episodes found")
        return

    episode_id = item.get("id") or item.get("link") or item.get("title")
    if not episode_id:
        log_with_timestamp("Could not determine episode id, skipping")
        return

    # Load seen list
    seen = load_seen()
    seen_ids = set(seen.get(name, []))
    if episode_id in seen_ids:
        log_with_timestamp(f"Skipping. Already processed: {item.get('title', 'Untitled')}")
        return

    mp3_url = item.get("mp3_url")
    if not mp3_url:
        log_with_timestamp("No MP3 url on latest episode, skipping")
        return

    base = f"{slugify(name)}__{slugify(item.get('title', 'Untitled'))}"

    # 1) Download audio
    mp3_path = download_mp3(mp3_url, str(AUDIO_DIR), base)
    log_with_timestamp(f"Audio: {mp3_path}")

    # 2) Transcribe
    txt_path, audio_duration = transcribe_file(mp3_path, str(TRANS_DIR), model_size="small")
    log_with_timestamp(f"Transcript: {txt_path} ({audio_duration:.1f} min)")

    # Track Whisper cost
    cost_tracker.log_whisper_cost(audio_duration, item.get('title', 'Untitled'))

    # 3) Translate if needed
    final_txt_path, translation_usage = translate_transcript(txt_path, str(TRANS_DIR))
    if final_txt_path != txt_path:
        log_with_timestamp(f"Translation: {final_txt_path}")
        if translation_usage:
            cost_tracker.log_claude_cost(
                "claude-3-5-haiku-20241022",
                translation_usage.input_tokens,
                translation_usage.output_tokens,
                "Translation",
                item.get('title', 'Untitled')
            )

    # 4) Summarise with Sonnet
    out_path, summary_usage = summarise_with_sonnet(final_txt_path, str(SUM_DIR))
    log_with_timestamp(f"Summary: {out_path}")
    if summary_usage:
        cost_tracker.log_claude_cost(
            "claude-sonnet-4-20250514",
            summary_usage.input_tokens,
            summary_usage.output_tokens,
            "Summary",
            item.get('title', 'Untitled')
        )

    # 5) Generate auto tags from the summary and merge with static tags
    episode_title = item.get('title', 'Untitled')
    auto_tags = generate_auto_tags_from_summary(out_path, max_tags=6, cost_tracker=cost_tracker, episode_name=episode_title)
    combined_tags = sorted(set((tags or []) + (auto_tags or [])))

    # 6) Save metadata
    published_date = item.get("published")
    if published_date:
        try:
            published_date = to_iso_date(published_date)
        except ValueError:
            log_with_timestamp(f"Warning: Could not parse date '{published_date}', using as-is")

    meta = {
        "podcast": name,
        "episode": item.get("title"),
        "published": published_date,
        "link": item.get("link"),
        "tags": combined_tags
    }
    meta_path = out_path.replace("_summary.txt", "_summary.meta.json")
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2)
    log_with_timestamp(f"Meta saved: {meta_path}")

    # 7) Push to Notion
    sys.argv = ["push_to_notion.py", out_path]  # fake CLI call
    push_to_notion_main()

    # Log episode cost total
    total_cost = cost_tracker.log_episode_total(f"{name}: {episode_title}")
    if total_cost:
        log_with_timestamp(f"Episode cost: ${total_cost:.3f}")

    # Mark as seen
    seen_ids.add(episode_id)
    seen[name] = list(seen_ids)
    save_seen(seen)
    log_with_timestamp("Marked as processed.")
    # Gentle throttle to respect API TPM across multiple feeds
    time.sleep(6)


def main():
    log_with_timestamp("=== Podcast automation pipeline started ===")

    # Initialize cost tracker
    cost_tracker = CostTracker()

    with open(CFG, "r", encoding="utf-8") as f:
        feeds = json.load(f)

    if not isinstance(feeds, list) or not feeds:
        log_with_timestamp("config/feeds.json is empty or invalid")
        return

    for feed in feeds:
        name = feed.get("name")
        rss = feed.get("rss")
        if not name or not rss:
            log_with_timestamp(f"Invalid feed entry, skipping: {feed}")
            continue
        process_feed(feed, cost_tracker)

    # Print cost summary at the end
    log_with_timestamp("\n" + cost_tracker.get_summary())
    log_with_timestamp("=== Podcast automation pipeline completed ===")


if __name__ == "__main__":
    main()