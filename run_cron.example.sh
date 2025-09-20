#!/bin/bash
# Example cron job script - customize paths for your setup

# Load environment variables
set -a
source ~/.podcast_env  # Update this path to your environment file
set +a

# Set Python path (adjust for your system)
export PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$PATH"

# Change to project directory (update this path)
cd /path/to/your/podcast-automation-public

# Run the pipeline with logging
python3 automation/pipeline.py >> logs/cron.log 2>&1