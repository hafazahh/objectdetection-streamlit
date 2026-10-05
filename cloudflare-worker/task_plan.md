# Cloudflare Worker Reverse Proxy — Streamlit Custom Domain

## Goal
Serve Streamlit app (https://objectdetection-streamlit.streamlit.app) at custom domain https://vision.choirulhaq.com via Cloudflare Worker reverse proxy.

## Why
Streamlit Community Cloud free tier does NOT support custom domains. Cloudflare Worker can reverse-proxy HTTP + WebSocket.

## Technical Challenge
Streamlit uses WebSocket at `/_stcore/stream` for runtime. Plain HTTP proxy loads shell but app hangs on "Connecting...". Worker MUST:
1. Proxy HTTP requests to origin, rewrite Host header
2. Proxy WebSocket requests (/_stcore/stream) with Upgrade header preserved
3. Strip/rewrite X-Frame-Options, CSP headers that block embedding
4. Handle Set-Cookie domain rewriting if needed

## Phases

### Phase 1: Design (Lead Engineer)
- [x] Research Cloudflare Worker WebSocket support
- [x] Design proxy architecture
- [x] Define worker.js structure

### Phase 2: Implementation (OpenCode)
- [x] worker.js — full Worker script with WS support
- [x] wrangler.toml — config with route vision.choirulhaq.com/*
- [x] Deployment instructions
- [x] Fix share.streamlit.io redirect_uri rewrite in rewriteResponseHeaders()

### Phase 3: Programmer Review
- [x] Review worker.js for bugs, security, edge cases
- [x] Verify WebSocket handling correctness
- [x] Check header rewriting logic

### Phase 4: Report
- [x] Verify worker.js syntax (node --check)
- [x] Report deployment steps
- [x] Note DNS CNAME recommendation

## Key Design Decisions

### WebSocket Handling
Cloudflare Workers support WebSocket via `fetch()` with `Upgrade` header passthrough. When request has `Upgrade: websocket`, Worker creates a WebSocket pair and proxies to origin.

### Header Rewriting
- Strip `X-Frame-Options` (prevents embedding)
- Strip `Content-Security-Policy` frame-ancestors (prevents embedding)
- Rewrite `Set-Cookie` domain attribute to `.choirulhaq.com`
- Rewrite `Location` header to use custom domain

### DNS
- CNAME `vision` -> `objectdetection-streamlit.streamlit.app` is NOT needed for Worker routes
- Worker routes with custom domain use Cloudflare's own routing (no DNS CNAME needed)
- Recommendation: Remove CNAME, use Worker route instead

## Acceptance Criteria
- [ ] worker.js handles HTTP proxy correctly
- [ ] worker.js handles WebSocket upgrade correctly
- [ ] Headers rewritten (X-Frame-Options, CSP, Set-Cookie, Location)
- [ ] wrangler.toml configured for vision.choirulhaq.com
- [ ] Deployment instructions clear and complete
- [ ] worker.js passes syntax check

## Status
- [x] Phase 1: Design
- [x] Phase 2: Implementation
- [x] Phase 3: Programmer Review
- [x] Phase 4: Report

## Fix: share.streamlit.io redirect_uri rewrite (2026-10-05)

### Problem
Auth flow escaped custom domain. Browser ended on raw origin instead of vision.choirulhaq.com.

### Root Cause
rewriteResponseHeaders() only rewrote Location when it started with origin host. Did NOT rewrite redirect_uri query param inside share.streamlit.io/-/auth/app Location.

### Fix
Added URL parsing for share.streamlit.io Locations — extract redirect_uri param, rewrite to PUBLIC_ORIGIN + pathname + search. Existing origin-prefix rewrites kept after.

### Verification
- node --check: OK
- Logic test: redirect_uri correctly rewritten from raw origin to vision.choirulhaq.com
- Set-Cookie Domain=.choirulhaq.com: correct, no change needed
