#!/usr/bin/env python3
"""
Quality evaluation for podcast processing pipeline
Analyzes transcript quality, summary completeness, and content metrics
Usage: python3 evals/quality_check.py [--recent N]
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def analyze_transcript(transcript_path: Path) -> dict:
    """Analyze transcript quality metrics"""
    if not transcript_path.exists():
        return {"error": "Transcript not found"}
    
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"error": f"Failed to read transcript: {e}"}
    
    # Basic metrics
    metrics = {
        "char_count": len(content),
        "word_count": len(content.split()),
        "line_count": len(content.splitlines()),
    }
    
    # Check for timestamps (indicates Whisper format)
    timestamp_pattern = r'\[\d+\.\d+ --> \d+\.\d+\]'
    timestamps = re.findall(timestamp_pattern, content)
    metrics["has_timestamps"] = len(timestamps) > 0
    metrics["timestamp_count"] = len(timestamps)
    
    # Estimate duration from timestamps if available
    if timestamps:
        try:
            last_timestamp = timestamps[-1]
            time_match = re.search(r'\[(\d+\.\d+) --> (\d+\.\d+)\]', last_timestamp)
            if time_match:
                end_time = float(time_match.group(2))
                metrics["estimated_duration_sec"] = end_time
                metrics["estimated_duration_min"] = end_time / 60
        except:
            pass
    
    # Language indicators
    metrics["likely_english"] = bool(re.search(r'\b(the|and|is|in|to|of|a|that|it|with|for|as|was|on|are|you)\b', content.lower()))
    
    # Quality indicators
    metrics["avg_words_per_line"] = metrics["word_count"] / max(metrics["line_count"], 1)
    metrics["has_repeated_phrases"] = check_repeated_phrases(content)
    
    return metrics

def analyze_summary(summary_path: Path) -> dict:
    """Analyze summary quality metrics"""
    if not summary_path.exists():
        return {"error": "Summary not found"}
    
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"error": f"Failed to read summary: {e}"}
    
    metrics = {
        "char_count": len(content),
        "word_count": len(content.split()),
        "line_count": len(content.splitlines()),
    }
    
    # Structure analysis
    sections = re.findall(r'^## (.+)$', content, re.MULTILINE)
    subsections = re.findall(r'^### (.+)$', content, re.MULTILINE)
    
    metrics["section_count"] = len(sections)
    metrics["subsection_count"] = len(subsections)
    metrics["sections"] = sections
    
    # Quote analysis
    quote_pattern = r'\*\*"([^"]+)"\*\* — \*\*([^*]+)\*\*'
    quotes = re.findall(quote_pattern, content)
    metrics["quote_count"] = len(quotes)
    metrics["quotes"] = [{"text": q[0][:100] + "..." if len(q[0]) > 100 else q[0], "speaker": q[1]} for q in quotes]
    
    # Key sections check
    expected_sections = ["Episode Overview", "Key Sections", "Top 5 Lessons", "Reflection Questions"]
    metrics["has_required_sections"] = all(section in content for section in expected_sections[:3])  # First 3 are required
    
    # Bullet point analysis
    bullet_points = re.findall(r'^- (.+)$', content, re.MULTILINE)
    metrics["bullet_point_count"] = len(bullet_points)
    
    return metrics

def check_repeated_phrases(text: str, min_length: int = 10, threshold: int = 3) -> bool:
    """Check for repeated phrases that might indicate transcription issues"""
    words = text.lower().split()
    phrases = {}
    
    for i in range(len(words) - min_length + 1):
        phrase = " ".join(words[i:i+min_length])
        phrases[phrase] = phrases.get(phrase, 0) + 1
    
    return any(count >= threshold for count in phrases.values())

def analyze_metadata(meta_path: Path) -> dict:
    """Analyze metadata completeness"""
    if not meta_path.exists():
        return {"error": "Metadata not found"}
    
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read metadata: {e}"}
    
    required_fields = ["podcast", "episode", "published", "link", "tags"]
    metrics = {
        "has_all_required": all(field in meta for field in required_fields),
        "missing_fields": [field for field in required_fields if field not in meta],
        "tag_count": len(meta.get("tags", [])),
        "tags": meta.get("tags", [])
    }
    
    return metrics

def main():
    # Parse arguments
    recent_count = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--recent" and len(sys.argv) > 2:
            recent_count = int(sys.argv[2])
    
    project_root = Path(__file__).parents[1]
    summaries_dir = project_root / "data" / "summaries"
    transcripts_dir = project_root / "data" / "transcripts"
    
    if not summaries_dir.exists():
        print("❌ No summaries directory found")
        return
    
    print("📊 Podcast Quality Analysis")
    print("=" * 50)
    
    # Find all summary files
    summary_files = list(summaries_dir.glob("*_summary.txt"))
    
    if not summary_files:
        print("No summary files found")
        return
    
    # Sort by modification time (newest first)
    summary_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Limit to recent files if specified
    if recent_count:
        summary_files = summary_files[:recent_count]
        print(f"Analyzing {recent_count} most recent episodes")
    else:
        print(f"Analyzing {len(summary_files)} episodes")
    
    print()
    
    # Aggregate stats
    stats = {
        "total_episodes": 0,
        "successful_summaries": 0,
        "total_quotes": 0,
        "avg_summary_length": 0,
        "missing_transcripts": 0,
        "missing_metadata": 0,
        "issues": []
    }
    
    for summary_file in summary_files:
        stats["total_episodes"] += 1
        
        # Get corresponding files
        base_name = summary_file.name.replace("_summary.txt", "")
        transcript_file = transcripts_dir / f"{base_name}.txt"
        meta_file = summary_file.parent / f"{base_name}_summary.meta.json"
        
        # Handle translated files
        if not transcript_file.exists():
            transcript_file = transcripts_dir / f"{base_name}_translated.txt"
        
        print(f"📝 {base_name}")
        print("-" * 30)
        
        # Analyze summary
        summary_metrics = analyze_summary(summary_file)
        if "error" not in summary_metrics:
            stats["successful_summaries"] += 1
            stats["total_quotes"] += summary_metrics["quote_count"]
            stats["avg_summary_length"] += summary_metrics["word_count"]
            
            print(f"  Summary: {summary_metrics['word_count']} words, {summary_metrics['section_count']} sections, {summary_metrics['quote_count']} quotes")
            
            if not summary_metrics["has_required_sections"]:
                stats["issues"].append(f"{base_name}: Missing required sections")
                print(f"  ⚠️  Missing required sections")
            
            if summary_metrics["quote_count"] == 0:
                stats["issues"].append(f"{base_name}: No quotes found")
                print(f"  ⚠️  No quotes found")
        else:
            print(f"  ❌ Summary error: {summary_metrics['error']}")
            stats["issues"].append(f"{base_name}: {summary_metrics['error']}")
        
        # Analyze transcript
        if transcript_file.exists():
            transcript_metrics = analyze_transcript(transcript_file)
            if "error" not in transcript_metrics:
                print(f"  Transcript: {transcript_metrics['word_count']} words")
                if transcript_metrics.get("estimated_duration_min"):
                    print(f"  Duration: ~{transcript_metrics['estimated_duration_min']:.1f} min")
                
                if transcript_metrics["has_repeated_phrases"]:
                    stats["issues"].append(f"{base_name}: Repeated phrases detected")
                    print(f"  ⚠️  Repeated phrases detected")
            else:
                print(f"  ❌ Transcript error: {transcript_metrics['error']}")
        else:
            stats["missing_transcripts"] += 1
            print(f"  ⚠️  Transcript not found")
        
        # Analyze metadata
        if meta_file.exists():
            meta_metrics = analyze_metadata(meta_file)
            if "error" not in meta_metrics:
                print(f"  Metadata: {meta_metrics['tag_count']} tags")
                if not meta_metrics["has_all_required"]:
                    stats["issues"].append(f"{base_name}: Missing metadata fields: {', '.join(meta_metrics['missing_fields'])}")
                    print(f"  ⚠️  Missing fields: {', '.join(meta_metrics['missing_fields'])}")
            else:
                print(f"  ❌ Metadata error: {meta_metrics['error']}")
        else:
            stats["missing_metadata"] += 1
            print(f"  ⚠️  Metadata not found")
        
        print()
    
    # Summary statistics
    print("=" * 50)
    print("📈 Summary Statistics")
    print("-" * 20)
    print(f"Total episodes analyzed: {stats['total_episodes']}")
    print(f"Successful summaries: {stats['successful_summaries']}")
    
    if stats["successful_summaries"] > 0:
        avg_length = stats["avg_summary_length"] / stats["successful_summaries"]
        avg_quotes = stats["total_quotes"] / stats["successful_summaries"]
        print(f"Average summary length: {avg_length:.0f} words")
        print(f"Average quotes per episode: {avg_quotes:.1f}")
    
    print(f"Missing transcripts: {stats['missing_transcripts']}")
    print(f"Missing metadata: {stats['missing_metadata']}")
    print(f"Total issues found: {len(stats['issues'])}")
    
    if stats["issues"]:
        print("\n🚨 Issues Found:")
        for issue in stats["issues"]:
            print(f"  - {issue}")
    else:
        print("\n✅ No major issues found!")

if __name__ == "__main__":
    main()