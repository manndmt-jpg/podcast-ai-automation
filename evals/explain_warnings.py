#!/usr/bin/env python3
"""
Warning Explanation Helper
Explains what different evaluation warnings mean and how to fix them
Usage: python3 evals/explain_warnings.py [warning_type]
"""

import sys

WARNING_EXPLANATIONS = {
    "date_parsing": {
        "title": "📅 Date Parsing Warning",
        "description": "Could not parse publication date format",
        "meaning": "The RSS feed uses a date format we don't recognize",
        "impact": "⚠️ Low - Can't check if episodes are old, but doesn't affect processing",
        "solutions": [
            "Usually harmless - different feeds use different date formats",
            "Episodes will still be processed normally",
            "If you see this consistently, the date parsing code may need updating"
        ],
        "example": "Could not parse publication date: 2025-09-22T10:00:00+00:00"
    },
    
    "old_episodes": {
        "title": "⏰ Old Episodes Warning", 
        "description": "Latest episode is X days old",
        "meaning": "The podcast hasn't published new content recently",
        "impact": "⚠️ Low-Medium - Podcast may be inactive or on hiatus",
        "solutions": [
            "Check if podcast is still active",
            "30+ days: Normal for some podcasts with irregular schedules",
            "90+ days: May want to remove from feeds if permanently inactive",
            "Consider checking the podcast website for updates"
        ],
        "example": "Latest episode is 45 days old"
    },
    
    "missing_mp3": {
        "title": "🎵 Missing MP3 Warning",
        "description": "Latest episode missing MP3 URL", 
        "meaning": "The episode entry doesn't have a valid audio file link",
        "impact": "❌ High - Episode cannot be processed",
        "solutions": [
            "Check if RSS feed is properly configured",
            "Some feeds may have corrupted entries",
            "Try manually visiting the podcast website",
            "Contact podcast publisher if issue persists"
        ],
        "example": "Latest episode missing MP3 URL"
    },
    
    "missing_title": {
        "title": "📝 Missing Title Warning",
        "description": "Latest episode missing title",
        "meaning": "The episode has no title in the RSS feed",
        "impact": "⚠️ Medium - Episode may be processed with generic name",
        "solutions": [
            "Usually indicates RSS feed issue",
            "Episode will still be processed if it has MP3 URL",
            "Check feed manually in a browser",
            "May be temporary feed generation issue"
        ],
        "example": "Latest episode missing title"
    },
    
    "feed_errors": {
        "title": "🌐 Feed Connection Error",
        "description": "Cannot connect to RSS feed",
        "meaning": "The feed URL is unreachable or returns an error",
        "impact": "❌ High - Cannot process new episodes from this feed",
        "solutions": [
            "Check your internet connection",
            "Verify the RSS URL is still valid",
            "Feed server may be temporarily down",
            "RSS URL may have changed - check podcast website",
            "Try accessing the URL in your browser"
        ],
        "example": "HTTP 404: Not Found"
    },
    
    "quality_issues": {
        "title": "📊 Quality Issues",
        "description": "Problems found in processed content",
        "meaning": "Generated summaries or transcripts have structural issues",
        "impact": "⚠️ Medium - Content quality may be degraded",
        "solutions": [
            "Missing sections: Check if summary generation is working properly",
            "No quotes: Verify quote extraction from transcripts",
            "Short summaries: May indicate transcript issues",
            "Review specific episodes mentioned in quality report"
        ],
        "example": "Missing required sections, No quotes found"
    },
    
    "duplicates": {
        "title": "🔄 Duplicate Episodes",
        "description": "Same episode appears multiple times",
        "meaning": "Episode tracking may have issues or feeds overlap",
        "impact": "⚠️ Low - May waste processing resources",
        "solutions": [
            "Run duplicate cleanup: python3 evals/duplicate_analysis.py --cleanup",
            "Check if multiple feeds contain the same content",
            "Review episode ID generation logic",
            "Usually safe to ignore unless numbers are very high"
        ],
        "example": "Found 3 potential duplicate issues"
    },
    
    "performance": {
        "title": "⚡ Performance Issues", 
        "description": "Processing success rate is low",
        "meaning": "Pipeline is failing frequently",
        "impact": "❌ High - Episodes are not being processed",
        "solutions": [
            "Check logs/cron.log for specific errors",
            "Verify API keys are still valid", 
            "Check disk space and system resources",
            "Review recent changes to pipeline configuration",
            "Run manual test: python3 automation/pipeline.py"
        ],
        "example": "Success rate: 45.2%"
    }
}

def show_all_warnings():
    """Show all possible warning types"""
    print("🚨 Evaluation Warning Types")
    print("=" * 50)
    print("\nCommon warnings and their meanings:")
    print()
    
    for key, warning in WARNING_EXPLANATIONS.items():
        print(f"{warning['title']}")
        print(f"  Impact: {warning['impact']}")
        print(f"  Meaning: {warning['meaning']}")
        print()

def explain_warning(warning_type: str):
    """Explain a specific warning type"""
    if warning_type not in WARNING_EXPLANATIONS:
        print(f"❌ Unknown warning type: {warning_type}")
        print("Available types:", ", ".join(WARNING_EXPLANATIONS.keys()))
        return
    
    warning = WARNING_EXPLANATIONS[warning_type]
    
    print(warning['title'])
    print("=" * 50)
    print(f"📋 Description: {warning['description']}")
    print(f"💭 Meaning: {warning['meaning']}")
    print(f"⚡ Impact: {warning['impact']}")
    
    if 'example' in warning:
        print(f"📝 Example: {warning['example']}")
    
    print("\n🛠️ Solutions:")
    for i, solution in enumerate(warning['solutions'], 1):
        print(f"  {i}. {solution}")
    
    print()

def detect_warning_type(warning_text: str) -> str:
    """Try to detect warning type from text"""
    warning_lower = warning_text.lower()
    
    if 'parse' in warning_lower and 'date' in warning_lower:
        return 'date_parsing'
    elif 'days old' in warning_lower:
        return 'old_episodes' 
    elif 'mp3' in warning_lower and 'missing' in warning_lower:
        return 'missing_mp3'
    elif 'title' in warning_lower and 'missing' in warning_lower:
        return 'missing_title'
    elif 'http' in warning_lower or 'connection' in warning_lower:
        return 'feed_errors'
    elif 'duplicate' in warning_lower:
        return 'duplicates'
    elif 'success rate' in warning_lower or 'performance' in warning_lower:
        return 'performance'
    elif 'quality' in warning_lower or 'section' in warning_lower or 'quote' in warning_lower:
        return 'quality_issues'
    else:
        return 'unknown'

def main():
    if len(sys.argv) < 2:
        show_all_warnings()
        print("📖 Usage:")
        print("  python3 evals/explain_warnings.py [warning_type]")
        print("  python3 evals/explain_warnings.py date_parsing")
        print("  python3 evals/explain_warnings.py \"Could not parse date...\"")
        return
    
    arg = sys.argv[1]
    
    # Check if it's a warning type or warning text
    if arg in WARNING_EXPLANATIONS:
        explain_warning(arg)
    else:
        # Try to detect from warning text
        detected_type = detect_warning_type(arg)
        if detected_type != 'unknown':
            print(f"🔍 Detected warning type: {detected_type}")
            print()
            explain_warning(detected_type)
        else:
            print(f"❓ Could not identify warning type from: {arg}")
            print("Try one of these specific types:")
            for warning_type in WARNING_EXPLANATIONS.keys():
                print(f"  - {warning_type}")

if __name__ == "__main__":
    main()