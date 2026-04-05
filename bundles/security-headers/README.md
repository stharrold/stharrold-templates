# security-headers bundle

Ship a Cloudflare Pages `_headers` file with baseline CSP, HSTS,
COOP/COEP, and cache rules. Derived from synavistra's production
setup after six months of iterative review by multiple bots and
two CI-driven failure modes.

## What you get

- `_headers` at the repo root — conservative baseline CSP for every
  page, plus commented-out examples for routes that need relaxed
  rules (e.g. WebGPU + DuckDB-WASM).
- This README with the ~12 gotchas that motivated each rule.

## Apply

```bash
python .tmp/stharrold-templates/scripts/apply_bundle.py \
  .tmp/stharrold-templates . --bundle security-headers
```

`_headers` is a user-owned (skip-on-update) file — the template copies
it on first install and leaves your customizations alone on updates.
Pass `--force` to overwrite.

## File ownership

| File | Ownership | First install | Update | `--force` |
|---|---|---|---|---|
| `_headers` | user-owned (skip) | Copy | Skip + warn | Replace |

---

## Gotchas (distilled from synavistra, 2026)

Each entry is a real failure we hit in production or in CI; most came
from combining Cloudflare Pages `_headers` with in-browser DuckDB-WASM
and ONNX Runtime Web.

### CSP / COOP / COEP

1. **`default-src 'self'` on `/*` is non-negotiable.** A missing baseline
   CSP (even briefly during a refactor) triggers every static-analysis
   reviewer as a critical regression. Keep it present even when you're
   overriding it elsewhere.

2. **`frame-ancestors 'none'` goes in the CSP, NOT `X-Frame-Options`.**
   Both are shipped in the baseline. `X-Frame-Options: DENY` is the
   legacy header; `frame-ancestors 'none'` is the CSP-era equivalent.
   Modern browsers use CSP; older browsers fall back to X-Frame-Options.

3. **COOP `same-origin` + COEP `credentialless`** are required for
   `SharedArrayBuffer` (DuckDB-WASM, ONNX Runtime Web, Emscripten-based
   libraries). Use `credentialless`, NOT `require-corp` — CDN resources
   lack CORP headers and `require-corp` blocks them silently.

4. **Apply COOP/COEP only on the routes that need it.** Globally applying
   these headers breaks Google Sign-In (the OAuth popup uses
   `window.opener` which COOP blocks). Scope via path patterns like
   `/*/showcases/my-wasm-app*`.

5. **CSP `script-src` governs `importScripts()`**, NOT `worker-src`. If a
   Worker does `importScripts("https://cdn.example.com/foo.js")`, the
   CDN must be in `script-src`. `worker-src` only governs the Worker
   script itself, not things the Worker loads.

6. **Meta CSP + HTTP header CSP = intersection, not union.** When a page
   has both `<meta http-equiv="Content-Security-Policy">` and an HTTP
   header, the browser enforces the intersection (most restrictive
   combination). Both must agree on every directive.

7. **`wasm-unsafe-eval` is needed for `WebAssembly.instantiate()`;
   `unsafe-eval` is ALSO needed for Emscripten-compiled WASM workers**
   that use dynamic code generation for ASM_CONSTS (DuckDB-WASM does
   this). You need BOTH, not just one.

8. **`'unsafe-inline'` in `style-src`** is unavoidable for most real
   apps (it's how React/Vue/Eleventy templates inject inline styles).
   Accept it. The alternative is nonces/hashes which break static
   builds.

### Workers / CDN

9. **`crossorigin="anonymous"` is required on external CDN `<script>` tags
   when the page has COEP `require-corp`.** Without it, scripts fail to
   load silently. Under `credentialless` this is optional, which is
   another reason to prefer `credentialless`.

10. **DuckDB-WASM Worker JS + WASM binary cannot be fully vendored**
    due to three upstream constraints: (a) WASM > 25 MB Workers asset
    limit, (b) Emscripten dynamic code in the Worker, (c) COEP blocks
    cross-origin Worker fetches. Current workaround: vendor the JS
    module locally, load the Worker JS via a Blob URL wrapper, pull
    the WASM binary from jsdelivr CDN. The CSP must allow
    `cdn.jsdelivr.net` in `script-src`, `connect-src`, and `worker-src`.

### Cloudflare Pages `_headers` syntax

11. **Path patterns support wildcards**: `/*/showcases/my-app*` matches
    `/en/showcases/my-app/`, `/de/showcases/my-app`, and trailing-slash
    variants. Use this to collapse duplicate entries for i18n routes.

12. **Eleventy passthrough copy**: if your site is built by Eleventy,
    add `addPassthroughCopy("_headers")` in `eleventy.config.js` or
    the file won't make it into `_site/`.

---

## Testing your CSP

After customizing `_headers`, verify with:

```bash
# Local: serve _site/ and check with curl
python3 -m http.server 3000 --directory _site
curl -sI http://localhost:3000/ | grep -i security

# Deployed: check Cloudflare serving the right headers
curl -sI https://your-site.pages.dev/ | grep -i -E "security|cross-origin|content-security"
```

Cloudflare's own CSP testing tool and CSP Evaluator
(csp-evaluator.withgoogle.com) will flag anything egregious.

## See also

- [`BUNDLES.md`](../../BUNDLES.md) — bundle catalog and file ownership rules
- synavistra commit `9176244` — the PR that landed 12 of these gotchas
  in one session of review-bot responses
- Content Security Policy Level 3 spec: https://www.w3.org/TR/CSP3/
- Cloudflare Pages `_headers` docs: https://developers.cloudflare.com/pages/configuration/headers/
