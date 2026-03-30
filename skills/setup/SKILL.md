---
name: setup
description: Set up the Daily Knowledge Builder — install dependencies, configure sources, and create Obsidian vault structure
user_invocable: true
---

# Setup Daily Knowledge Builder

Walk the user through initial setup.

## Steps

### 1. Install Python Dependencies

```bash
cd <project_root> && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Then install Playwright browser:
```bash
.venv/bin/playwright install chromium
```

### 2. Create Config

Check if `config.yaml` exists. If not, copy from `config.yaml.example`:
```bash
cp config.yaml.example config.yaml
```

Tell the user to customize `config.yaml`:
- Add their Reddit subreddits
- Add their YouTube channels (use `/add-source` to auto-resolve channel IDs)
- Add their X/Twitter handles
- Set their Obsidian vault path under `obsidian.vault_path`

### 3. Set Up API Keys

Create a `.env` file with:
```
X_BEARER_TOKEN=your_x_api_bearer_token_here
```

Tell the user how to get an X API key:
1. Go to https://developer.x.com
2. Create a project and app
3. Generate a Bearer Token
4. Paste it in `.env`

This is optional — the system works without X/Twitter, it just skips that source.

### 4. Set Up Obsidian Vault

Read the vault path from `config.yaml` and create the folder structure:
```bash
mkdir -p {vault_path}/Daily {vault_path}/Ideas {vault_path}/Weekly
```

### 5. Gmail Setup

The Gmail MCP integration requires the Claude Gmail extension to be enabled and authenticated. Tell the user:
- Enable the Gmail plugin in Claude Code settings
- Authorize with their Gmail account when prompted

This is optional — the system works without Gmail, it just skips newsletters.

### 6. Test

Run `/test-source all` to verify everything works.

### 7. Install Global Plugin (Optional — Recommended)

Ask: **"Would you like to use /digest from anywhere in Claude (desktop app, any directory)?"**

If yes, install Signal Hunter as a global Claude plugin:

```bash
# Create plugin directory
mkdir -p ~/.claude/plugins/cache/local/signal-hunter/1.0.0/commands
```

Then write the digest command file to `~/.claude/plugins/cache/local/signal-hunter/1.0.0/commands/digest.md`:

```markdown
---
allowed-tools: Bash(*), Read(*), Write(*), Edit(*), Glob(*), Grep(*), WebFetch(*), mcp__claude_ai_Gmail__gmail_search_messages(*), mcp__claude_ai_Gmail__gmail_read_message(*)
description: Run Signal Hunter daily digest
disable-model-invocation: false
---

# Signal Hunter Daily Digest

Read {project_root}/CLAUDE.md and {project_root}/skills/digest/SKILL.md for full instructions.
Working directory: {project_root}
```

Replace `{project_root}` with the actual path (e.g., `/Users/me/signal-hunter`).

Register in `~/.claude/plugins/installed_plugins.json` by adding to the `plugins` object:

```json
"signal-hunter@local": [
  {
    "scope": "user",
    "installPath": "~/.claude/plugins/cache/local/signal-hunter/1.0.0",
    "version": "1.0.0",
    "installedAt": "{current_iso_date}",
    "lastUpdated": "{current_iso_date}"
  }
]
```

Enable in `~/.claude/settings.json`:

```json
"signal-hunter@local": true
```

Tell the user: **"Done! You can now run /digest from any Claude session — desktop app, terminal, anywhere."**

### 8. Schedule (Optional)

To run daily at 10 AM, the user can either:
- Use Claude Code cron (session-only, 7-day expiry): just run `/digest` and it gets scheduled
- Use macOS launchd for permanent scheduling (provide instructions if asked)