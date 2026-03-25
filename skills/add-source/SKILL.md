---
name: add-source
description: Add a new content source to the daily knowledge builder. Auto-categorizes the URL and validates it works.
user_invocable: true
---

# Add Source

The user wants to add a new source URL to the Daily Knowledge Builder.

## Steps

1. **Parse the URL** from the user's input: `$ARGUMENTS`

2. **Auto-categorize** based on URL pattern:
   - `reddit.com/r/` → category: `reddit`, extract subreddit name
   - `youtube.com/@` or `youtube.com/watch` → category: `youtube`, resolve channel ID via yt-dlp
   - `x.com/` or `twitter.com/` → category: `twitter`, extract handle
   - `appmagic.rocks`, `appraven.net` → category: `app_stores` (needs Playwright)
   - `gmail` or email address → category: `gmail`, add to explicit_senders
   - Everything else → category: `webfetch` (try WebFetch first)

3. **Read current config**: Find `config.yaml` in the project root

4. **Check for duplicates**: Don't add if URL/source already exists

5. **Test the source**:
   - For `webfetch`: Use WebFetch to verify content is extractable
   - For `reddit`: Run Python to test `.json` API
   - For `youtube`: Resolve channel ID and test RSS feed
   - For `twitter`: Test via X API
   - For `app_stores`: Run Playwright test

6. **Add to config.yaml** under the correct category

7. **Report results**: Show the user what was added, which category, and sample content from the test

## Important
- If WebFetch fails for a URL, suggest trying it as `app_stores` (Playwright) or `data_sources`
- For YouTube channels, always resolve and store the `channel_id`
- Always validate before adding — don't add broken sources