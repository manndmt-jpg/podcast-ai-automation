import os
import sys
import anthropic
from pathlib import Path

# Import our extraction modules
sys.path.append(str(Path(__file__).parent))
from extract_chapters import extract_chapters, format_chapters_for_summary, get_episode_duration

MODEL = "claude-sonnet-4-20250514"  # Sonnet by default

def build_prompt(transcript: str) -> str:
    return (
        "You are an expert educator and editor. Produce an EDUCATIONAL summary that is easy to follow end-to-end.\n"
        "CRITICAL: add connective tissue so sections flow logically.\n\n"
        "Output format:\n"
        "## Episode Overview\n"
        "A comprehensive 1-minute summary (200-300 words) that covers:\n"
        "- The main topic and key participants\n"
        "- 3-4 core insights or lessons from the episode\n"
        "- The most important practical takeaways\n"
        "- Why this matters to the listener\n"
        "Write it as flowing paragraphs that someone could read in 60 seconds to get the essential value.\n\n"
        "## Key Sections\n"
        "For EACH major section:\n"
        "1) Start with a 2–4 sentence BRIDGE PARAGRAPH that explains how this section connects to the previous one.\n"
        "2) Then bullets with the concrete details (steps, tools, numbers, examples). Keep bullets crisp.\n"
        "3) Include 1-2 RELEVANT QUOTES from the transcript that capture key insights for this section. Format as:\n"
        "   **\"Exact quote from transcript\"** — **Speaker Name**\n"
        "4) End the section with one sentence: **Why this matters:** <practical takeaway>.\n"
        "Use ### headings for section titles. Bold important names, tools, and numbers.\n\n"
        "## Top 5 Lessons Recap\n"
        "Exactly 5 bullets. Each bullet should be a single actionable lesson in plain English.\n\n"
        "## Reflection Questions (Optional)\n"
        "2–3 short questions to reinforce learning.\n\n"
        "Stylistic rules:\n"
        "- Prefer short paragraphs. Avoid wall-of-text.\n"
        "- Use transitions like: 'Building on that...', 'This sets up...', 'As a result...', 'The key shift here is...'.\n"
        "- Do NOT repeat the same info across sections; refer back with phrases like 'As noted above'.\n"
        "- Keep a clear narrative throughline from start to finish.\n\n"
        "Transcript follows:\n\n" + transcript
    )

def summarise_with_sonnet_and_quotes(transcript_path: str, out_dir: str) -> str:
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Run:\n"
            "   export ANTHROPIC_API_KEY='your_api_key_here'"
        )

    # Step 1: Check episode duration and extract chapters if needed
    # For translated transcripts, check original for duration
    original_path = transcript_path
    if transcript_path.endswith('_translated.txt'):
        original_path = transcript_path.replace('_translated.txt', '.txt')

    duration = get_episode_duration(original_path)
    chapters = None
    if duration and duration >= 45:
        print("📑 Extracting chapters...")
        chapters = extract_chapters(transcript_path)

    # Step 2: Generate summary with integrated quotes
    client = anthropic.Anthropic(api_key=api_key)
    print(f"Using model: {MODEL}")
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": build_prompt(transcript)}],
    )

    summary = resp.content[0].text
    usage = resp.usage  # Store usage for cost tracking

    # Step 3: Insert chapters after Episode Overview (if available)
    if chapters and duration:
        print(f"✅ Found {len(chapters)} chapters")
        lines = summary.split('\n')
        insert_index = -1

        # Find where to insert chapters (after Episode Overview, before Key Sections)
        for i, line in enumerate(lines):
            if line.strip().startswith('## Key Sections'):
                insert_index = i
                break

        if insert_index > 0:
            chapters_section = format_chapters_for_summary(chapters, duration)
            lines.insert(insert_index, chapters_section)
            summary = '\n'.join(lines)
        else:
            # Fallback: add chapters at the end
            chapters_section = format_chapters_for_summary(chapters, duration)
            summary += '\n' + chapters_section

    # Step 4: Save enhanced summary
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(transcript_path))[0]
    out_path = os.path.join(out_dir, base + "_summary.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary)

    # Step 5: Save chapters separately if found
    import json

    if chapters:
        chapters_path = os.path.join(out_dir, base + "_chapters.json")
        with open(chapters_path, "w", encoding="utf-8") as f:
            json.dump({
                'duration_minutes': duration,
                'chapters': chapters
            }, f, indent=2, ensure_ascii=False)
        print(f"📑 Chapters saved to: {chapters_path}")

    return out_path, usage

# Keep original function for backward compatibility - returns tuple now
def summarise_with_sonnet(transcript_path: str, out_dir: str):
    return summarise_with_sonnet_and_quotes(transcript_path, out_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/summarise_with_quotes.py <TRANSCRIPT_PATH> <OUT_DIR>")
        sys.exit(1)

    transcript_path = sys.argv[1]
    out_dir = sys.argv[2]
    out_file = summarise_with_sonnet_and_quotes(transcript_path, out_dir)
    print(f"✅ Enhanced summary with quotes saved to {out_file}")