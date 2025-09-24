#!/usr/bin/env python3
"""
RSS Feed Health Monitor
Checks feed availability, validates content, and monitors for issues
Usage: python3 evals/feed_health.py [--verbose]
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import time

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parents[1]))

from scripts.fetch_feed import get_latest_episode
import feedparser
import requests

def check_feed_availability(rss_url: str, timeout: int = 10) -> dict:
    """Check if RSS feed is accessible"""
    try:
        response = requests.get(rss_url, timeout=timeout, headers={
            'User-Agent': 'Podcast-Automation/1.0 (Personal Use)'
        })
        
        if response.status_code == 200:
            # Try to parse as RSS
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                return {
                    "status": "warning",
                    "message": f"Feed parsed with errors: {feed.bozo_exception}",
                    "http_code": response.status_code
                }
            
            return {
                "status": "ok",
                "message": "Feed accessible and valid",
                "http_code": response.status_code,
                "entries_count": len(feed.entries),
                "feed_title": getattr(feed.feed, 'title', 'Unknown'),
                "last_updated": getattr(feed.feed, 'updated', None)
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.reason}",
                "http_code": response.status_code
            }
    
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Request timed out",
            "http_code": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error", 
            "message": "Connection error",
            "http_code": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "http_code": None
        }

def analyze_feed_content(feed_info: dict) -> dict:
    """Analyze feed content for potential issues"""
    rss_url = feed_info["rss"]
    
    try:
        # Get latest episode info using our existing function
        latest = get_latest_episode(rss_url)
        
        if not latest:
            return {
                "status": "warning",
                "message": "No episodes found in feed"
            }
        
        issues = []
        warnings = []
        
        # Check for missing essential fields
        if not latest.get("mp3_url"):
            issues.append("Latest episode missing MP3 URL")
        
        if not latest.get("title"):
            issues.append("Latest episode missing title")
            
        if not latest.get("published"):
            warnings.append("Latest episode missing publication date")
        
        # Check publication date recency
        if latest.get("published"):
            try:
                # Parse date string - handle multiple formats
                if isinstance(latest["published"], str):
                    date_str = latest["published"]
                    # Try ISO 8601 format first (most common in modern RSS feeds)
                    try:
                        if 'T' in date_str:
                            # ISO 8601 format: 2025-09-22T10:00:00+00:00
                            if date_str.endswith('Z'):
                                date_str = date_str.replace('Z', '+00:00')
                            pub_date = datetime.fromisoformat(date_str)
                        else:
                            # RFC 2822 format: Wed, 22 Sep 2025 10:00:00 +0000
                            pub_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    except ValueError:
                        # Try other common formats
                        try:
                            pub_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                        except ValueError:
                            raise ValueError(f"Unsupported date format: {date_str}")
                else:
                    pub_date = latest["published"]
                
                # Check if timezone-aware, if not assume UTC
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                
                days_old = (datetime.now(timezone.utc) - pub_date).days
                
                if days_old > 90:
                    issues.append(f"Latest episode is very old ({days_old} days)")
                elif days_old > 30:
                    warnings.append(f"Latest episode is {days_old} days old")
                    
            except Exception as e:
                # Only warn if it's actually a problem
                warnings.append(f"Could not parse publication date format: {latest.get('published', 'unknown')}")
        
        # Determine overall status
        if issues:
            status = "error"
            message = f"{len(issues)} critical issues found"
        elif warnings:
            status = "warning" 
            message = f"{len(warnings)} warnings found"
        else:
            status = "ok"
            message = "Content looks good"
        
        return {
            "status": status,
            "message": message,
            "issues": issues,
            "warnings": warnings,
            "latest_episode": {
                "title": latest.get("title", "Unknown"),
                "published": latest.get("published", "Unknown"),
                "has_mp3": bool(latest.get("mp3_url"))
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to analyze content: {str(e)}"
        }

def check_seen_status(feed_name: str, seen_data: dict) -> dict:
    """Check processing status for this feed"""
    if feed_name not in seen_data:
        return {
            "status": "new",
            "message": "Feed not yet processed",
            "processed_count": 0
        }
    
    processed_episodes = seen_data[feed_name]
    count = len(processed_episodes)
    
    return {
        "status": "processed",
        "message": f"{count} episodes processed",
        "processed_count": count,
        "latest_processed": processed_episodes[-1] if processed_episodes else None
    }

def main():
    verbose = "--verbose" in sys.argv
    
    project_root = Path(__file__).parents[1]
    feeds_config = project_root / "config" / "feeds.json"
    seen_file = project_root / "data" / "seen.json"
    
    if not feeds_config.exists():
        print("❌ feeds.json not found")
        return
    
    print("🏥 RSS Feed Health Check")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load configuration
    with open(feeds_config, 'r') as f:
        feeds = json.load(f)
    
    # Load seen episodes if available
    seen_data = {}
    if seen_file.exists():
        with open(seen_file, 'r') as f:
            seen_data = json.load(f)
    
    overall_stats = {
        "total_feeds": len(feeds),
        "healthy_feeds": 0,
        "feeds_with_warnings": 0,
        "unhealthy_feeds": 0,
        "total_issues": 0
    }
    
    for i, feed in enumerate(feeds, 1):
        name = feed.get("name", f"Feed #{i}")
        rss_url = feed.get("rss")
        tags = feed.get("tags", [])
        
        print(f"🎧 {name}")
        print("-" * 40)
        
        if not rss_url:
            print("  ❌ No RSS URL configured")
            overall_stats["unhealthy_feeds"] += 1
            overall_stats["total_issues"] += 1
            print()
            continue
        
        if verbose:
            print(f"  URL: {rss_url}")
            print(f"  Tags: {', '.join(tags) if tags else 'None'}")
        
        # Check feed availability
        print("  🌐 Checking availability...", end=" ")
        availability = check_feed_availability(rss_url)
        
        if availability["status"] == "ok":
            print("✅ OK")
            if verbose:
                print(f"      Entries: {availability.get('entries_count', 'Unknown')}")
                print(f"      Title: {availability.get('feed_title', 'Unknown')}")
        elif availability["status"] == "warning":
            print(f"⚠️  {availability['message']}")
            overall_stats["feeds_with_warnings"] += 1
        else:
            print(f"❌ {availability['message']}")
            overall_stats["unhealthy_feeds"] += 1
            overall_stats["total_issues"] += 1
            print()
            continue
        
        # Analyze content
        print("  📝 Analyzing content...", end=" ")
        content_analysis = analyze_feed_content(feed)
        
        if content_analysis["status"] == "ok":
            print("✅ OK")
            overall_stats["healthy_feeds"] += 1
        elif content_analysis["status"] == "warning":
            print(f"⚠️  {content_analysis['message']}")
            overall_stats["feeds_with_warnings"] += 1
            if verbose and content_analysis.get("warnings"):
                for warning in content_analysis["warnings"]:
                    print(f"      - {warning}")
        else:
            print(f"❌ {content_analysis['message']}")
            overall_stats["unhealthy_feeds"] += 1
            overall_stats["total_issues"] += 1
            if verbose and content_analysis.get("issues"):
                for issue in content_analysis["issues"]:
                    print(f"      - {issue}")
        
        # Show latest episode info if available
        if content_analysis.get("latest_episode"):
            latest = content_analysis["latest_episode"]
            if verbose:
                print(f"      Latest: {latest['title']}")
                print(f"      Published: {latest['published']}")
                print(f"      Has MP3: {'Yes' if latest['has_mp3'] else 'No'}")
        
        # Check processing status
        seen_status = check_seen_status(name, seen_data)
        print(f"  📊 Processing: {seen_status['message']}")
        
        print()
        
        # Brief delay to be respectful to servers
        if i < len(feeds):
            time.sleep(0.5)
    
    # Summary
    print("=" * 50)
    print("📊 Health Summary")
    print("-" * 20)
    print(f"Total feeds: {overall_stats['total_feeds']}")
    print(f"Healthy: {overall_stats['healthy_feeds']}")
    print(f"With warnings: {overall_stats['feeds_with_warnings']}")
    print(f"Unhealthy: {overall_stats['unhealthy_feeds']}")
    print(f"Total issues: {overall_stats['total_issues']}")
    
    if overall_stats["total_issues"] == 0:
        print("\n🎉 All feeds are healthy!")
    else:
        print(f"\n⚠️  {overall_stats['total_issues']} issues need attention")

if __name__ == "__main__":
    main()