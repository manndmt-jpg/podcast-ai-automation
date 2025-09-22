"""
Cost tracking module for podcast pipeline
Tracks API usage and costs for Whisper, Claude models
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

class CostTracker:
    """Tracks and logs costs for podcast processing pipeline"""

    # Pricing as of Jan 2025 (per 1M tokens)
    PRICING = {
        'claude-3-5-haiku-20241022': {
            'input': 1.00,   # $1 per 1M input tokens
            'output': 5.00   # $5 per 1M output tokens
        },
        'claude-sonnet-4-20250514': {
            'input': 3.00,   # $3 per 1M input tokens
            'output': 15.00  # $15 per 1M output tokens
        },
        'whisper': {
            'per_minute': 0.00  # $0.00 - using local faster-whisper (free)
        }
    }

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = Path(__file__).parents[1] / "logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.cost_log = self.log_dir / "costs.log"
        self.daily_totals_file = self.log_dir / "daily_costs.json"
        self.session_costs = []

    def log_whisper_cost(self, audio_duration_minutes: float, episode_name: str = ""):
        """Log Whisper transcription cost (FREE - using local faster-whisper)"""
        cost = audio_duration_minutes * self.PRICING['whisper']['per_minute']  # $0.00
        self._append_to_log(
            f"Whisper: {audio_duration_minutes:.1f} min audio = ${cost:.3f} (local, free)",
            episode_name
        )
        self.session_costs.append(('whisper', cost))
        return cost

    def log_claude_cost(self, model: str, input_tokens: int, output_tokens: int,
                       task: str = "", episode_name: str = ""):
        """Log Claude API cost"""
        if model not in self.PRICING:
            # Fallback for unknown models
            model_key = 'claude-3-5-haiku-20241022'
        else:
            model_key = model

        input_cost = (input_tokens / 1_000_000) * self.PRICING[model_key]['input']
        output_cost = (output_tokens / 1_000_000) * self.PRICING[model_key]['output']
        total_cost = input_cost + output_cost

        task_label = f" ({task})" if task else ""
        model_short = "Haiku" if "haiku" in model.lower() else "Sonnet"

        self._append_to_log(
            f"{task or model_short}: {input_tokens:,} in + {output_tokens:,} out = ${total_cost:.3f}{task_label}",
            episode_name
        )
        self.session_costs.append((task or model_short.lower(), total_cost))
        return total_cost

    def log_episode_total(self, episode_name: str):
        """Log total cost for an episode"""
        if not self.session_costs:
            return

        total = sum(cost for _, cost in self.session_costs)

        # Write detailed breakdown
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.cost_log, 'a') as f:
            f.write(f"\n[{timestamp}] Episode: \"{episode_name}\"\n")
            for task, cost in self.session_costs:
                f.write(f"  - {task}: ${cost:.3f}\n")
            f.write(f"  TOTAL: ${total:.3f}\n")

        # Update daily total
        self._update_daily_total(total)

        # Reset session
        self.session_costs = []
        return total

    def _append_to_log(self, message: str, episode_name: str = ""):
        """Internal method to append to cost log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Don't write individual costs yet, collect them for episode total
        # This is just for tracking

    def _update_daily_total(self, amount: float):
        """Update daily totals JSON"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Load existing totals
        totals = {}
        if self.daily_totals_file.exists():
            try:
                with open(self.daily_totals_file, 'r') as f:
                    totals = json.load(f)
            except:
                totals = {}

        # Update today's total
        if today not in totals:
            totals[today] = {"episodes": 0, "cost": 0.0}

        totals[today]["episodes"] += 1
        totals[today]["cost"] += amount

        # Save back
        with open(self.daily_totals_file, 'w') as f:
            json.dump(totals, f, indent=2)

        # Log daily total
        with open(self.cost_log, 'a') as f:
            f.write(f"[{today} Running Total] Episodes: {totals[today]['episodes']}, Cost: ${totals[today]['cost']:.2f}\n")

    def estimate_token_count(self, text: str) -> int:
        """Rough estimate of token count (1 token ~= 4 chars for English)"""
        return len(text) // 4

    def get_summary(self) -> str:
        """Get cost summary for display"""
        if not self.daily_totals_file.exists():
            return "No cost data available yet."

        with open(self.daily_totals_file, 'r') as f:
            totals = json.load(f)

        # Calculate monthly total
        current_month = datetime.now().strftime("%Y-%m")
        monthly_total = 0
        monthly_episodes = 0

        for date_str, data in totals.items():
            if date_str.startswith(current_month):
                monthly_total += data["cost"]
                monthly_episodes += data["episodes"]

        today = datetime.now().strftime("%Y-%m-%d")
        today_data = totals.get(today, {"episodes": 0, "cost": 0})

        return (
            f"📊 Cost Summary\n"
            f"Today: ${today_data['cost']:.2f} ({today_data['episodes']} episodes)\n"
            f"Month: ${monthly_total:.2f} ({monthly_episodes} episodes)\n"
        )