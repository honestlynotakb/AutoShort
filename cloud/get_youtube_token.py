#!/usr/bin/env python3
"""One-time local helper to obtain a YouTube OAuth 2.0 Refresh Token.
Run this script once on your computer:
    python cloud/get_youtube_token.py
It will open your browser, request permission to upload to your YouTube channel,
and print your YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN
to paste into GitHub Actions Secrets.
"""
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Installing google-auth-oauthlib...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-auth-oauthlib"])
    from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    print("=" * 60)
    print(" YouTube OAuth2 Token Generator for GitHub Actions")
    print("=" * 60)
    print("\nTo upload to YouTube from GitHub Actions, you need an OAuth 2.0 Client ID.")
    print("If you haven't created one yet:")
    print(" 1. Go to https://console.cloud.google.com/apis/credentials")
    print(" 2. Enable 'YouTube Data API v3'")
    print(" 3. Click 'Create Credentials' -> 'OAuth client ID' -> Application type: 'Desktop app'")
    print(" 4. Copy your Client ID and Client Secret below.\n")

    client_id = input("Enter YouTube Client ID: ").strip()
    client_secret = input("Enter YouTube Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Error: Client ID and Secret are required.")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost/"]
        }
    }

    print("\nOpening your browser to authorize your YouTube channel...")
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0, prompt='consent', access_type='offline', open_browser=True)

    print("\n" + "=" * 60)
    print(" SUCCESS! Add these 3 secrets to your GitHub Repository:")
    print(" (Go to GitHub Repo -> Settings -> Secrets and variables -> Actions -> New repository secret)")
    print("=" * 60)
    print(f"\nName:  YOUTUBE_CLIENT_ID\nValue: {client_id}\n")
    print(f"Name:  YOUTUBE_CLIENT_SECRET\nValue: {client_secret}\n")
    print(f"Name:  YOUTUBE_REFRESH_TOKEN\nValue: {creds.refresh_token}\n")
    print("=" * 60)

if __name__ == '__main__':
    main()
