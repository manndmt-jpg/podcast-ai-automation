#!/usr/bin/env python3
"""
Evaluation Log Viewer
View evaluation results and trends from log files
Usage: python3 evals/view_eval_logs.py [health|quality|performance|duplicates|summary] [--tail N]
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def view_text_log(log_file: Path, tail_lines: int = None):
    """View a text-based log file"""
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return
    
    print(f"📋 {log_file.name}")
    print("=" * 60)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if tail_lines:
        # Show only recent entries
        entries = content.split('=' * 60)
        entries = [entry.strip() for entry in entries if entry.strip()]
        
        if entries:
            recent_entries = entries[-tail_lines:]
            for entry in recent_entries:
                print('=' * 60)
                print(entry)
        else:
            print("No entries found")
    else:
        print(content)

def view_summary_log(log_file: Path, tail_entries: int = None):
    """View the JSON summary log with trend analysis"""
    if not log_file.exists():
        print(f"❌ Summary log not found: {log_file}")
        return
    
    try:
        with open(log_file, 'r') as f:
            summaries = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read summary log: {e}")
        return
    
    if not summaries:
        print("📭 No summary data available yet")
        return
    
    print(f"📊 Evaluation Summary Trends ({len(summaries)} entries)")
    print("=" * 60)
    
    # Limit to recent entries if requested
    if tail_entries:
        summaries = summaries[-tail_entries:]
    
    # Show recent entries
    print("\n🔍 Recent Evaluations:")
    print("-" * 40)
    
    for i, summary in enumerate(summaries[-10:], 1):  # Show last 10
        timestamp = datetime.fromisoformat(summary['timestamp']).strftime('%Y-%m-%d %H:%M')
        mode = summary.get('mode', 'unknown')
        success = summary.get('success_count', 0)
        total = summary.get('total_evaluations', 0)
        issues = summary.get('total_issues', 0)
        
        status_icon = "✅" if issues == 0 else "⚠️" if issues < 5 else "❌"
        
        print(f"{i:2d}. [{timestamp}] {mode:8} - {success}/{total} success {status_icon}")
        if issues > 0:
            print(f"     Issues: {issues} found")
    
    # Analyze trends
    if len(summaries) >= 5:
        print("\n📈 Trends Analysis:")
        print("-" * 40)
        
        # Health trends
        recent_health = [s for s in summaries[-10:] if s.get('feeds_checked', 0) > 0]
        if recent_health:
            avg_healthy = sum(s.get('feeds_healthy', 0) for s in recent_health) / len(recent_health)
            avg_warnings = sum(s.get('feeds_with_warnings', 0) for s in recent_health) / len(recent_health)
            print(f"Feed Health: {avg_healthy:.1f} healthy, {avg_warnings:.1f} warnings (avg last 10 runs)")
        
        # Quality trends
        recent_quality = [s for s in summaries[-10:] if s.get('episodes_analyzed', 0) > 0]
        if recent_quality:
            avg_issues = sum(s.get('quality_issues', 0) for s in recent_quality) / len(recent_quality)
            avg_length = sum(s.get('avg_summary_length', 0) for s in recent_quality if s.get('avg_summary_length'))
            if avg_length:
                avg_length = avg_length / len([s for s in recent_quality if s.get('avg_summary_length')])
                print(f"Quality: {avg_issues:.1f} issues, {avg_length:.0f} words (avg)")
        
        # Performance trends
        recent_perf = [s for s in summaries[-10:] if s.get('processing_success_rate') is not None]
        if recent_perf:
            avg_success = sum(s.get('processing_success_rate', 0) for s in recent_perf) / len(recent_perf)
            print(f"Performance: {avg_success:.1f}% success rate (avg)")
        
        # Issue trends
        recent_issues = [s.get('total_issues', 0) for s in summaries[-10:]]
        if recent_issues:
            avg_issues = sum(recent_issues) / len(recent_issues)
            trend = "📈" if recent_issues[-1] > avg_issues else "📉" if recent_issues[-1] < avg_issues else "➡️"
            print(f"Issues: {avg_issues:.1f} average, current: {recent_issues[-1]} {trend}")
    
    # Show latest summary
    if summaries:
        latest = summaries[-1]
        print(f"\n📋 Latest Summary ({datetime.fromisoformat(latest['timestamp']).strftime('%Y-%m-%d %H:%M')}):")
        print("-" * 40)
        
        if latest.get('feeds_checked', 0) > 0:
            print(f"Feeds: {latest.get('feeds_healthy', 0)} healthy, {latest.get('feeds_with_warnings', 0)} warnings, {latest.get('feeds_unhealthy', 0)} unhealthy")
        
        if latest.get('episodes_analyzed', 0) > 0:
            print(f"Quality: {latest.get('episodes_analyzed', 0)} episodes, {latest.get('quality_issues', 0)} issues")
            if latest.get('avg_summary_length'):
                print(f"Average summary: {latest.get('avg_summary_length', 0)} words")
        
        if latest.get('processing_success_rate') is not None:
            print(f"Performance: {latest.get('processing_success_rate', 0):.1f}% success rate")
        
        if latest.get('duplicates_found', 0) > 0:
            print(f"Duplicates: {latest.get('duplicates_found', 0)} potential issues")
        
        total_issues = latest.get('total_issues', 0)
        if total_issues == 0:
            print("🎉 No issues detected!")
        else:
            print(f"⚠️  Total issues: {total_issues}")

def list_log_files():
    """List available evaluation log files"""
    project_root = Path(__file__).parents[1]
    logs_dir = project_root / 'logs'
    
    eval_logs = list(logs_dir.glob('eval_*.log')) + list(logs_dir.glob('eval_*.json'))
    
    if not eval_logs:
        print("📭 No evaluation logs found yet")
        print("Run: python3 evals/eval_runner.py")
        return
    
    print("📁 Available Evaluation Logs:")
    print("-" * 40)
    
    for log_file in sorted(eval_logs):
        if log_file.suffix == '.json':
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    entries = len(data) if isinstance(data, list) else 1
                print(f"📊 {log_file.name:20} → {entries} entries")
            except:
                print(f"📊 {log_file.name:20} → (error reading)")
        else:
            try:
                size_kb = log_file.stat().st_size / 1024
                print(f"📋 {log_file.name:20} → {size_kb:.1f} KB")
            except:
                print(f"📋 {log_file.name:20} → (error reading)")

def main():
    # Parse arguments
    log_type = None
    tail_lines = None
    
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if arg1 in ['health', 'quality', 'performance', 'duplicates', 'summary']:
            log_type = arg1
        
        # Check for --tail option
        if '--tail' in sys.argv:
            tail_idx = sys.argv.index('--tail')
            if tail_idx + 1 < len(sys.argv):
                try:
                    tail_lines = int(sys.argv[tail_idx + 1])
                except ValueError:
                    print("❌ Invalid tail count")
                    return
    
    project_root = Path(__file__).parents[1]
    logs_dir = project_root / 'logs'
    
    if not log_type:
        print("📋 Evaluation Log Viewer")
        print("=" * 30)
        list_log_files()
        print("\nUsage:")
        print("  python3 evals/view_eval_logs.py [health|quality|performance|duplicates|summary]")
        print("  python3 evals/view_eval_logs.py summary --tail 5")
        return
    
    # View specific log
    if log_type == 'summary':
        log_file = logs_dir / 'eval_summary.json'
        view_summary_log(log_file, tail_lines)
    else:
        log_file = logs_dir / f'eval_{log_type}.log'
        view_text_log(log_file, tail_lines)

if __name__ == "__main__":
    main()