#!/usr/bin/env python3
"""
Duplicate Detection Analysis
Analyzes seen.json file for potential duplicate processing issues
Usage: python3 evals/duplicate_analysis.py [--cleanup]
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import difflib

def analyze_seen_file(seen_file: Path) -> dict:
    """Analyze the seen.json file for potential issues"""
    if not seen_file.exists():
        return {"error": "seen.json not found"}
    
    try:
        with open(seen_file, 'r', encoding='utf-8') as f:
            seen_data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read seen.json: {e}"}
    
    analysis = {
        "total_feeds": len(seen_data),
        "total_episodes": sum(len(episodes) for episodes in seen_data.values()),
        "feeds": {},
        "potential_duplicates": [],
        "suspicious_patterns": [],
        "recommendations": []
    }
    
    # Analyze each feed
    for feed_name, episodes in seen_data.items():
        feed_analysis = analyze_feed_episodes(feed_name, episodes)
        analysis["feeds"][feed_name] = feed_analysis
        
        # Collect potential duplicates
        if feed_analysis["duplicates"]:
            analysis["potential_duplicates"].extend([
                {"feed": feed_name, "episodes": dup} for dup in feed_analysis["duplicates"]
            ])
        
        # Collect suspicious patterns
        if feed_analysis["suspicious"]:
            analysis["suspicious_patterns"].extend([
                {"feed": feed_name, "pattern": pattern} for pattern in feed_analysis["suspicious"]
            ])
    
    # Cross-feed duplicate detection
    cross_feed_duplicates = find_cross_feed_duplicates(seen_data)
    if cross_feed_duplicates:
        analysis["cross_feed_duplicates"] = cross_feed_duplicates
        analysis["suspicious_patterns"].append({
            "feed": "Multiple feeds", 
            "pattern": f"{len(cross_feed_duplicates)} episodes appear in multiple feeds"
        })
    
    # Generate recommendations
    if analysis["potential_duplicates"]:
        analysis["recommendations"].append("Review potential duplicates for cleanup")
    
    if analysis["suspicious_patterns"]:
        analysis["recommendations"].append("Investigate suspicious patterns in episode IDs")
    
    if any(feed["episodes_count"] == 0 for feed in analysis["feeds"].values()):
        analysis["recommendations"].append("Some feeds have no processed episodes - check feed configuration")
    
    return analysis

def analyze_feed_episodes(feed_name: str, episodes: list) -> dict:
    """Analyze episodes for a single feed"""
    analysis = {
        "episodes_count": len(episodes),
        "unique_episodes": len(set(episodes)),
        "duplicates": [],
        "suspicious": [],
        "patterns": {}
    }
    
    # Find exact duplicates
    episode_counts = Counter(episodes)
    duplicates = {ep: count for ep, count in episode_counts.items() if count > 1}
    
    if duplicates:
        analysis["duplicates"] = list(duplicates.items())
    
    # Find similar episode IDs that might be duplicates with slight variations
    similar_pairs = find_similar_episodes(episodes)
    if similar_pairs:
        analysis["suspicious"] = similar_pairs
    
    # Analyze patterns in episode IDs
    patterns = analyze_episode_patterns(episodes)
    analysis["patterns"] = patterns
    
    # Check for suspicious patterns
    if patterns.get("very_short_ids", 0) > len(episodes) * 0.1:  # More than 10% very short IDs
        analysis["suspicious"].append("High ratio of very short episode IDs (potential conflicts)")
    
    if patterns.get("numeric_only", 0) == len(episodes) and len(episodes) > 5:
        analysis["suspicious"].append("All episode IDs are numeric (high collision risk)")
    
    return analysis

def find_similar_episodes(episodes: list) -> list:
    """Find episodes with similar IDs that might be duplicates"""
    similar_pairs = []
    unique_episodes = list(set(episodes))
    
    for i, ep1 in enumerate(unique_episodes):
        for ep2 in unique_episodes[i+1:]:
            # Skip if episodes are identical
            if ep1 == ep2:
                continue
            
            # Calculate similarity ratio
            similarity = difflib.SequenceMatcher(None, str(ep1), str(ep2)).ratio()
            
            # Flag as suspicious if very similar (but not identical)
            if similarity > 0.85:
                similar_pairs.append({
                    "episode1": ep1,
                    "episode2": ep2, 
                    "similarity": similarity
                })
    
    return similar_pairs

def analyze_episode_patterns(episodes: list) -> dict:
    """Analyze patterns in episode IDs"""
    patterns = {
        "numeric_only": 0,
        "contains_url": 0,
        "contains_title": 0,
        "very_short_ids": 0,  # Less than 10 chars
        "very_long_ids": 0,   # More than 200 chars
        "common_prefixes": [],
        "id_lengths": []
    }
    
    for episode in episodes:
        ep_str = str(episode)
        length = len(ep_str)
        patterns["id_lengths"].append(length)
        
        # Check patterns
        if ep_str.isdigit():
            patterns["numeric_only"] += 1
        
        if "http" in ep_str.lower():
            patterns["contains_url"] += 1
        
        if any(char.isalpha() for char in ep_str) and not ep_str.isdigit():
            patterns["contains_title"] += 1
        
        if length < 10:
            patterns["very_short_ids"] += 1
        elif length > 200:
            patterns["very_long_ids"] += 1
    
    # Find common prefixes
    if len(episodes) > 1:
        prefixes = defaultdict(int)
        for episode in episodes:
            ep_str = str(episode)
            if len(ep_str) >= 10:  # Only analyze reasonably long IDs
                prefix = ep_str[:10]
                prefixes[prefix] += 1
        
        # Keep prefixes that appear multiple times
        common_prefixes = [(prefix, count) for prefix, count in prefixes.items() if count > 1]
        patterns["common_prefixes"] = sorted(common_prefixes, key=lambda x: x[1], reverse=True)
    
    return patterns

def find_cross_feed_duplicates(seen_data: dict) -> list:
    """Find episodes that appear in multiple feeds"""
    all_episodes = defaultdict(list)
    
    # Collect all episodes with their feeds
    for feed, episodes in seen_data.items():
        for episode in episodes:
            all_episodes[episode].append(feed)
    
    # Find episodes that appear in multiple feeds
    duplicates = []
    for episode, feeds in all_episodes.items():
        if len(feeds) > 1:
            duplicates.append({
                "episode": episode,
                "feeds": feeds,
                "feed_count": len(feeds)
            })
    
    return sorted(duplicates, key=lambda x: x["feed_count"], reverse=True)

def generate_cleanup_suggestions(analysis: dict) -> list:
    """Generate specific cleanup suggestions"""
    suggestions = []
    
    for duplicate_info in analysis.get("potential_duplicates", []):
        feed = duplicate_info["feed"]
        for episode, count in duplicate_info["episodes"]:
            suggestions.append({
                "type": "duplicate_removal",
                "feed": feed,
                "episode": episode,
                "action": f"Remove {count-1} duplicate entries",
                "risk": "low"
            })
    
    for cross_dup in analysis.get("cross_feed_duplicates", []):
        suggestions.append({
            "type": "cross_feed_duplicate",
            "episode": cross_dup["episode"],
            "feeds": cross_dup["feeds"],
            "action": "Verify if this episode should exist in multiple feeds",
            "risk": "medium"
        })
    
    return suggestions

def main():
    cleanup_mode = "--cleanup" in sys.argv
    
    project_root = Path(__file__).parents[1]
    seen_file = project_root / "data" / "seen.json"
    
    print("🔍 Duplicate Detection Analysis")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Analyze seen file
    analysis = analyze_seen_file(seen_file)
    
    if "error" in analysis:
        print(f"❌ {analysis['error']}")
        return
    
    # Basic statistics
    print("📊 Overview")
    print("-" * 20)
    print(f"Total feeds: {analysis['total_feeds']}")
    print(f"Total episodes tracked: {analysis['total_episodes']}")
    print(f"Potential duplicates: {len(analysis['potential_duplicates'])}")
    print(f"Suspicious patterns: {len(analysis['suspicious_patterns'])}")
    print()
    
    # Feed-by-feed analysis
    print("📝 Feed Analysis")
    print("-" * 30)
    for feed_name, feed_data in analysis["feeds"].items():
        status_icon = "✅"
        issues = []
        
        if feed_data["duplicates"]:
            status_icon = "⚠️"
            issues.append(f"{len(feed_data['duplicates'])} duplicates")
        
        if feed_data["suspicious"]:
            status_icon = "🔍"
            issues.append(f"{len(feed_data['suspicious'])} suspicious patterns")
        
        if feed_data["episodes_count"] == 0:
            status_icon = "❌"
            issues.append("no episodes processed")
        
        issue_text = f" ({', '.join(issues)})" if issues else ""
        print(f"{status_icon} {feed_name}: {feed_data['episodes_count']} episodes{issue_text}")
        
        # Show duplicates if any
        if feed_data["duplicates"]:
            for episode, count in feed_data["duplicates"][:3]:  # Show first 3
                episode_short = str(episode)[:50] + "..." if len(str(episode)) > 50 else str(episode)
                print(f"    - Duplicate: {episode_short} ({count} times)")
            if len(feed_data["duplicates"]) > 3:
                print(f"    - ... and {len(feed_data['duplicates']) - 3} more")
        
        # Show suspicious patterns
        if feed_data["suspicious"]:
            for pattern in feed_data["suspicious"][:2]:  # Show first 2
                if isinstance(pattern, dict) and "episode1" in pattern:
                    print(f"    - Similar IDs: {pattern['similarity']:.2f} similarity")
                else:
                    print(f"    - Suspicious: {pattern}")
            if len(feed_data["suspicious"]) > 2:
                print(f"    - ... and {len(feed_data['suspicious']) - 2} more patterns")
    
    print()
    
    # Cross-feed duplicates
    if analysis.get("cross_feed_duplicates"):
        print("🔄 Cross-Feed Duplicates")
        print("-" * 30)
        for dup in analysis["cross_feed_duplicates"][:5]:  # Show first 5
            episode_short = str(dup["episode"])[:60] + "..." if len(str(dup["episode"])) > 60 else str(dup["episode"])
            feeds_text = ", ".join(dup["feeds"])
            print(f"  {episode_short}")
            print(f"    Found in: {feeds_text}")
        
        if len(analysis["cross_feed_duplicates"]) > 5:
            print(f"  ... and {len(analysis['cross_feed_duplicates']) - 5} more cross-feed duplicates")
        print()
    
    # Recommendations
    if analysis["recommendations"]:
        print("💡 Recommendations")
        print("-" * 30)
        for i, rec in enumerate(analysis["recommendations"], 1):
            print(f"  {i}. {rec}")
        print()
    
    # Cleanup suggestions
    if cleanup_mode:
        suggestions = generate_cleanup_suggestions(analysis)
        if suggestions:
            print("🧹 Cleanup Suggestions")
            print("-" * 30)
            for sugg in suggestions:
                risk_icon = {"low": "✅", "medium": "⚠️", "high": "❌"}.get(sugg["risk"], "❓")
                print(f"{risk_icon} {sugg['action']}")
                if sugg["type"] == "cross_feed_duplicate":
                    print(f"    Episode: {str(sugg['episode'])[:60]}...")
                    print(f"    Feeds: {', '.join(sugg['feeds'])}")
                elif sugg["type"] == "duplicate_removal":
                    print(f"    Feed: {sugg['feed']}")
                    print(f"    Episode: {str(sugg['episode'])[:60]}...")
                print()
        else:
            print("🎉 No cleanup needed!")
    
    # Summary
    total_issues = len(analysis['potential_duplicates']) + len(analysis.get('cross_feed_duplicates', []))
    if total_issues == 0:
        print("✅ No duplicate issues detected!")
    else:
        print(f"⚠️  Found {total_issues} potential issues that may need attention")

if __name__ == "__main__":
    main()