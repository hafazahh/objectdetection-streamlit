# Findings — Cloudflare Worker Reverse Proxy

## Cloudflare Worker WebSocket Support
- Workers support WebSocket via `fetch()` with `Upgrade` header
- When `Upgrade: websocket` present, Worker creates WebSocket pair
- Both client-side and server-side WebSocket objects needed
- `WebSocketPair` class available in Workers runtime

## Streamlit WebSocket Endpoint
- Path: `/_stcore/stream`
- Same host as HTTP (not separate WS server)
- Used for bidirectional communication between browser and Streamlit server
- Without WS proxy, app loads shell but hangs on "Connecting..."

## Header Issues
- `X-Frame-Options: DENY` or `SAMEORIGIN` — blocks embedding in iframe
- `Content-Security-Policy: frame-ancestors 'none'` — blocks embedding
- `Set-Cookie` with `Domain=streamlit.app` — cookies won't be sent to vision.choirulhaq.com
- `Location` header — redirects may point to streamlit.app

## DNS for Worker Routes
- Worker routes with custom domain do NOT need DNS CNAME
- Cloudflare routes traffic to Worker based on route pattern
- CNAME `vision` -> streamlit.app is unnecessary and may cause confusion
- Recommendation: Remove CNAME, use Worker route `vision.choirulhaq.com/*`

## wrangler.toml Configuration
```toml
name = "vision-proxy"
main = "worker.js"
compatibility_date = "2024-01-01"

[routes]
pattern = "vision.choirulhaq.com/*"
zone_name = "choirulhaq.com"
```

## Alternative: Dashboard Deployment
- Can deploy via Cloudflare Dashboard (Workers & Pages -> Create -> Routes)
- No wrangler CLI needed
- Upload worker.js directly or paste code
