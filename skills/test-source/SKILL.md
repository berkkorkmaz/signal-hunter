---
name: test-source
description: Test a specific source or category to validate scraping works and output is meaningful
user_invocable: true
---

# Test Source

Test one or more sources from the Daily Knowledge Builder to verify they work.

## Input
The user provides either:
- A URL to test directly
- A category name: `reddit`, `youtube`, `twitter`, `webfetch`, `app_stores`, `gmail`, or `all`

Parse from: `$ARGUMENTS`

## Steps

### If a URL is provided:
1. Determine the category from URL pattern
2. Run the appropriate scraper/fetch method
3. Display sample results (first 5 items with titles, URLs, scores)
4. Validate: items have titles, URLs are not empty, content is meaningful

### If a category is provided:
1. Read `config.yaml` from the project root
2. Run all sources in that category via: `.venv/bin/python -m src.collector --test <category>`
3. Display per-source results count and sample items
4. Report any failures

### If "all" is provided:
1. Run the full collector: `.venv/bin/python -m src.collector`
2. Test each WebFetch URL
3. Test Gmail auto-discovery
4. Report a summary table

## Validation Criteria
- Items must have non-empty titles (>5 chars)
- Items must have valid URLs
- At least 1 item per source (except twitter which may fail)

## Output Format
```
Source: {name}
Status: OK / FAILED / PARTIAL
Items: {count}
Sample:
  1. {title} | {url} | score={score}
Validation: PASSED / FAILED ({reason})
```