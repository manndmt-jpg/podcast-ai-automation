#!/usr/bin/env python3
"""
Centralized Evaluation Runner
Runs all evaluation scripts and logs results to dedicated files
Usage: python3 evals/eval_runner.py [--daily|--weekly|--monthly]
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class EvalLogger:
    """Handles logging evaluation results to dedicated files"""
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(exist_ok=True)
        
        # Define log files for different evaluation types
        self.log_files = {
            'health': logs_dir / 'eval_health.log',
            'quality': logs_dir / 'eval_quality.log', 
            'performance': logs_dir / 'eval_performance.log',
            'duplicates': logs_dir / 'eval_duplicates.log',
            'summary': logs_dir / 'eval_summary.json'
        }
    
    def log_evaluation(self, eval_type: str, output: str, status: str = 'success'):
        """Log evaluation results with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_file = self.log_files.get(eval_type)
        if not log_file:
            return
        
        # Write to dedicated log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{timestamp}] {eval_type.upper()} EVALUATION - {status.upper()}\n")
            f.write('='*60 + '\n')
            f.write(output)
            f.write('\n')
    
    def log_summary(self, summary_data: Dict[str, Any]):
        """Log summary data as JSON for easy parsing"""
        timestamp = datetime.now().isoformat()
        
        # Load existing summaries
        summaries = []
        if self.log_files['summary'].exists():
            try:
                with open(self.log_files['summary'], 'r') as f:
                    summaries = json.load(f)
            except:
                summaries = []
        
        # Add new summary
        summary_data['timestamp'] = timestamp
        summaries.append(summary_data)
        
        # Keep only last 100 entries
        summaries = summaries[-100:]
        
        # Save back
        with open(self.log_files['summary'], 'w') as f:
            json.dump(summaries, f, indent=2)

