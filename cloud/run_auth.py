#!/usr/bin/env python3
import sys
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

client_id = "858226116982-hfercg98458gb4oetp7o9f0onq3e007j.apps.googleusercontent.com"
client_secret = "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"

client_config = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost/"]
    }
}

print("=" * 60)
print(" Starting YouTube OAuth Authorization...")
print("=" * 60)

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

# port=0 lets OS choose an available free port, preventing port collisions
creds = flow.run_local_server(port=0, prompt='consent', access_type='offline', open_browser=True)

print("\n" + "=" * 60)
print(" SUCCESSFULLY AUTHORIZED!")
print("=" * 60)
print(f"\nYOUTUBE_CLIENT_ID:\n{client_id}\n")
print(f"YOUTUBE_CLIENT_SECRET:\n{client_secret}\n")
print(f"YOUTUBE_REFRESH_TOKEN:\n{creds.refresh_token}\n")
print("=" * 60)

import json
with open("cloud/youtube_tokens.json", "w") as f:
    json.dump({
        "YOUTUBE_CLIENT_ID": client_id,
        "YOUTUBE_CLIENT_SECRET": client_secret,
        "YOUTUBE_REFRESH_TOKEN": creds.refresh_token
    }, f, indent=2)
print("Saved to cloud/youtube_tokens.json")
