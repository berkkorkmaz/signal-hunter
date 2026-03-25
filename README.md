# Signal Hunter

> AI-powered daily trend hunter. Aggregates 15+ sources, scores signals with cross-source detection and newsletter mention tracking, generates Obsidian notes with business ideas. Claude Code plugin.

## What It Does

Every day, it collects from:

| Source | Method | What You Get |
|--------|--------|-------------|
| HackerNews | WebFetch | Top stories with points & comments |
| Product Hunt | WebFetch | Top products with taglines & upvotes |
| GitHub Trending | WebFetch | Trending repos with stars & descriptions |
| HuggingFace | WebFetch | Trending papers with likes |
| smol.ai | WebFetch | AI news summaries |
| Reddit | Python API | Top 10 posts/day per subreddit |
| YouTube | RSS + Transcripts | New videos with summarized transcripts |
| X/Twitter | X API v2 | Latest tweets from accounts you follow |
| Gmail | Gmail MCP | Auto-discovered newsletter content |
| App Stores | Playwright | Trending apps from AppMagic, AppRaven |

Then it:
1. **Scores** every item (0-100 normalized across sources)
2. **Detects cross-source signals** — topics in 2+ sources get 1.5x multiplier
3. **Tracks newsletter mentions** — +15 bonus (human-curated = strong signal)
4. **Tracks velocity** — 🔥 accelerating, 🆕 new, 📉 fading, ➡️ steady (7-day lookback)
5. **Detects app store gaps** — auto-checks if trending topic has existing apps
6. **Summarizes transcripts** — YouTube transcripts → 5 bullet points + key quote
7. **Generates up to 3 business ideas** per day (app, SaaS, BaaS, gaming, dev-tools)
8. **Writes Obsidian notes** with daily digests, idea notes, and weekly rollups
9. **Caches everything** — historical data preserved, same-day re-runs are free

## Install

```bash
# Clone
git clone https://github.com/berkkorkmaz/signal-hunter.git
cd signal-hunter

# Setup
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium

# Configure
cp config.yaml.example config.yaml
# Edit config.yaml with your sources and Obsidian vault path

# Optional: X/Twitter API
echo "X_BEARER_TOKEN=your_token_here" > .env
```

Or just run `/setup` in Claude Code.

## Usage

### As a Claude Code Plugin

```
/digest              # Run the full daily pipeline
/weekly              # Generate weekly trend report
/add-source <url>    # Add a new source (auto-categorized)
/test-source reddit  # Test a category
/list-sources        # Show all configured sources
```

### As a Script

```bash
# Run all scrapers
.venv/bin/python -m src.collector

# Run scoring engine (velocity + normalized scores)
.venv/bin/python -m src.scoring

# Weekly aggregate
.venv/bin/python -m src.scoring --weekly

# Test one category
.venv/bin/python -m src.collector --test reddit

# Force re-fetch (ignore daily cache)
.venv/bin/python -m src.collector --force
```

## Configuration

Copy `config.yaml.example` to `config.yaml` and customize:

```yaml
sources:
  reddit:
    - subreddit: singularity
    - subreddit: AINewsMinute

  youtube:
    - channel: "@AIDailyBrief"
      channel_id: UCKelCK4ZaO6HeEI1KQjqzWA

  twitter:
    - handle: nlw
    - handle: edsim

  # ... see config.yaml.example for all options

scoring:
  weights:
    hackernews: { divisor: 10 }    # 800pts → 80/100
    reddit: { divisor: 5 }         # 500pts → 100/100
    gmail: { default: 70 }         # newsletter mention = strong signal
  cross_source_multiplier: 1.5
  newsletter_mention_bonus: 15     # bonus if topic in newsletters

obsidian:
  vault_path: ~/Documents/obsidian/vault
  daily_folder: Daily
  ideas_folder: Ideas
  weekly_folder: Weekly
```

### X/Twitter API (Optional)

1. Go to [developer.x.com](https://developer.x.com)
2. Create a project → generate a Bearer Token
3. Add to `.env`: `X_BEARER_TOKEN=your_token`

Free tier (1,500 tweets/month) works for a few handles. Basic ($100/month) for more.

### Gmail (Optional)

Requires the Claude Gmail MCP extension. Enable it in Claude Code settings and authorize with your Gmail account.

## Output

Daily notes are written to your Obsidian vault:

```
vault/
  Daily/
    2026-03-25.md    # Full daily digest with scored trends
  Ideas/
    idea-2026-03-25-ai-security.md      # Up to 3 ideas per day
    idea-2026-03-25-agent-monitoring.md
    idea-2026-03-25-task-manager.md
  Weekly/
    2026-W13.md      # Weekly rollup with persistent/flash/rising signals
```

## How Trend Detection Works

The system catches emerging signals early by combining scoring, cross-source detection, and velocity tracking:

1. **Score normalization** (0-100) — each source's raw engagement mapped to a common scale
2. **Cross-source multiplier** (1.5x) — topics in 2+ source categories get boosted
3. **Newsletter mention bonus** (+15) — human-curated newsletters are strong signal amplifiers
4. **Velocity tracking** — compares against 7 days of cached data to detect:
   - 🔥 **Accelerating**: source count doubled vs yesterday
   - 🆕 **New**: first appearance today
   - 📉 **Fading**: declining from peak
   - ➡️ **Steady**: stable presence
5. **App store gap detection** — auto-checks if anyone has already built it
6. **Weekly rollups** — persistent trends (5+ days), flash signals (peaked and faded), rising signals (watch next week)

## License

MIT
