# Daily Knowledge Builder

> A Claude Code plugin that aggregates content from 15+ sources daily, detects cross-source trending signals, and generates structured Obsidian notes with business ideas.

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
| YouTube | RSS + Transcripts | New videos with full auto-generated transcripts |
| X/Twitter | X API v2 | Latest tweets from accounts you follow |
| Gmail | Gmail MCP | Auto-discovered newsletter content |
| App Stores | Playwright | Trending apps from AppMagic, AppRaven |

Then Claude:
1. **Cross-references** all sources to find topics appearing in 3+ places
2. **Ranks signals** by strength (engagement, novelty, source count)
3. **Generates business ideas** (app, SaaS, BaaS, gaming) from each trend
4. **Writes Obsidian notes** with daily digests and individual idea files
5. **Caches everything** — historical data preserved, same-day re-runs are free

## Install

```bash
# Clone
git clone https://github.com/berkkorkmaz/me-myself-i.git
cd me-myself-i

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
/add-source <url>    # Add a new source (auto-categorized)
/test-source reddit  # Test a category
/list-sources        # Show all configured sources
```

### As a Script

```bash
# Run all scrapers
.venv/bin/python -m src.collector

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
    2026-03-25.md    # Full daily digest
  Ideas/
    idea-2026-03-25-ai-supply-chain-security.md
  Weekly/
    2026-W13.md      # Weekly summary (future)
```

## How Trend Detection Works

The system catches emerging signals like early-stage viral projects by finding topics that appear across **multiple independent sources simultaneously**:

1. **Entity extraction** from all collected items
2. **Cross-source frequency** — topic in HN + Reddit + Newsletter = strong signal
3. **Engagement velocity** — 1000+ GitHub stars in a day, 500+ HN points
4. **Novelty detection** — compares against yesterday's note to highlight what's NEW

## License

MIT
