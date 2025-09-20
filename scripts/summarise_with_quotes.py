import os
import sys
import anthropic
from pathlib import Path

# Import our quote extraction
sys.path.append(str(Path(__file__).parent))
from extract_quotes import extract_quotes, format_quotes_for_summary

MODEL = "claude-sonnet-4-20250514"  # Sonnet by default

def build_prompt(transcript: str) -> str:
    return (
        "You are an expert educator and editor. Produce an EDUCATIONAL summary that is easy to follow end-to-end.\n"
        "CRITICAL: add connective tissue so sections flow logically.\n\n"
        "Output format:\n"
        "## Episode Overview\n"
        "A tight 2–3 sentence paragraph that frames the episode and sets the throughline (what we are learning + why).\n\n"
        "## Key Sections\n"
        "For EACH major section:\n"
        "1) Start with a 2–4 sentence BRIDGE PARAGRAPH that explains how this section connects to the previous one.\n"
        "2) Then bullets with the concrete details (steps, tools, numbers, examples). Keep bullets crisp.\n"
        "3) End the section with one sentence: **Why this matters:** <practical takeaway>.\n"
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

    # Step 1: Extract quotes
    print("🔍 Extracting quotes...")
    quotes = extract_quotes(transcript_path)

    # Step 2: Generate summary
    client = anthropic.Anthropic(api_key=api_key)
    print(f"Using model: {MODEL}")
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": build_prompt(transcript)}],
    )

    summary = resp.content[0].text

    # Step 3: Insert quotes after Episode Overview
    if quotes:
        print(f"✅ Found {len(quotes)} quotes")
        quotes_section = format_quotes_for_summary(quotes)

        # Insert quotes after Episode Overview
        lines = summary.split('\n')
        insert_index = -1

        # Find where to insert quotes (after Episode Overview, before Key Sections)
        for i, line in enumerate(lines):
            if line.strip().startswith('## Key Sections'):
                insert_index = i
                break

        if insert_index > 0:
            # Insert quotes section
            lines.insert(insert_index, quotes_section)
            summary = '\n'.join(lines)
        else:
            # Fallback: add quotes at the end
            summary += '\n' + quotes_section
    else:
        print("ℹ️  No quotes extracted")

    # Step 4: Save enhanced summary
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(transcript_path))[0]
    out_path = os.path.join(out_dir, base + "_summary.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary)

    # Step 5: Save quotes separately if found
    if quotes:
        quotes_path = os.path.join(out_dir, base + "_quotes.json")
        import json
        with open(quotes_path, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)
        print(f"📝 Quotes saved to: {quotes_path}")

    return out_path

# Keep original function for backward compatibility
def summarise_with_sonnet(transcript_path: str, out_dir: str) -> str:
    return summarise_with_sonnet_and_quotes(transcript_path, out_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/summarise_with_quotes.py <TRANSCRIPT_PATH> <OUT_DIR>")
        sys.exit(1)

    transcript_path = sys.argv[1]
    out_dir = sys.argv[2]
    out_file = summarise_with_sonnet_and_quotes(transcript_path, out_dir)
    print(f"✅ Enhanced summary with quotes saved to {out_file}")