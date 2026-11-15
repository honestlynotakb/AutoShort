#!/usr/bin/env python3
"""Direct YouTube Data API v3 uploader using OAuth2 refresh token.
Uploads 1080x1920 MP4 Shorts directly to your YouTube channel.
Includes Gate 5 Application-Level Upload Idempotency protection.

Reads credentials from environment variables:
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN
"""
import os
import sys
import time
import argparse
import hashlib
from pathlib import Path
from typing import Tuple, Optional, List

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
except ImportError:
    Credentials = None
    Request = None
    build = None
    HttpError = Exception
    MediaFileUpload = None

from cloud.state_manager import get_state_manager

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def get_authenticated_service():
    if Credentials is None:
        raise ImportError(
            "google-api-python-client or google-auth-oauthlib is not installed in this environment."
        )

    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing YouTube credentials! Ensure YOUTUBE_CLIENT_ID, "
            "YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN are set in environment/secrets."
        )

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds)


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def upload_short(
    video_path,
    title,
    description,
    tags=None,
    category_id="28",
    privacy_status="public",
    run_id: Optional[str] = None
) -> Tuple[str, str]:
    """Uploads MP4 video to YouTube with Gate 5 idempotency checking.

    Returns:
        (video_id, short_url)
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Gate 5: Pre-Upload Idempotency Verification
    state_mgr = get_state_manager()
    video_hash = compute_file_sha256(video_path)

    # 1. Check if video hash was already published
    existing_record = state_mgr.is_video_hash_published(video_hash)
    if existing_record:
        vid_id = existing_record.get("youtube_id", "")
        short_url = existing_record.get("short_url", f"https://www.youtube.com/shorts/{vid_id}")
        print(f"[Gate 5 Idempotency] Video file SHA-256 ({video_hash[:12]}) already published!")
        print(f"[Gate 5 Idempotency] Reusing confirmed YouTube publication: {short_url}")
        return vid_id, short_url

    # 2. Check if run_id was already published
    if run_id and state_mgr.is_run_published(run_id):
        existing_record = state_mgr.publications["records"].get(str(run_id), {})
        vid_id = existing_record.get("youtube_id", "")
        short_url = existing_record.get("short_url", f"https://www.youtube.com/shorts/{vid_id}")
        print(f"[Gate 5 Idempotency] Run ID ({run_id}) already has a confirmed upload record!")
        print(f"[Gate 5 Idempotency] Skipping duplicate API upload: {short_url}")
        return vid_id, short_url

    print(f"Preparing upload for: {video_path.name}")
    print(f"Title: {title}")
    print(f"File size: {video_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"SHA-256: {video_hash[:16]}...")

    youtube = get_authenticated_service()

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or ['shorts', 'science', 'whatif', 'curiosity'],
            'categoryId': str(category_id)
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False,
            'embeddable': True,
            'license': 'youtube'
        }
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype='video/mp4',
        chunksize=1024 * 1024 * 5,  # 5MB chunks
        resumable=True
    )

    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    retry_count = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        except HttpError as e:
            if hasattr(e, 'resp') and e.resp.status in [500, 502, 503, 504] and retry_count < 5:
                retry_count += 1
                wait_time = 2 ** retry_count
                print(f"Transient HTTP {e.resp.status}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

    video_id = response['id']
    short_url = f"https://www.youtube.com/shorts/{video_id}"
    print(f"\nUpload Successful!")
    print(f"Video ID: {video_id}")
    print(f"Shorts URL: {short_url}")

    return video_id, short_url


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Upload YouTube Short")
    parser.add_argument('video', help="Path to MP4 file")
    parser.add_argument('--title', required=True, help="Video title (include #shorts)")
    parser.add_argument('--desc', default="", help="Video description")
    parser.add_argument('--tags', default="shorts,science,curiosity", help="Comma-separated tags")
    parser.add_argument('--category', default="28", help="Category ID (28=Science & Tech, 27=Education)")
    parser.add_argument('--privacy', default="public", choices=['public', 'unlisted', 'private'])
    parser.add_argument('--run-id', default=None, help="Execution run ID for idempotency")

    args = parser.parse_args()
    tags_list = [t.strip() for t in args.tags.split(',') if t.strip()]

    upload_short(
        video_path=args.video,
        title=args.title,
        description=args.desc,
        tags=tags_list,
        category_id=args.category,
        privacy_status=args.privacy,
        run_id=args.run_id
    )
