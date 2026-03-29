# Daily Knowledge Builder

Automated daily knowledge aggregation from 20+ sources. Detects cross-source trending signals and generates Obsidian notes with business ideas.

## Setup
Run `/setup` to get started, or manually:
1. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. `.venv/bin/playwright install chromium`
3. `cp config.yaml.example config.yaml` — customize your sources
4. Add `X_BEARER_TOKEN=...` to `.env` (optional, for X/Twitter)
5. Set your output path in `config.yaml` (Obsidian vault or any folder)

## Skills
- `/deploy` — **One-command setup**: configure sources and deploy with local launchd automation
- `/digest` — Run full daily pipeline (collect, score, detect trends, write Obsidian notes)
- `/weekly` — Generate weekly trend report (persistent, flash, rising signals)
- `/add-source <url>` — Auto-categorize and add a new source
- `/test-source <url_or_category>` — Test a scraper and validate output
- `/list-sources` — Show all configured sources
- `/setup` — Guided first-time setup

## Quick Commands
- Run collector: `.venv/bin/python -m src.collector`
- Run scoring: `.venv/bin/python -m src.scoring` (daily velocity)
- Run weekly scoring: `.venv/bin/python -m src.scoring --weekly`
- Test one category: `.venv/bin/python -m src.collector --test reddit` (also: youtube, twitter, app_stores, api_endpoints)
- Force re-fetch (ignore cache): `.venv/bin/python -m src.collector --force`

## Source Tiers
- **Tier 1 (WebFetch)**: HN, ProductHunt, GitHub Trending, HuggingFace, smol.ai, Superhuman AI, Ben's Bites, TechCrunch AI, Futurepedia Innovations — Claude fetches directly
- **Tier 2 (Gmail MCP)**: Newsletters auto-discovered via "unsubscribe" search
- **Tier 3 (Python)**: Reddit (.json API), YouTube (RSS + transcripts), X/Twitter (v2 API), App stores (Playwright)
- **Tier 4 (API Endpoints)**: Futurepedia Tools API — direct JSON endpoints, product-discovery signals

## Key Patterns
- All scrapers use `safe_fetch()` — never crash the pipeline
- `config.yaml` is the single source of truth for all sources and scoring weights
- Daily cache in `.cache/{date}/` avoids re-fetching and preserves history
- Scoring: 0-100 normalized scores, tiered cross-source multiplier (1.3x for 2 sources, 1.5x for 3+), +15 newsletter mention bonus
- Velocity: 🔥 accelerating, 🆕 new, 📉 fading, ➡️ steady (compared across 7 days)
- App store gap detection: auto-check if trending topic has existing apps
- YouTube transcripts: summarized to 5 bullet points (not raw dump)
- Up to 3 idea notes per day for signals scoring >= 70
