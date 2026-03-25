# Privacy Policy — Signal Hunter

**Last updated:** 2026-03-25

## Overview

Signal Hunter is a Claude Code plugin that runs entirely on your local machine. It does not collect, store, or transmit any personal data to external servers.

## What Data Is Accessed

Signal Hunter accesses the following data sources **on your behalf, from your machine**:

- **Public websites** (HackerNews, GitHub, Reddit, Product Hunt, HuggingFace, etc.) — fetched via standard HTTP requests
- **Gmail** — accessed through the Claude Gmail MCP extension using your own OAuth credentials. Signal Hunter does not store your Gmail credentials or email content outside your local machine.
- **X/Twitter** — accessed via the X API using a Bearer Token you provide in your local `.env` file
- **YouTube** — public RSS feeds and auto-generated transcripts

## What Data Is Stored

All data is stored **locally on your machine only**:

- **`.cache/`** — fetched content organized by date, stored as JSON files on your local filesystem
- **Obsidian vault** — daily digest notes and idea notes written to your local Obsidian vault
- **`config.yaml`** — your source configuration, stored locally and excluded from git

## What Data Is NOT Collected

- No analytics or telemetry
- No data sent to third-party servers
- No user accounts or registration
- No cookies or tracking
- No personal data leaves your machine

## Third-Party Services

Signal Hunter interacts with third-party APIs (Reddit, YouTube, X/Twitter) using their public APIs. Your use of these services is governed by their respective privacy policies. Signal Hunter does not act as an intermediary or store credentials for these services beyond your local `.env` file.

## Contact

For questions about this privacy policy, open an issue at [github.com/berkkorkmaz/signal-hunter](https://github.com/berkkorkmaz/signal-hunter/issues).
