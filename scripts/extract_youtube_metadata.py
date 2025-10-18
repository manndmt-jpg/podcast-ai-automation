# scripts/extract_youtube_metadata.py

import subprocess
import json

def get_youtube_metadata(url: str) -> dict:
    """
    Extract metadata from YouTube video using yt-dlp.
    Returns dict with title, channel, upload_date, description, id.
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        url
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)

        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "channel": data.get("uploader") or data.get("channel"),
            "upload_date": data.get("upload_date"),  # Format: YYYYMMDD
            "description": data.get("description"),
            "url": data.get("webpage_url") or url,
            "duration": data.get("duration")  # seconds
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to extract YouTube metadata: {e.stderr}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse YouTube metadata JSON: {e}")
