#!/usr/bin/env python3
"""Direct video hosting helper for Zapier YouTube automated publishing.
Uploads MP4 video to high-speed public direct hosts so Zapier can stream
raw 'video/mp4' content without authentication hurdles on private GitHub repos.
"""
import sys
import json
import time
import requests
from pathlib import Path

def upload_to_direct_host(video_path: Path) -> str:
    """Uploads MP4 video and returns a verified direct download URL."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"Uploading {video_path.name} ({file_size_mb:.2f} MB) to direct video host...", file=sys.stderr)

    # 1. Primary Host: uguu.se (Supports up to 100MB, fast streaming, ~24h retention)
    for attempt in range(1, 4):
        try:
            with open(video_path, 'rb') as f:
                resp = requests.post(
                    'https://uguu.se/upload',
                    files={'files[]': (video_path.name, f, 'video/mp4')},
                    timeout=180
                )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success') and data.get('files'):
                    url = data['files'][0]['url']
                    if verify_direct_url(url):
                        print(f"Successfully uploaded to primary host (uguu.se): {url}", file=sys.stderr)
                        return url
        except Exception as e:
            print(f"[Attempt {attempt}/3] uguu.se upload attempt failed: {e}", file=sys.stderr)
            time.sleep(2)

    # 2. Secondary Host: catbox.moe (Permanent direct hosting up to 200MB)
    for attempt in range(1, 4):
        try:
            with open(video_path, 'rb') as f:
                resp = requests.post(
                    'https://catbox.moe/user/api.php',
                    data={'reqtype': 'fileupload'},
                    files={'fileToUpload': (video_path.name, f, 'video/mp4')},
                    timeout=180
                )
            if resp.status_code == 200 and resp.text.strip().startswith('http'):
                url = resp.text.strip()
                if verify_direct_url(url):
                    print(f"Successfully uploaded to secondary host (catbox.moe): {url}", file=sys.stderr)
                    return url
        except Exception as e:
            print(f"[Attempt {attempt}/3] catbox.moe upload attempt failed: {e}", file=sys.stderr)
            time.sleep(2)

    raise RuntimeError("All direct video hosting endpoints failed.")

def verify_direct_url(url: str) -> bool:
    """Verifies that the URL responds with HTTP 200/206 and a valid media type."""
    try:
        head_resp = requests.head(url, timeout=15, allow_redirects=True)
        content_type = head_resp.headers.get('Content-Type', '').lower()
        if head_resp.status_code in (200, 206) and any(m in content_type for m in ['video', 'octet-stream', 'binary']):
            return True
        # Some servers don't support HEAD properly, try Range GET for first 100 bytes
        range_resp = requests.get(url, headers={'Range': 'bytes=0-100'}, timeout=15)
        content_type = range_resp.headers.get('Content-Type', '').lower()
        return range_resp.status_code in (200, 206) and any(m in content_type for m in ['video', 'octet-stream', 'binary'])
    except Exception as e:
        print(f"URL verification warning for {url}: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_helper.py <path_to_video.mp4>", file=sys.stderr)
        sys.exit(1)

    video_path = Path(sys.argv[1])
    try:
        url = upload_to_direct_host(video_path)
        # Print ONLY the clean URL to stdout so calling scripts/workflows can capture it
        print(url)
    except Exception as e:
        print(f"Fatal upload error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
