# Autonomous YouTube Shorts Cloud Pipeline

A 100% autonomous, serverless cloud pipeline that generates, animates, renders, and publishes faceless YouTube Shorts on a daily schedule using **GitHub Actions**.

Runs completely in the cloud — **even when your computer is turned off, asleep, or offline**.

---

## ⚡ How It Works

1. **Schedule**: Triggers twice daily via GitHub Actions:
   - **8:00 AM PKT** (03:00 UTC)
   - **8:10 PM PKT** (15:10 UTC)
   - *Can also be triggered manually anytime via the "Run workflow" button.*
2. **Topic & Script**: Researches trending viral curiosity topics (science, human body, space, survival). Never repeats a topic already logged in `_published.md`.
3. **Calm Explanation Voice**: Synthesizes speech using Kokoro ONNX at 0.88x speed with natural pauses.
4. **Whisper Subtitles**: Aligns word-by-word animated captions with OpenAI Whisper (`small.en`).
5. **Headless 3D Render**: Renders Three.js 3D animations at 1080x1920 (30 fps) in headless Chrome with software GPU acceleration.
6. **YouTube Publishing**: Uploads directly to YouTube via YouTube Data API v3 as a public Short.
7. **Cloud Backup & Logging**: Retains every rendered MP4 in GitHub Actions artifacts for 30 days and logs the video title & link to `_published.md`.

---

## 🚀 Setup Instructions (One-time, ~3 minutes)

### Step 1: Push This Repository to GitHub
If you haven't pushed this folder to GitHub yet:
1. Create a new repository on [GitHub](https://github.com/new) (e.g. `youtube-shorts-bot`, private or public).
2. Link and push your code:
```bash
git add .
git commit -m "feat: initial autonomous shorts cloud setup"
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
git branch -M master
git push -u origin master
```

---

### Step 2: Generate Your YouTube Token
To allow GitHub Actions to upload to your YouTube channel without asking for permission every day, run this one-time helper script on your computer:

```bash
python cloud/get_youtube_token.py
```

The script will:
- Prompt for your Google Cloud Client ID and Secret (or guide you to create one in 60 seconds).
- Open your browser to authorize your YouTube channel.
- Output your **Refresh Token**.

---

### Step 3: Add Secrets to GitHub
Go to your GitHub repository:
1. Click **Settings** &rarr; **Secrets and variables** &rarr; **Actions**.
2. Click **New repository secret** and add:

| Secret Name | Description |
|---|---|
| `YOUTUBE_CLIENT_ID` | Your Google OAuth Client ID |
| `YOUTUBE_CLIENT_SECRET` | Your Google OAuth Client Secret |
| `YOUTUBE_REFRESH_TOKEN` | The token generated from Step 2 |
| `GEMINI_API_KEY` *(Optional)* | Google AI Studio key for infinite dynamic topics |

---

## 🎮 Manual Trigger
You can test the workflow anytime without waiting for the schedule:
1. Go to the **Actions** tab on your GitHub repository.
2. Select **Autonomous Daily YouTube Shorts** on the left.
3. Click **Run workflow** &rarr; **Run workflow**.

---

## 📁 Repository Structure
- `.github/workflows/daily-shorts.yml`: GitHub Actions cron & execution workflow.
- `cloud/cloud_runner.py`: Cloud orchestration engine (topic selection, script generation, audio mix, render).
- `cloud/upload_youtube.py`: YouTube Data API v3 resumable uploader.
- `cloud/get_youtube_token.py`: One-time local OAuth token helper.
- `faceless-shorts/`: 3D visual styles, Three.js shaders, Kokoro TTS, and Whisper alignment scripts.
- `_published.md`: Master log of all published Shorts.
