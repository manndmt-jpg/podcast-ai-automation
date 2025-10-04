# scripts/download_youtube.py

import os
import subprocess
import pathlib

def download_youtube_audio(url: str, output_dir: str, base_name: str) -> str:
    """
    Download YouTube video and extract audio as MP3 using yt-dlp.
    Returns path to the downloaded MP3 file.
    """
    out_dir = pathlib.Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Output template
    output_template = str(out_dir / f"{base_name}.mp3")

    # yt-dlp command: download best audio, convert to mp3
    cmd = [
        "yt-dlp",
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",  # Best quality
        "-o", output_template,
        url
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # yt-dlp might add .mp3 extension, verify file exists
        if os.path.exists(output_template):
            return output_template

        # Check if yt-dlp created file with different extension handling
        possible_paths = [
            output_template,
            output_template + ".mp3"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError(f"Downloaded file not found at expected location: {output_template}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp failed: {e.stderr}")
