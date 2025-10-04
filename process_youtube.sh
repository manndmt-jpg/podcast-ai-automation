#!/bin/zsh

# Simple wrapper to run YouTube video processing pipeline
# Usage: ./process_youtube.sh

cd "$(dirname "$0")"
python3 automation/youtube_pipeline.py
