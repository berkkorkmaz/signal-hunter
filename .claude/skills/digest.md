---
name: digest
description: Run the full daily knowledge digest pipeline — collect from all sources, synthesize trends with scoring and velocity tracking, write Obsidian notes
user_invocable: true
---

# Daily Knowledge Digest

You are running the Daily Knowledge Builder pipeline. First, determine the project root (where `config.yaml` lives) and read `config.yaml` to get all settings.

## Step 1: Collect Data

### 1a. Run Python Collector
```bash
cd <project_root> && .venv/bin/python -m src.collector
```
This fetches Reddit, YouTube (with transcripts), X/Twitter, and app store data. Uses daily cache — re-runs are free.

### 1b. Run Scoring Engine
```bash
cd <project_root> && .venv/bin/python -m src.scoring
```
This outputs velocity data (🔥 accelerating, 🆕 new, 📉 fading, ➡️ steady) and topic tracking across days.

## Step 2: Fetch Web Sources via WebFetch

Read `config.yaml` → `sources.webfetch`. For each URL, use WebFetch to extract:
- Titles, URLs, scores/points, descriptions
- Fetch in parallel where possible

## Step 3: Fetch Email Newsletters via Gmail MCP

Check `config.yaml` → `sources.gmail`. If `auto_discover: true`:
```
gmail_search_messages with q: "unsubscribe" newer_than:1d category:updates
```

For each newsletter (filter out promotional/transactional emails):
- Read with `gmail_read_message`
- Extract key AI/tech/business content
- **IMPORTANT**: Note which topics/projects are mentioned in newsletters — newsletter mentions are a strong curation signal for trend scoring

## Step 4: Read Historical Notes (velocity context)

Read the Obsidian vault path from `config.yaml` → `obsidian.vault_path`.
Read the **last 7 daily notes** from `{vault_path}/{daily_folder}/` (not just yesterday).
This gives you historical context to identify:
- What topics are NEW today vs continuing
- What is accelerating vs fading
- What you predicted last week that came true

## Step 5: Synthesize & Analyze

### 5a) Cross-Source Trend Detection with Scoring
Find topics appearing in **2+ different sources**. Use the scoring output from Step 1b and these rules:

**Score calculation (0-100):**
- Base score from engagement (HN points, Reddit upvotes, GitHub stars, tweet likes)
- **1.5x multiplier** if topic appears in 2+ source categories
- **+15 bonus** if topic is also mentioned in a newsletter (newsletters are human-curated, strong signal)
- Use velocity data: 🔥 accelerating, 🆕 new, 📉 fading, ➡️ steady

**Rank all trending topics by their final score.**

### 5b) Business Idea Extraction
For the **top signals with score >= 70**, generate up to **3 business ideas**. Each idea MUST target a different market category:
- **App ideas** (mobile/web)
- **SaaS opportunities**
- **BaaS (Backend as a Service)** plays
- **Gaming applications**
- **Developer tools**

If fewer than 3 signals qualify, create as many as do. Never create two ideas in the same category.

### 5c) App Store Gap Detection
For each trending topic with score >= 60:
1. Extract 2-3 keywords from the topic
2. Search the collected app_stores data for items whose titles contain those keywords
3. If **no matching apps found** → flag as **"🟢 GAP DETECTED — no existing app/tool"**
4. If **matching apps found** → note as **"🔴 Existing: {app names}"**
5. Gaps are stronger signals for new product opportunities — mention this in the business idea

### 5d) Transcript Summarization
For each YouTube video that has a transcript (`raw_text`):
1. Summarize to exactly **5 bullet points**
2. Extract the **single most quotable statement** as a key quote
3. List any product announcements, releases, or actionable insights
4. **Do NOT dump raw transcript** into the daily note — only the summary

### 5e) Executive Summary
Write 3-5 sentences covering the day's most important developments. Mention the strongest signal and its velocity.

## Step 6: Write Obsidian Daily Note

Write to: `{vault_path}/{daily_folder}/{today_date}.md`

```markdown
---
date: {today_date}
type: daily-digest
tags: [daily-digest, {top_tags}]
sources_ok: [{list}]
sources_failed: [{list}]
---

# Daily Knowledge Digest — {today_date}

## Executive Summary
{3-5 sentences, mention strongest signal + velocity}

## Trending Topics (Cross-Source Signals)

### {velocity_emoji} {topic_name}
- **Score**: {score}/100
- **Velocity**: {velocity_label} (first seen: {date}, {days_active} days active)
- **Seen in**: {source1}, {source2}, {source3}...
- **Sources**: [{source1_title}]({url1}), [{source2_title}]({url2}), ...
- **Newsletter mentions**: {newsletter_names or "none"}
- **App Store Gap**: {🟢 GAP DETECTED | 🔴 Existing: app names}
- **Summary**: {what's happening}
- **Why it matters**: {analysis}
- **Business angle**: {opportunity if any}

## Business Ideas & Opportunities

### {idea_title}
- **Category**: app / saas / baas / gaming / dev-tools
- **Inspired by**: [[{today_date}#{topic_name}]] | [{source_title}]({url})
- **Market gap**: {what's missing}
- **App store gap**: {gap analysis result}
- **Difficulty**: low / medium / high
- **Next step**: {what to do first}

---

## Source Details

### HackerNews (Top 20)
{numbered list: [title](url) — {points} pts | {comments} comments}

### Product Hunt (Top 10)
{**name** — tagline — {upvotes} upvotes}

### GitHub Trending (Top 15)
{[owner/repo](url) — {stars} stars today — {description}}

### HuggingFace Papers (Top 10)
{[title](url) — {likes} likes}

### Reddit (Top 10/day per sub)
{[{score} pts] [title](url) — r/{subreddit}}

### YouTube (Last 48h)
For each video with transcript, show the 5-bullet summary:
{**[title](url)** — {channel}}
{> "Key quote from transcript"}
{- Bullet point 1}
{- Bullet point 2...}

### X/Twitter (Last 48h)
{[@handle] "{tweet text}" — {likes} likes — [link](url)}

### Email Newsletters
{#### {sender} — "{subject}"}
{Key takeaways as bullet points}

### smol.ai News
{headlines and summaries}

### App Charts
{app name — category}

---

## Source Status
| Source | Status | Items |
|--------|--------|-------|
{status table}

---
*Generated by Signal Hunter*
```

## Step 7: Write Idea Notes (up to 3)

For the **top 3 signals with score >= 70**, create separate idea notes at:
`{vault_path}/{ideas_folder}/idea-{today_date}-{slug}.md`

Each must target a **different market category**.

```markdown
---
date: {today_date}
type: idea
category: {app/saas/baas/gaming/dev-tools}
signal_score: {score}
velocity: {emoji} {label}
tags: [idea, {category}, {related_tags}]
---

# {Idea Title}

## The Signal
{What trend/event inspired this, with source links}
- Score: {score}/100 | Velocity: {velocity}
- Seen in: {sources list}
- Newsletter mentions: {names}

## The Opportunity
{Market gap, problem to solve}
- App store gap: {analysis}

## How It Could Work
{Brief product description}

## Difficulty & Next Steps
- **Difficulty**: {low/medium/high}
- **Next step**: {what to do first}
- **Revenue model**: {how it makes money}

## Related
- Daily digest: [[{today_date}]]
- Signal: [[{today_date}#{topic_name}]]
- Sources: [{title1}]({url1}), [{title2}]({url2})
```