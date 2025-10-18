#!/usr/bin/env python3
"""
Test cost tracking functionality
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from utils.cost_tracker import CostTracker

def test_cost_tracking():
    print("Testing cost tracking module...")

    # Initialize tracker
    tracker = CostTracker()

    # Test 1: Whisper cost
    print("\n1. Testing Whisper cost tracking:")
    cost = tracker.log_whisper_cost(45.5, "Test Episode #1")
    print(f"   45.5 minutes of audio = ${cost:.3f}")

    # Test 2: Claude translation cost
    print("\n2. Testing Claude translation cost:")
    cost = tracker.log_claude_cost(
        "claude-3-5-haiku-20241022",
        input_tokens=5000,
        output_tokens=4500,
        task="Translation",
        episode_name="Test Episode #1"
    )
    print(f"   5000 in + 4500 out tokens = ${cost:.3f}")

    # Test 3: Claude summary cost
    print("\n3. Testing Claude summary cost:")
    cost = tracker.log_claude_cost(
        "claude-sonnet-4-20250514",
        input_tokens=12000,
        output_tokens=2000,
        task="Summary",
        episode_name="Test Episode #1"
    )
    print(f"   12000 in + 2000 out tokens = ${cost:.3f}")

    # Test 4: Auto-tagging cost
    print("\n4. Testing auto-tagging cost:")
    cost = tracker.log_claude_cost(
        "claude-3-5-haiku-20241022",
        input_tokens=1500,
        output_tokens=50,
        task="Auto-tagging",
        episode_name="Test Episode #1"
    )
    print(f"   1500 in + 50 out tokens = ${cost:.3f}")

    # Test 5: Episode total
    print("\n5. Testing episode total:")
    total = tracker.log_episode_total("Test Podcast: Test Episode #1")
    print(f"   Episode total cost: ${total:.3f}")

    # Test 6: Summary
    print("\n6. Cost summary:")
    print(tracker.get_summary())

    print("\n✅ Cost tracking test completed!")
    print(f"Check logs at: {tracker.cost_log}")

if __name__ == "__main__":
    test_cost_tracking()