def run_evaluation(script_name: str, args: list = None) -> tuple[str, str, int]:
    """Run an evaluation script and capture output"""
    project_root = Path(__file__).parents[1]
    script_path = project_root / "evals" / script_name
    
    cmd = ["python3", str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=str(project_root),
            timeout=120  # 2 minute timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Evaluation timed out after 2 minutes", 1
    except Exception as e:
        return "", f"Failed to run evaluation: {e}", 1

def extract_summary_data(outputs: Dict[str, str]) -> Dict[str, Any]:
    """Extract key metrics from evaluation outputs for summary logging"""
    summary = {
        'feeds_checked': 0,
        'feeds_healthy': 0,
        'feeds_with_warnings': 0,
        'feeds_unhealthy': 0,
        'episodes_analyzed': 0,
        'quality_issues': 0,
        'duplicates_found': 0,
        'processing_success_rate': None,
        'avg_summary_length': None,
        'total_issues': 0
    }
    
    # Extract health data
    if 'health' in outputs:
        health_output = outputs['health']
        import re
        
        # Parse health summary
        if match := re.search(r'Total feeds: (\d+)', health_output):
            summary['feeds_checked'] = int(match.group(1))
        if match := re.search(r'Healthy: (\d+)', health_output):
            summary['feeds_healthy'] = int(match.group(1))
        if match := re.search(r'With warnings: (\d+)', health_output):
            summary['feeds_with_warnings'] = int(match.group(1))
        if match := re.search(r'Unhealthy: (\d+)', health_output):
            summary['feeds_unhealthy'] = int(match.group(1))
    
    # Extract quality data
    if 'quality' in outputs:
        quality_output = outputs['quality']
        if match := re.search(r'Total episodes analyzed: (\d+)', quality_output):
            summary['episodes_analyzed'] = int(match.group(1))
        if match := re.search(r'Total issues found: (\d+)', quality_output):
            summary['quality_issues'] = int(match.group(1))
        if match := re.search(r'Average summary length: (\d+)', quality_output):
            summary['avg_summary_length'] = int(match.group(1))
    
    # Extract performance data
    if 'performance' in outputs:
        performance_output = outputs['performance']
        if match := re.search(r'Success rate: ([\d.]+)%', performance_output):
            summary['processing_success_rate'] = float(match.group(1))
    
    # Extract duplicate data
    if 'duplicates' in outputs:
        duplicates_output = outputs['duplicates']
        if match := re.search(r'Found (\d+) potential issues', duplicates_output):
            summary['duplicates_found'] = int(match.group(1))
    
    # Calculate total issues
    summary['total_issues'] = (
        summary['feeds_unhealthy'] + 
        summary['quality_issues'] + 
        summary['duplicates_found']
    )
    
    return summary

def main():
    mode = 'manual'
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--daily', '--weekly', '--monthly']:
            mode = sys.argv[1].strip('--')
    
    project_root = Path(__file__).parents[1]
    logger = EvalLogger(project_root / 'logs')
    
    print("🔍 Running Podcast Evaluation Suite")
    print("=" * 50)
    print(f"Mode: {mode}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Define evaluation configurations
    evaluations = {
        'health': {
            'script': 'feed_health.py',
            'args': ['--verbose'] if mode in ['weekly', 'monthly'] else [],
            'description': 'RSS Feed Health Check'
        },
        'quality': {
            'script': 'quality_check.py', 
            'args': ['--recent', '10'] if mode == 'daily' else [],
            'description': 'Content Quality Analysis'
        },
        'performance': {
            'script': 'processing_stats.py',
            'args': ['--days', '1'] if mode == 'daily' else ['--days', '7'] if mode == 'weekly' else ['--days', '30'],
            'description': 'Processing Performance Analysis'
        },
        'duplicates': {
            'script': 'duplicate_analysis.py',
            'args': [],
            'description': 'Duplicate Detection Analysis'
        }
    }
    
    # Skip some evaluations for daily runs
    if mode == 'daily':
        evaluations.pop('duplicates', None)  # Skip duplicates for daily
    
    results = {}
    outputs = {}
    
    # Run each evaluation
    for eval_name, config in evaluations.items():
        print(f"🔄 Running {config['description']}...")
        
        stdout, stderr, returncode = run_evaluation(config['script'], config['args'])
        
        if returncode == 0:
            print(f"✅ {eval_name} completed")
            status = 'success'
            output = stdout
        else:
            print(f"❌ {eval_name} failed: {stderr}")
            status = 'error'
            output = f"ERROR: {stderr}\n\nSTDOUT: {stdout}"
        
        # Log to dedicated file
        logger.log_evaluation(eval_name, output, status)
        
        results[eval_name] = {
            'status': status,
            'returncode': returncode
        }
        outputs[eval_name] = stdout
    
    # Extract and log summary data
    summary_data = extract_summary_data(outputs)
    summary_data['mode'] = mode
    summary_data['evaluations_run'] = list(evaluations.keys())
    summary_data['success_count'] = sum(1 for r in results.values() if r['status'] == 'success')
    summary_data['total_evaluations'] = len(results)
    
    logger.log_summary(summary_data)
    
    # Display summary
    print("\n" + "=" * 50)
    print("📊 Evaluation Summary")
    print("-" * 30)
    
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    print(f"Completed: {successful}/{total} evaluations")
    
    if summary_data['feeds_checked'] > 0:
        print(f"Feeds: {summary_data['feeds_healthy']} healthy, {summary_data['feeds_with_warnings']} warnings, {summary_data['feeds_unhealthy']} unhealthy")
    
    if summary_data['episodes_analyzed'] > 0:
        print(f"Episodes: {summary_data['episodes_analyzed']} analyzed, {summary_data['quality_issues']} quality issues")
    
    if summary_data['processing_success_rate'] is not None:
        print(f"Processing: {summary_data['processing_success_rate']:.1f}% success rate")
    
    if summary_data['duplicates_found'] > 0:
        print(f"Duplicates: {summary_data['duplicates_found']} potential issues found")
    
    total_issues = summary_data['total_issues']
    if total_issues == 0:
        print("\n🎉 No issues detected across all evaluations!")
    else:
        print(f"\n⚠️  Total issues found: {total_issues}")
    
    print(f"\n📁 Results logged to: logs/eval_*.log")
    print(f"📊 Summary data: logs/eval_summary.json")
    
    # Show recent log file locations
    print("\n📋 Log Files:")
    for eval_type, log_file in logger.log_files.items():
        if eval_type != 'summary' and log_file.exists():
            size_kb = log_file.stat().st_size / 1024
            print(f"  {eval_type:12} → {log_file} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()