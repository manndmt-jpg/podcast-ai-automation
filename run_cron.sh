#!/bin/bash
# Load env for cron
set -a
. /Users/dmitrymuzhikov/.podcast_env
set +a

# Ensure python is on PATH (belt-and-suspenders)
export PATH="/usr/local/bin:/usr/bin:/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"

cd /Users/dmitrymuzhikov/podcast_summary_project
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 automation/pipeline.py >> /Users/dmitrymuzhikov/podcast_summary_project/logs/cron.log 2>&1