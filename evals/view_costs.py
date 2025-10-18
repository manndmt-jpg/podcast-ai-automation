#!/usr/bin/env python3
"""
View cost logs for the podcast pipeline
Usage: python3 evals/view_costs.py [--tail N]
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

def main():
    # Parse arguments
    tail_lines = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--tail" and len(sys.argv) > 2:
            tail_lines = int(sys.argv[2])

    # Find log files
    project_root = Path(__file__).parents[1]
    cost_log = project_root / "logs" / "costs.log"
    daily_totals = project_root / "logs" / "daily_costs.json"

    print("📊 Podcast Pipeline Cost Report")
    print("=" * 50)

    # Show daily totals if available
    if daily_totals.exists():
        with open(daily_totals, 'r') as f:
            totals = json.load(f)

        # Calculate totals for different periods
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%Y-%m")

        # Today's costs
        if today in totals:
            print(f"Today ({today}):")
            print(f"  Episodes: {totals[today]['episodes']}")
            print(f"  Cost: ${totals[today]['cost']:.2f}")
            print()

        # Yesterday's costs
        if yesterday in totals:
            print(f"Yesterday ({yesterday}):")
            print(f"  Episodes: {totals[yesterday]['episodes']}")
            print(f"  Cost: ${totals[yesterday]['cost']:.2f}")
            print()

        # This month's total
        monthly_total = 0
        monthly_episodes = 0
        for date_str, data in totals.items():
            if date_str.startswith(current_month):
                monthly_total += data["cost"]
                monthly_episodes += data["episodes"]

        if monthly_episodes > 0:
            print(f"Month to date ({current_month}):")
            print(f"  Episodes: {monthly_episodes}")
            print(f"  Cost: ${monthly_total:.2f}")
            print(f"  Avg per episode: ${monthly_total/monthly_episodes:.3f}")
            print()

        # All-time total
        all_time_cost = sum(data["cost"] for data in totals.values())
        all_time_episodes = sum(data["episodes"] for data in totals.values())
        if all_time_episodes > 0:
            print(f"All time:")
            print(f"  Episodes: {all_time_episodes}")
            print(f"  Cost: ${all_time_cost:.2f}")
            print(f"  Avg per episode: ${all_time_cost/all_time_episodes:.3f}")
            print()

    # Show recent log entries
    if cost_log.exists():
        print("-" * 50)
        print("Recent episode costs:")
        print()

        with open(cost_log, 'r') as f:
            lines = f.readlines()

        # If tail specified, show only last N lines
        if tail_lines:
            lines = lines[-tail_lines:]

        # Print the lines
        for line in lines:
            print(line.rstrip())

    else:
        print("No cost log found yet. Run the pipeline to start tracking costs.")

if __name__ == "__main__":
    main()