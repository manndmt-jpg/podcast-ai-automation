#!/usr/bin/env python3
"""
Chapter extraction script for long podcast episodes
Identifies major topic transitions and creates timestamped chapters
"""

import os
import re
import anthropic
from pathlib import Path

def seconds_to_mmss(seconds):
    """Convert seconds to MM:SS format"""
    try:
        total_seconds = float(seconds)
        minutes = int(total_seconds // 60)
        secs = int(total_seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return seconds  # Return original if conversion fails

def fix_timestamp_format(timestamp, episode_duration_minutes=None):
    """Fix and validate timestamp format, converting to proper MM:SS"""
    try:
        timestamp = timestamp.strip()

        # Handle pure seconds (like "477" -> "7:57")
        if ':' not in timestamp:
            return seconds_to_mmss(float(timestamp))

        # Handle invalid MM:SS format (like "77:92" -> "78:32")
        if timestamp.count(':') == 1:
            parts = timestamp.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])

                # Check if this timestamp is likely in seconds format
                should_convert_to_seconds = False

                # Case 1: Invalid seconds (>= 60)
                if seconds >= 60:
                    should_convert_to_seconds = True

                # Case 2: Minutes exceed episode duration (likely seconds format)
                elif episode_duration_minutes and minutes > episode_duration_minutes:
                    should_convert_to_seconds = True

                # Case 3: Very high minutes with :00 seconds (likely seconds format)
                elif minutes > 60 and seconds == 0:
                    should_convert_to_seconds = True

                if should_convert_to_seconds:
                    # For timestamps that exceed episode duration, treat first part as seconds
                    # e.g., "151:50" in 96-min episode -> treat 151 as seconds -> "02:31"
                    return seconds_to_mmss(minutes)
                else:
                    # Fix invalid seconds only
                    if seconds >= 60:
                        extra_minutes = seconds // 60
                        seconds = seconds % 60
                        minutes += extra_minutes

                    return f"{minutes:02d}:{seconds:02d}"

        # Handle HH:MM:SS format - convert to MM:SS
        if timestamp.count(':') == 2:
            parts = timestamp.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1]) + (hours * 60)
                seconds = int(parts[2])

                # Fix invalid seconds
                if seconds >= 60:
                    extra_minutes = seconds // 60
                    seconds = seconds % 60
                    minutes += extra_minutes

                return f"{minutes:02d}:{seconds:02d}"

        return timestamp  # Return original if no conversion needed
    except (ValueError, IndexError):
        return timestamp  # Return original if parsing fails

def get_episode_duration(transcript_path):
    """
    Extract episode duration from transcript timestamps
    Returns duration in minutes or None if not found
    """
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip translation header if present
        if content.startswith("Here's the English translation:"):
            content = content.split('\n', 1)[1] if '\n' in content else content

        # Find all timestamps in format [MM:SS.SS --> MM:SS.SS] or [HH:MM:SS.SS --> HH:MM:SS.SS]
        timestamps = re.findall(r'\[([0-9:\.]+) --> ([0-9:\.]+)\]', content)

        if not timestamps:
            return None

        # Get the last timestamp (end of episode)
        last_timestamp = timestamps[-1][1]  # End time of last segment

        # Parse timestamp to minutes
        parts = last_timestamp.split(':')
        if len(parts) == 1:  # SS.SS format (seconds only)
            total_seconds = float(parts[0])
            total_minutes = total_seconds / 60
        elif len(parts) == 2:  # MM:SS.SS format
            minutes = int(parts[0])
            seconds = float(parts[1])
            total_minutes = minutes + (seconds / 60)
        elif len(parts) == 3:  # HH:MM:SS.SS format
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            total_minutes = (hours * 60) + minutes + (seconds / 60)
        else:
            return None
        return total_minutes

    except Exception as e:
        print(f"Error getting episode duration: {e}")
        return None

def create_simple_chapters(duration_minutes, num_chapters=6):
    """Create simple chapter structure without timestamps"""
    # Just return the number of chapters to create
    return num_chapters

