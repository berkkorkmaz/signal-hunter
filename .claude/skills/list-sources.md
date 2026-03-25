---
name: list-sources
description: Show all configured sources in the daily knowledge builder grouped by category
user_invocable: true
---

# List Sources

Display all configured sources from the Daily Knowledge Builder.

## Steps

1. Read `config.yaml` from the project root
2. Display sources grouped by category in a formatted table:

```
## WebFetch Sources (Claude fetches directly)
| Name | URL |
|------|-----|

## Reddit (Python: top 10 posts/day per sub)
| Subreddit |
|-----------|

## YouTube (Python: RSS + transcripts)
| Channel | Channel ID |
|---------|------------|

## X/Twitter (Python: X API v2)
| Handle |
|--------|

## App Stores (Python: Playwright)
| Name | URL |
|------|-----|

## Gmail (MCP: auto-discover newsletters)
- Auto-discover: {enabled/disabled}
- Explicit senders: {list}
```

3. Show total count: "**{N} sources configured across {M} categories**"