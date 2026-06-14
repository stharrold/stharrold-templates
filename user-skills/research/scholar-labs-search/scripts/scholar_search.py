#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""
Google Scholar Labs search over a user-authenticated Chrome (CDP).

This script attaches to a Chrome you launched with --remote-debugging-port
(it does NOT launch or authenticate Chrome itself; Google auth is user-attended).
It supports two modes:

  --read-only            Extract results already on the current Scholar Labs tab.
                         Costs ZERO quota. Use this to re-read a page whose results
                         rendered after an earlier extraction fired too early.

  --query "TEXT"         Start a FRESH session (navigates to the base search URL so
                         the previous query can't contaminate this one), submit TEXT,
                         wait for results to render, then extract. COSTS ONE QUERY of
                         the Scholar Labs daily quota (typically 3/day per account).

Output: JSON on stdout (or to --out FILE): {url, result_count, status, body, sources[]}.
Each source is {title, url}. The script never writes Markdown answer files itself;
the caller decides how to record results (project conventions vary).

Examples:
  uv run python scholar_search.py --read-only
  uv run python scholar_search.py --query "human-in-the-loop validation accuracy of AI-generated SQL"
  uv run python scholar_search.py --query "..." --authuser 1   # second Google account
"""

import argparse
import asyncio
import json
import sys

from playwright.async_api import async_playwright

BASE = "https://scholar.google.com/scholar_labs/search?hl=en"


def base_url(authuser):
    return BASE if authuser is None else f"{BASE}&authuser={authuser}"


async def _find_or_open(ctx, authuser):
    for pg in ctx.pages:
        if "scholar_labs" in pg.url:
            return pg
    pg = await ctx.new_page()
    await pg.goto(base_url(authuser))
    return pg


async def _extract(page):
    """Read-only: pull body text + external source anchors from the current page."""
    body = await page.locator("body").inner_text()

    # The page can show a stale '--query / Found 0 relevant results' sub-block from a
    # prior search ABOVE the real one. Report the LAST 'Found N relevant results'.
    result_count = None
    for line in body.splitlines():
        s = line.strip().lower()
        if "relevant result" in s:
            for tok in s.replace("found", "").split():
                if tok.isdigit():
                    result_count = int(tok)

    status = "ok"
    if "not designed for queries like this" in body.lower():
        status = "bounced"  # rephrase needed (often a compound/comparative question)
    if "sign in" in body.lower() and "scholar labs" not in body.lower():
        status = "needs_auth"

    sources, seen = [], set()
    anchors = page.locator("a")
    for i in range(await anchors.count()):
        try:
            href = await anchors.nth(i).get_attribute("href")
            txt = (await anchors.nth(i).text_content() or "").strip()
        except Exception:
            continue
        if not href or not href.startswith("http") or "google." in href:
            continue
        if len(txt) < 6 or txt.lower().startswith("[pdf]") or txt.lower().startswith("[html]"):
            # the bare "[PDF] domain.com" anchors duplicate the titled ones; skip
            continue
        if href in seen:
            continue
        seen.add(href)
        sources.append({"title": txt, "url": href})

    return {"url": page.url, "result_count": result_count, "status": status, "body": body, "sources": sources}


async def _submit_and_wait(page, query, authuser, timeout_s):
    # Fresh session: navigate to base URL so the previous query cannot contaminate.
    await page.goto(base_url(authuser))
    box = page.locator("#gs_as_i_t, textarea, [role=combobox]").first
    await box.wait_for(timeout=15000)
    await box.fill(query)
    await box.press("Enter")

    # Poll until results render. 'Looking for results...' is the in-progress state.
    waited = 0
    while waited < timeout_s:
        await page.wait_for_timeout(2000)
        waited += 2
        txt = (await page.locator("body").inner_text()).lower()
        if "not designed for queries like this" in txt:
            break
        if "relevant result" in txt and "looking for results" not in txt:
            break


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", help="query text (positional; or use --query)")
    ap.add_argument("--query", dest="query_flag", help="query text")
    ap.add_argument("--read-only", action="store_true", help="extract current page only; spends NO quota")
    ap.add_argument("--authuser", type=int, default=None, help="Google account index for a second account (quota reset)")
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--timeout", type=int, default=60, help="seconds to wait for results")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    a = ap.parse_args()

    query = a.query_flag or a.query
    if not a.read_only and not query:
        print("ERROR: provide a query, or pass --read-only.", file=sys.stderr)
        sys.exit(2)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{a.port}")
        except Exception:
            print(json.dumps({"status": "no_chrome", "hint": f"Launch Chrome with --remote-debugging-port={a.port} and log into Google."}))
            return
        ctx = browser.contexts[0]
        page = await _find_or_open(ctx, a.authuser)
        await page.bring_to_front()

        if not a.read_only:
            await _submit_and_wait(page, query, a.authuser, a.timeout)

        result = await _extract(page)

    payload = json.dumps(result, indent=2)
    if a.out:
        with open(a.out, "w") as f:
            f.write(payload)
        print(f"wrote {a.out} (status={result['status']}, results={result['result_count']}, sources={len(result['sources'])})")
    else:
        print(payload)


if __name__ == "__main__":
    asyncio.run(main())
