---
name: deploy
description: Deploy Signal Hunter for automated daily digests — local macOS setup with launchd
user_invocable: true
---

# Deploy Signal Hunter

You are setting up automated daily digest delivery with a smooth onboarding flow. Walk the user through these steps one at a time. Be conversational and friendly.

---

## Step 0: Configure Your Sources

Before deploying, help the user customize what they want to track. Start with `config.yaml.example` as a template.

Present each source category one at a time. Show the defaults and ask if they want to keep, modify, or skip each one. Format as a clean checklist.

### Reddit
> **Reddit** — Track trending posts from AI/tech subreddits.
> Defaults: `r/singularity`, `r/AINewsMinute`, `r/aicuriosity`
>
> Want to keep these? Add/remove any? (or type "skip" to disable Reddit)

Wait for answer. Apply changes.

### YouTube
> **YouTube** — Monitor channels for new videos (with transcript summaries).
> Defaults: `@AIDailyBrief`, `@matthew_berman`, `@aiDotEngineer`, `@GregIsenberg`
>
> Want to keep these? Add/remove any? (or "skip")

For any new channels, resolve their `channel_id` using yt-dlp or the YouTube RSS feed.

### X/Twitter
> **X/Twitter** — Track tweets from AI/tech leaders.
> Defaults: 17 handles (nlw, edsim, polynoamial, natolambert, bcherny, mattshumer_, etc.)
>
> Want to keep these? Add/remove any? (or "skip" — requires X API Bearer Token)

If they keep Twitter, check if `X_BEARER_TOKEN` is in `.env`. If not, guide them:
1. Go to https://developer.x.com
2. Create a project → Generate Bearer Token
3. They'll paste it and you add it to `.env`

### App Stores
> **App Stores** — Scrape trending app charts (uses Playwright headless browser).
> Defaults: AppMagic, AppRaven
>
> Keep these? Add others? (or "skip")

### Email Recipients
> **Email Digest** — Where should the daily digest be sent?
> Default: your Gmail address
>
> Add any other recipients? (e.g., team Google Group, personal email)

Check if `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` are in `.env`. If not:
1. Ask for their Gmail address
2. Guide them to create an App Password: Google Account → Security → 2-Step Verification → App Passwords
3. Add both to `.env`

### Scoring Weights (Optional)
> **Scoring** — Want to customize how signals are weighted?
> Defaults: HN ÷10, Reddit ÷5, Twitter ÷2, 1.5x cross-source multiplier
>
> Keep defaults? (most users should — type "keep" or customize)

Only modify if they explicitly want to change weights.

### Write config.yaml
After all sources are configured, write the final `config.yaml` with their choices.

---

## Step 1: Collect & Validate All API Keys

First check `.env` for existing keys, then ask for any missing ones.

Present a single checklist showing status:

> **API Keys needed for your setup:**
>
> | Key | Status | Required for |
> |-----|--------|-------------|
> | `GMAIL_ADDRESS` | {found in .env / missing} | Sending digest emails |
> | `GMAIL_APP_PASSWORD` | {found / missing} | Gmail SMTP auth |
> | `X_BEARER_TOKEN` | {found / missing / skipped} | X/Twitter source |
> | `ANTHROPIC_API_KEY` | {found / missing} | AI analysis (~$0.50/month) |

For each missing key:
1. Show the user where to get it
2. Ask them to paste it
3. Save it to `.env` immediately

---

## Step 2: Local Deployment

### 2a. Verify prerequisites
```bash
cd <project_root> && .venv/bin/python -c "import src.collector; print('OK')"
```
If this fails, tell them to run `/setup` first.

### 2b. Ask for schedule
Ask: "What time should the digest run daily? (default: 10 PM)"

### 2c. Create the local runner
Copy `run_digest.py` from the deployment template into the project root if it doesn't exist. This script:
1. Collects from all sources (webfetch + python scrapers)
2. Scores and detects cross-source signals
3. Analyzes with Claude via Anthropic API
4. Sends email digest

### 2d. Set up launchd (macOS persistent cron)
Create a launchd plist at `~/Library/LaunchAgents/com.signal-hunter.digest.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.signal-hunter.digest</string>
    <key>ProgramArguments</key>
    <array>
        <string>{project_root}/.venv/bin/python</string>
        <string>{project_root}/run_digest.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{project_root}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{project_root}/logs/digest.log</string>
    <key>StandardErrorPath</key>
    <string>{project_root}/logs/digest-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>{project_root}/.venv/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

Load it:
```bash
mkdir -p {project_root}/logs
launchctl load ~/Library/LaunchAgents/com.signal-hunter.digest.plist
```

### 2e. Confirm
Tell the user: "Done! Your digest will run daily at {time}. Check `logs/digest.log` for output. To stop: `launchctl unload ~/Library/LaunchAgents/com.signal-hunter.digest.plist`"
