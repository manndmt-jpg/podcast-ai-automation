import os
import sys
import re
import requests

def slugify(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")[:120]

def download_mp3(url: str, out_dir: str, filename_base: str = "episode"):
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{slugify(filename_base)}.mp3"
    path = os.path.join(out_dir, fname)

    headers = {"User-Agent": "Mozilla/5.0"}
    with requests.get(url, headers=headers, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return path

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/download_audio.py <MP3_URL> <OUT_DIR> <FILENAME_BASE>")
        sys.exit(1)
    mp3_url = sys.argv[1]
    out_dir = sys.argv[2]
    base = sys.argv[3]
    p = download_mp3(mp3_url, out_dir, base)
    print("Saved:", p)
