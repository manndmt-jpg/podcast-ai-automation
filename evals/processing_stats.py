#!/usr/bin/env python3
"""
Processing Efficiency Analysis
Analyzes pipeline performance, processing times, and identifies bottlenecks
Usage: python3 evals/processing_stats.py [--days N]
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import json

def parse_cron_log(log_file: Path, days_back: int = 7) -> dict:
    """Parse cron log for processing statistics"""
    if not log_file.exists():
        return {"error": "Log file not found"}
    
    stats = {
        "runs": [],
        "episodes_processed": 0,
        "episodes_skipped": 0,
        "feeds_processed": defaultdict(int),
        "feeds_skipped": defaultdict(int),
        "errors": [],
        "processing_times": {},
        "date_range": {"start": None, "end": None}
    }
    
    # Calculate date cutoff
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"error": f"Failed to read log: {e}"}
    
    # Split into runs (each run starts with "=== Podcast automation pipeline started ===")
    runs = re.split(r'=== Podcast automation pipeline started ===', content)[1:]  # Skip first empty part
    
    for run_content in runs:
        run_data = parse_single_run(run_content, cutoff_date)
        if run_data:
            stats["runs"].append(run_data)
            
            # Aggregate statistics
            stats["episodes_processed"] += run_data.get("episodes_processed", 0)
            stats["episodes_skipped"] += run_data.get("episodes_skipped", 0)
            
            for feed, count in run_data.get("feeds_processed", {}).items():
                stats["feeds_processed"][feed] += count
            
            for feed, count in run_data.get("feeds_skipped", {}).items():
                stats["feeds_skipped"][feed] += count
            
            if run_data.get("errors"):
                stats["errors"].extend(run_data["errors"])
    
    # Set date range
    if stats["runs"]:
        stats["date_range"]["start"] = min(run["timestamp"] for run in stats["runs"])
        stats["date_range"]["end"] = max(run["timestamp"] for run in stats["runs"])
    
    return stats

def parse_single_run(run_content: str, cutoff_date: datetime) -> dict:
    """Parse a single pipeline run from log content"""
    lines = run_content.strip().split('\n')
    
    run_data = {
        "timestamp": None,
        "duration": None,
        "episodes_processed": 0,
        "episodes_skipped": 0,
        "feeds_processed": defaultdict(int),
        "feeds_skipped": defaultdict(int),
        "errors": [],
        "cost_summary": None
    }
    
    current_feed = None
    
    for line in lines:
        line = line.strip()
        
        # Extract timestamp from first line
        timestamp_match = re.search(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
        if timestamp_match and run_data["timestamp"] is None:
            try:
                timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                if timestamp < cutoff_date:
                    return None  # Skip old runs
                run_data["timestamp"] = timestamp
            except ValueError:
                pass
        
        # Track current feed being processed
        feed_match = re.search(r'== (.+) ==$', line)
        if feed_match:
            current_feed = feed_match.group(1)
        
        # Count processed episodes
        if "Audio:" in line and "mp3" in line:
            run_data["episodes_processed"] += 1
            if current_feed:
                run_data["feeds_processed"][current_feed] += 1
        
        # Count skipped episodes
        if "Skipping. Already processed:" in line:
            run_data["episodes_skipped"] += 1
            if current_feed:
                run_data["feeds_skipped"][current_feed] += 1
        
        # Track errors
        if "error" in line.lower() or "failed" in line.lower() or "exception" in line.lower():
            run_data["errors"].append({
                "feed": current_feed,
                "message": line,
                "timestamp": run_data["timestamp"]
            })
        
        # Extract cost summary
        cost_match = re.search(r'Episode cost: \$(\d+\.\d+)', line)
        if cost_match:
            cost = float(cost_match.group(1))
            if run_data["cost_summary"] is None:
                run_data["cost_summary"] = {"total_cost": 0, "episode_costs": []}
            run_data["cost_summary"]["total_cost"] += cost
            run_data["cost_summary"]["episode_costs"].append(cost)
        
        # Check for completion
        if "=== Podcast automation pipeline completed ===" in line:
            # Try to extract timestamp for duration calculation
            end_timestamp_match = re.search(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
            if end_timestamp_match and run_data["timestamp"]:
                try:
                    end_time = datetime.strptime(end_timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                    duration = (end_time - run_data["timestamp"]).total_seconds()
                    run_data["duration"] = duration
                except ValueError:
                    pass
    
    return run_data if run_data["timestamp"] else None

def analyze_processing_patterns(stats: dict) -> dict:
    """Analyze processing patterns and identify issues"""
    analysis = {
        "avg_runtime": 0,
        "success_rate": 0,
        "most_active_feeds": [],
        "problematic_feeds": [],
        "processing_efficiency": {},
        "recommendations": []
    }
    
    if not stats["runs"]:
        return analysis
    
    # Calculate average runtime
    runtimes = [run["duration"] for run in stats["runs"] if run["duration"]]
    if runtimes:
        analysis["avg_runtime"] = sum(runtimes) / len(runtimes)
    
    # Calculate success rate (runs without errors)
    successful_runs = sum(1 for run in stats["runs"] if not run["errors"])
    analysis["success_rate"] = successful_runs / len(stats["runs"]) * 100
    
    # Most active feeds (processed most episodes)
    feed_activity = [(feed, count) for feed, count in stats["feeds_processed"].items()]
    analysis["most_active_feeds"] = sorted(feed_activity, key=lambda x: x[1], reverse=True)[:5]
    
    # Problematic feeds (high error rate or no processing)
    for feed in stats["feeds_processed"]:
        feed_errors = sum(1 for run in stats["runs"] for error in run["errors"] if error["feed"] == feed)
        if feed_errors > len(stats["runs"]) * 0.5:  # More than 50% error rate
            analysis["problematic_feeds"].append((feed, "High error rate"))
    
    # Check for feeds that are never processing new content
    total_feeds = set(stats["feeds_processed"].keys()) | set(stats["feeds_skipped"].keys())
    for feed in total_feeds:
        processed = stats["feeds_processed"].get(feed, 0)
        skipped = stats["feeds_skipped"].get(feed, 0)
        if processed == 0 and skipped > 0:
            analysis["problematic_feeds"].append((feed, "Only skipping, no new content"))
    
    # Processing efficiency
    if stats["episodes_processed"] > 0:
        analysis["processing_efficiency"]["episodes_per_run"] = stats["episodes_processed"] / len(stats["runs"])
        analysis["processing_efficiency"]["skip_rate"] = stats["episodes_skipped"] / (stats["episodes_processed"] + stats["episodes_skipped"]) * 100
    
    # Generate recommendations
    if analysis["success_rate"] < 90:
        analysis["recommendations"].append("Success rate is below 90% - investigate recurring errors")
    
    if analysis["processing_efficiency"].get("skip_rate", 0) > 95:
        analysis["recommendations"].append("Very high skip rate - most feeds may not have new content")
    
    if len(analysis["problematic_feeds"]) > 0:
        analysis["recommendations"].append(f"{len(analysis['problematic_feeds'])} feeds have issues - check feed configurations")
    
    if analysis["avg_runtime"] > 600:  # 10 minutes
        analysis["recommendations"].append("Average runtime is high - consider optimizing processing")
    
    return analysis

def main():
    # Parse arguments
    days_back = 7
    if len(sys.argv) > 1:
        if sys.argv[1] == "--days" and len(sys.argv) > 2:
            days_back = int(sys.argv[2])
    
    project_root = Path(__file__).parents[1]
    log_file = project_root / "logs" / "cron.log"
    
    print(f"🔍 Processing Efficiency Analysis (Last {days_back} days)")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Parse log data
    stats = parse_cron_log(log_file, days_back)
    
    if "error" in stats:
        print(f"❌ {stats['error']}")
        return
    
    if not stats["runs"]:
        print("📭 No pipeline runs found in the specified time period")
        return
    
    # Basic statistics
    print("📊 Basic Statistics")
    print("-" * 30)
    print(f"Total runs: {len(stats['runs'])}")
    print(f"Episodes processed: {stats['episodes_processed']}")
    print(f"Episodes skipped: {stats['episodes_skipped']}")
    print(f"Total errors: {len(stats['errors'])}")
    
    if stats['date_range']['start'] and stats['date_range']['end']:
        start_date = stats['date_range']['start'].strftime('%Y-%m-%d %H:%M')
        end_date = stats['date_range']['end'].strftime('%Y-%m-%d %H:%M')
        print(f"Period: {start_date} to {end_date}")
    
    print()
    
    # Performance analysis
    analysis = analyze_processing_patterns(stats)
    
    print("⚡ Performance Analysis")
    print("-" * 30)
    print(f"Success rate: {analysis['success_rate']:.1f}%")
    
    if analysis['avg_runtime'] > 0:
        print(f"Average runtime: {analysis['avg_runtime']:.1f} seconds ({analysis['avg_runtime']/60:.1f} min)")
    
    if analysis['processing_efficiency']:
        eff = analysis['processing_efficiency']
        if 'episodes_per_run' in eff:
            print(f"Episodes per run: {eff['episodes_per_run']:.1f}")
        if 'skip_rate' in eff:
            print(f"Skip rate: {eff['skip_rate']:.1f}%")
    
    print()
    
    # Feed activity
    if analysis['most_active_feeds']:
        print("🎧 Most Active Feeds")
        print("-" * 30)
        for feed, count in analysis['most_active_feeds']:
            print(f"  {feed}: {count} episodes processed")
        print()
    
    # Problematic feeds
    if analysis['problematic_feeds']:
        print("⚠️  Problematic Feeds")
        print("-" * 30)
        for feed, issue in analysis['problematic_feeds']:
            print(f"  {feed}: {issue}")
        print()
    
    # Recent errors
    if stats['errors']:
        recent_errors = sorted(stats['errors'], key=lambda x: x['timestamp'], reverse=True)[:5]
        print("🚨 Recent Errors")
        print("-" * 30)
        for error in recent_errors:
            timestamp = error['timestamp'].strftime('%Y-%m-%d %H:%M')
            feed = error.get('feed', 'Unknown')
            message = error['message'][:100] + "..." if len(error['message']) > 100 else error['message']
            print(f"  [{timestamp}] {feed}: {message}")
        
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more errors")
        print()
    
    # Recommendations
    if analysis['recommendations']:
        print("💡 Recommendations")
        print("-" * 30)
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
        print()
    
    # Cost analysis if available
    total_costs = []
    for run in stats['runs']:
        if run.get('cost_summary') and run['cost_summary'].get('total_cost'):
            total_costs.append(run['cost_summary']['total_cost'])
    
    if total_costs:
        print("💰 Cost Analysis")
        print("-" * 30)
        total_cost = sum(total_costs)
        avg_cost_per_run = total_cost / len(total_costs)
        print(f"Total cost (period): ${total_cost:.2f}")
        print(f"Average per run: ${avg_cost_per_run:.2f}")
        if stats['episodes_processed'] > 0:
            avg_per_episode = total_cost / stats['episodes_processed']
            print(f"Average per episode: ${avg_per_episode:.3f}")
        print()
    
    # Summary status
    if analysis['success_rate'] >= 95 and len(analysis['problematic_feeds']) == 0:
        print("✅ Pipeline is running efficiently!")
    elif analysis['success_rate'] >= 85:
        print("⚠️  Pipeline has some issues but is generally functional")
    else:
        print("❌ Pipeline has significant issues that need attention")

if __name__ == "__main__":
    main()