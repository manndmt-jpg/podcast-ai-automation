#!/usr/bin/env python3
"""
Translation script using Claude API
Detects language and translates non-English transcripts to English
"""

import os
import anthropic
from pathlib import Path
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set seed for consistent language detection
DetectorFactory.seed = 0

# Language code mapping for better user feedback
LANGUAGE_NAMES = {
    'en': 'English',
    'de': 'German',
    'fr': 'French',
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'ar': 'Arabic',
    'hi': 'Hindi'
}

def detect_language(text):
    """
    Detect the language of the given text
    Returns language code or 'unknown' if detection fails
    """
    try:
        # Take a sample from middle of text for better detection
        sample_size = min(1000, len(text))
        start_pos = max(0, (len(text) - sample_size) // 2)
        sample_text = text[start_pos:start_pos + sample_size]

        detected_lang = detect(sample_text)
        return detected_lang
    except LangDetectException:
        return 'unknown'

def translate_with_claude(text, source_lang, target_lang='en'):
    """
    Translate text using Claude API
    """
    client = anthropic.Client()

    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_lang, target_lang)

    prompt = f"""Please translate the following {source_name} text to {target_name}.

Key requirements:
- Maintain the original meaning and context
- Keep the conversational tone and style
- Preserve proper nouns, company names, and technical terms
- Do not add explanations or commentary
- Return only the translated text

Text to translate:

{text}"""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Using cheaper model for translation
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"Translation failed: {e}")
        return None

def translate_transcript(transcript_path, output_dir=None):
    """
    Main function to translate a transcript if needed
    Returns path to the transcript to use for summarization (original or translated)
    """
    transcript_path = Path(transcript_path)

    # Read the transcript
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading transcript {transcript_path}: {e}")
        return str(transcript_path)

    # Detect language
    detected_lang = detect_language(text)
    lang_name = LANGUAGE_NAMES.get(detected_lang, detected_lang)

    print(f"Detected language: {lang_name} ({detected_lang})")

    # If already English or detection failed, return original
    if detected_lang == 'en' or detected_lang == 'unknown':
        if detected_lang == 'unknown':
            print("⚠️  Could not detect language, assuming English")
        return str(transcript_path)

    # Set output directory
    if output_dir is None:
        output_dir = transcript_path.parent
    else:
        output_dir = Path(output_dir)

    # Create translated filename
    translated_filename = transcript_path.stem + "_translated.txt"
    translated_path = output_dir / translated_filename

    # Check if translation already exists
    if translated_path.exists():
        print(f"✅ Translation already exists: {translated_path}")
        return str(translated_path)

    # Translate the text
    print(f"🔄 Translating from {lang_name} to English...")
    translated_text = translate_with_claude(text, detected_lang, 'en')

    if translated_text is None:
        print("❌ Translation failed, using original transcript")
        return str(transcript_path)

    # Save translated text
    try:
        with open(translated_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        print(f"✅ Translation saved: {translated_path}")
        return str(translated_path)
    except Exception as e:
        print(f"Error saving translation: {e}")
        return str(transcript_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python translate.py <transcript_path> [output_dir]")
        sys.exit(1)

    transcript_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    result_path = translate_transcript(transcript_path, output_dir)
    print(f"Final transcript path: {result_path}")