def extract_chapters(transcript_path, min_duration_minutes=45):
    """
    Extract chapter information from transcript if episode is long enough
    Returns list of chapter objects or None if too short
    """
    # For translated transcripts, check original for duration
    original_path = transcript_path
    if transcript_path.endswith('_translated.txt'):
        original_path = transcript_path.replace('_translated.txt', '.txt')

    # Check episode duration first (using original transcript)
    duration = get_episode_duration(original_path)
    if duration is None:
        print("Could not determine episode duration - skipping chapter extraction")
        return None
    if duration < min_duration_minutes:
        print(f"Episode duration: {duration:.1f}min - too short for chapters (minimum: {min_duration_minutes}min)")
        return None

    print(f"Episode duration: {duration:.1f}min - extracting chapters...")

    # Read transcript (use the provided path for content)
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()

        # Skip translation header if present
        if transcript_text.startswith("Here's the English translation:"):
            transcript_text = transcript_text.split('\n', 1)[1] if '\n' in transcript_text else transcript_text

    except Exception as e:
        print(f"Error reading transcript: {e}")
        return None

    client = anthropic.Client()

    # Check if this is a translated (potentially truncated) transcript
    is_translated = transcript_path.endswith('_translated.txt')

    # Create a simple prompt for chapter titles only
    prompt = f"""Analyze this podcast transcript and create exactly 6 chapter titles that represent the main topic flow.

Episode duration: {duration:.0f} minutes

Create 6 concise chapter titles (3-8 words each) that capture the major topics and logical flow of the episode.

Format each chapter like this:
CHAPTER: Chapter Title Here

Example:
CHAPTER: Introduction and Context Setting
CHAPTER: Core Problem Definition
CHAPTER: Solution Framework Discussion
CHAPTER: Implementation Strategies
CHAPTER: Case Studies and Examples
CHAPTER: Key Takeaways and Next Steps

Make the titles descriptive and flow logically from one to the next.

Transcript:

{transcript_text[:10000]}"""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Using cheaper model
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Parse chapters
        chapters = []
        lines = response_text.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('CHAPTER: '):
                title = line[9:].strip()  # Remove 'CHAPTER: '
                if title:
                    chapters.append({
                        'title': title.strip()
                    })

        return chapters if chapters else None

    except Exception as e:
        print(f"Chapter extraction failed: {e}")
        return None

def format_chapters_for_summary(chapters, duration_minutes):
    """Format chapters for inclusion in summary"""
    if not chapters:
        return ""

    formatted = f"\n## 📑 Episode Structure *({duration_minutes:.0f} minutes)*\n\n"

    for chapter in chapters:
        formatted += f"- **{chapter['title']}**\n"

    formatted += "\n"
    return formatted

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extract_chapters.py <transcript_path>")
        sys.exit(1)

    transcript_path = sys.argv[1]

    # Get duration first (use original transcript for correct duration)
    original_path = transcript_path
    if transcript_path.endswith('_translated.txt'):
        original_path = transcript_path.replace('_translated.txt', '.txt')

    duration = get_episode_duration(original_path)
    if duration:
        print(f"Episode duration: {duration:.1f} minutes")

    # Extract chapters
    chapters = extract_chapters(transcript_path)

    if chapters:
        print(f"\n✅ Extracted {len(chapters)} chapters:")
        formatted = format_chapters_for_summary(chapters, duration)
        print(formatted)

        # Save chapters to file
        transcript_name = Path(transcript_path).stem
        chapters_path = Path(transcript_path).parent / f"{transcript_name}_chapters.json"

        import json
        with open(chapters_path, 'w', encoding='utf-8') as f:
            json.dump({
                'duration_minutes': duration,
                'chapters': chapters
            }, f, indent=2, ensure_ascii=False)

        print(f"📝 Chapters saved to: {chapters_path}")
    else:
        print("❌ No chapters extracted (episode too short or extraction failed)")