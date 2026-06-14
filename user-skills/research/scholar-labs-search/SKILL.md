---
name: scholar-labs-search
description: >-
  Run academic literature searches on Google Scholar Labs through the user's
  own authenticated Chrome, then extract the papers and citations found. Use
  this whenever the user wants to search Google Scholar, find peer-reviewed
  sources or citations for a claim, answer a research question with the
  literature, or gather academic evidence, even if they don't name "Scholar
  Labs" explicitly. Especially important because Scholar Labs has a strict
  ~3-queries-per-day quota: this skill prevents wasting queries on malformed
  searches and on re-reads that cost nothing. Do NOT use for general web
  search, fetching one known URL, or reading a PDF the user already has.
compatibility: Requires the playwright Python package and a Chromium-based browser the user can authenticate.
---

# Google Scholar Labs search

Scholar Labs is Google's experimental AI-overview search over scholarly papers. It
evaluates ~60-200 results per query and surfaces ~10 with structured summaries, which
makes it excellent for finding peer-reviewed evidence quickly. Two constraints shape how
to use it well:

1. **It is quota-limited** (commonly ~3 queries/day per Google account). A wasted query is
   expensive. Treat every search as scarce.
2. **Authentication is the user's job.** Scholar Labs needs a logged-in Google session, and
   automating Google login is fragile and against the spirit of the user-attended workflow.
   So the human launches and authenticates the browser; this skill drives it afterward.

Because of (1), the golden rule is: **never burn a query you didn't have to.** Re-reads are
free (`--read-only`); only a fresh `--query` costs quota.

## Step 1 - Decide whether Scholar Labs is even the right tool

Reserve the scarce quota for questions that genuinely need *peer-reviewed* citations
(empirical claims, healthcare/clinical evidence, "what does the literature show about X").
For general definitions, vendor docs, news, or background, prefer ordinary web search or a
deep-research tool and save the quota. Tell the user when you're deliberately *not* spending
a Scholar query so they know the plan.

## Step 2 - Have the user launch and authenticate Chrome (user-attended)

Ask the user to run this (in Claude Code they can prefix with `!`), then log into Google in
the window it opens:

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug" &
```

Then: open `https://scholar.google.com/scholar_labs/search?hl=en` in that window and sign in.

Gotchas worth stating up front, because they silently waste the user's time:
- If Chrome is **already running under their normal profile**, macOS routes the
  `--remote-debugging-port` flag to the existing process and ignores it, so port 9222 stays
  empty. Have them **Quit Chrome fully (Cmd-Q)** first. The throwaway `/tmp/chrome-debug`
  profile keeps this separate from their everyday session.
- Confirm the endpoint is live before doing anything else:
  `curl -s http://localhost:9222/json | python3 -c "import sys,json;[print(t['title'],'|',t['url']) for t in json.load(sys.stdin) if t['type']=='page']"`
  You want to see a `Google Scholar` tab on the `scholar_labs/search` URL.

## Step 3 - Install the one dependency

The bundled script attaches over CDP, so no browser download is needed, only the package:

```
uv pip install playwright   # or: pip install playwright
```

## Step 4 - Phrase the query for a retrieval engine

Scholar Labs *retrieves papers*; it does not synthesize opinions. Compound or comparative
questions ("do X reviewers outperform Y; also consider Z?") with semicolons tend to get
**bounced** with "Scholar Labs is currently not designed for queries like this." Rephrase as
a single focused retrieval ask.

**Example 1:**
Input: Empirical evidence that human experts detect and correct LLM errors in text-to-SQL; do reviewers outperform the model alone?
Output: human-in-the-loop validation accuracy of AI-generated SQL queries

**Example 2:**
Input: What's the best way to define workforce agility and is it the same as IT agility or not?
Output: definitions of workforce agility in organizational research

Draft the queries, show them to the user, and get a thumbs-up *before* spending quota.

## Step 5 - Run the search (this spends one query)

Each fresh query starts a clean session automatically (the script navigates to the base
search URL first, so a previous query cannot contaminate this one - a real failure mode of
naive automation that reuses the open box).

```
uv run python ~/.claude/skills/scholar-labs-search/scripts/scholar_search.py --query "your focused query"
```

The script prints JSON: `{url, result_count, status, body, sources[]}`.
- `status: "ok"` with a non-null `result_count` (e.g. 10) means real results.
- `status: "bounced"` means rephrase (Step 4) - this still consumed a query, so pause and
  fix the wording before retrying.
- `status: "needs_auth"` / `"no_chrome"` means go back to Step 2.

Out of quota? The user can sign into a **second Google account** and you re-run with
`--authuser 1` for a fresh allotment.

## Step 6 - The free re-read (use this constantly)

Results render a beat *after* the page first updates. If an extraction looks empty or shows a
stale "Found 0 / not designed for queries like this" block but the browser visibly has
results, **do not re-query**. Re-read the live page for free:

```
uv run python ~/.claude/skills/scholar-labs-search/scripts/scholar_search.py --read-only
```

This is the single most important habit: a "0 results" from the script is often an early-read
artifact, not the truth. Confirm by re-reading before you ever conclude a gap exists.

## Step 7 - Record the results (follow the project's convention)

This skill returns raw findings; recording them is project-specific. If the repo has a
research-provenance system (an answers/ directory of `Research_*.md` files, a questions index,
a rule that every claim traces to a source URL), write the findings there with full citation
metadata and source URLs, and update the index. Otherwise, summarize the `sources[]` with
their URLs for the user. Mark a question as a genuine literature *gap* only after a clean,
non-bounced search returned nothing - never after a bounce or an early-read 0.

## Quick reference

| Need | Command | Quota |
|------|---------|-------|
| Check endpoint | `curl -s http://localhost:9222/json` | free |
| New search | `scholar_search.py --query "..."` | 1 query |
| Re-read current page | `scholar_search.py --read-only` | free |
| Second account | add `--authuser 1` | 1 query (other account) |
