#!/usr/bin/env python3
"""
Quote extraction script using Claude API
Extracts memorable quotes from podcast transcripts
"""

import os
import json
import anthropic
from pathlib import Path

def extract_quotes(transcript_path):
    """
    Extract 3-5 memorable quotes from a transcript
    Returns list of quote objects
    """
    # Read the transcript
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
    except Exception as e:
        print(f"Error reading transcript {transcript_path}: {e}")
        return []

    # Skip if transcript is too short
    if len(transcript_text) < 500:
        print("Transcript too short for quote extraction")
        return []

    client = anthropic.Client()

    prompt = f"""Extract 3-5 memorable quotes from this podcast transcript.

Look for:
- Profound insights or actionable advice
- Surprising or thought-provoking statements
- Key conclusions worth remembering

Format each quote like this:
QUOTE: "exact quote text"
SPEAKER: speaker name or Host/Guest
CONTEXT: brief context

Example:
QUOTE: "The biggest mistake founders make is building features nobody wants"
SPEAKER: Guest
CONTEXT: Discussing product-market fit

Transcript:

{transcript_text[:8000]}"""  # Limit to first 8000 chars for cost efficiency

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Using cheaper model for quotes
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Parse the structured text format
        quotes = []
        lines = response_text.split('\n')
        current_quote = {}

        for line in lines:
            line = line.strip()
            if line.startswith('QUOTE: '):
                current_quote['quote'] = line[7:].strip().strip('"')
            elif line.startswith('SPEAKER: '):
                current_quote['speaker'] = line[9:].strip()
            elif line.startswith('CONTEXT: '):
                current_quote['context'] = line[9:].strip()
                # End of a quote block - save it
                if 'quote' in current_quote and current_quote['quote']:
                    quotes.append(current_quote.copy())
                current_quote = {}

        return quotes

    except Exception as e:
        print(f"Quote extraction failed: {e}")
        return []

    return []

def save_quotes(quotes, output_path):
    """Save quotes to a JSON file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving quotes: {e}")
        return False

def format_quotes_for_summary(quotes):
    """Format quotes for inclusion in summary"""
    if not quotes:
        return ""

    formatted = "\n## 💬 Key Quotes\n\n"

    for i, quote in enumerate(quotes[:3]):  # Include top 3 quotes in summary
        quote_text = quote.get('quote', '').strip()
        speaker = quote.get('speaker', 'Unknown').strip()
        context = quote.get('context', '').strip()

        if quote_text:
            formatted += f'**{i+1}.** *"{quote_text}"*\n'
            formatted += f'— **{speaker}**\n'
            if context:
                formatted += f'_{context}_\n'
            formatted += '\n'

    return formatted

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extract_quotes.py <transcript_path> [output_dir]")
        sys.exit(1)

    transcript_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    if output_dir is None:
        output_dir = Path(transcript_path).parent

    # Extract quotes
    print(f"Extracting quotes from: {transcript_path}")
    quotes = extract_quotes(transcript_path)

    if quotes:
        # Save quotes file
        transcript_name = Path(transcript_path).stem
        quotes_path = Path(output_dir) / f"{transcript_name}_quotes.json"

        if save_quotes(quotes, quotes_path):
            print(f"✅ Saved {len(quotes)} quotes to: {quotes_path}")

            # Print formatted quotes for summary
            print("\nFormatted for summary:")
            print(format_quotes_for_summary(quotes))
        else:
            print("❌ Failed to save quotes")
    else:
        print("❌ No quotes extracted")