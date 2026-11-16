#!/usr/bin/env python3
"""One-time local helper to obtain a YouTube OAuth 2.0 Refresh Token.
Run this script once on your computer:
    python cloud/get_youtube_token.py
It will open your browser, request permission to upload to your YouTube channel,
and print your YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN
to paste into GitHub Actions Secrets.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_dotenv():
    """Simple zero-dependency .env loader."""
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

load_dotenv()

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

    env_client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
    env_client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")

    if env_client_id:
        client_id_prompt = f"Enter YouTube Client ID [default: {env_client_id[:12]}...]: "
        entered_id = input(client_id_prompt).strip()
        client_id = entered_id if entered_id else env_client_id
    else:
        client_id = input("Enter YouTube Client ID: ").strip()

    if env_client_secret:
        client_secret_prompt = f"Enter YouTube Client Secret [default: (saved in .env)]: "
        entered_secret = input(client_secret_prompt).strip()
        client_secret = entered_secret if entered_secret else env_client_secret
    else:
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

    try:
        save_env = input("\nSave these to local .env file? [y/N]: ").strip().lower()
        if save_env == 'y':
            env_file = ROOT / ".env"
            existing = {}
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        existing[k.strip()] = v.strip()
            existing["YOUTUBE_CLIENT_ID"] = client_id
            existing["YOUTUBE_CLIENT_SECRET"] = client_secret
            existing["YOUTUBE_REFRESH_TOKEN"] = creds.refresh_token
            out_content = "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n"
            env_file.write_text(out_content, encoding="utf-8")
            print("Successfully updated local .env (safely gitignored).")
    except Exception as e:
        print(f"Notice: Could not update .env: {e}")

if __name__ == '__main__':
    main()
