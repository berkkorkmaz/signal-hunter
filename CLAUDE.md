# Daily Knowledge Builder

Automated daily knowledge aggregation from 15+ sources. Detects cross-source trending signals and generates Obsidian notes with business ideas.

## Setup
Run `/setup` to get started, or manually:
1. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. `.venv/bin/playwright install chromium`
3. `cp config.yaml.example config.yaml` — customize your sources
4. Add `X_BEARER_TOKEN=...` to `.env` (optional, for X/Twitter)
5. Set your Obsidian vault path in `config.yaml`

## Skills
- `/digest` — Run full daily pipeline (collect, synthesize, write Obsidian notes)
- `/add-source <url>` — Auto-categorize and add a new source
- `/test-source <url_or_category>` — Test a scraper and validate output
- `/list-sources` — Show all configured sources
- `/setup` — Guided first-time setup

## Quick Commands
- Run collector: `.venv/bin/python -m src.collector`
- Test one category: `.venv/bin/python -m src.collector --test reddit`
- Force re-fetch (ignore cache): `.venv/bin/python -m src.collector --force`

## Source Tiers
- **Tier 1 (WebFetch)**: HN, ProductHunt, GitHub Trending, HuggingFace, smol.ai — Claude fetches directly
- **Tier 2 (Gmail MCP)**: Newsletters auto-discovered via "unsubscribe" search
- **Tier 3 (Python)**: Reddit (.json API), YouTube (RSS + transcripts), X/Twitter (v2 API), App stores (Playwright)

## Key Patterns
- All scrapers use `safe_fetch()` — never crash the pipeline
- `config.yaml` is the single source of truth for all sources
- Daily cache in `.cache/{date}/` avoids re-fetching and preserves history
- Cross-source trend detection: find topics in 3+ sources, rate signal 1-10
