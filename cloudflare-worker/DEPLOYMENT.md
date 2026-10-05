# Deployment Instructions — vision.choirulhaq.com

## Prerequisites
- Cloudflare account with choirulhaq.com zone active
- Streamlit app live at https://objectdetection-streamlit.streamlit.app

## Option A: Wrangler CLI (Recommended)

### 1. Install wrangler
```bash
npm install -g wrangler
```

### 2. Authenticate
```bash
wrangler login
```
Follow browser prompt to authorize.

### 3. Deploy
```bash
cd /home/choirulhaq/GoogleDrive/AhliPemrograman/objectdetection-streamlit/cloudflare-worker
wrangler deploy
```

### 4. Verify
```bash
curl -I https://vision.choirulhaq.com
```
Expected: 200 OK (or redirect to Streamlit).

---

## Option B: Cloudflare Dashboard (No CLI)

### 1. Open Cloudflare Dashboard
https://dash.cloudflare.com/

### 2. Navigate to Workers & Pages
- Select choirulhaq.com zone
- Click "Workers & Pages" in left sidebar
- Click "Create application" -> "Create Worker"

### 3. Configure Worker
- Name: `vision-proxy`
- Click "Deploy" (creates placeholder)

### 4. Edit Code
- Click "Edit code" button
- Delete default code
- Paste contents of `worker.js`
- Click "Deploy"

### 5. Add Route
- Go to Worker settings -> "Triggers" tab
- Under "Routes", click "Add route"
- Route: `vision.choirulhaq.com/*`
- Zone: `choirulhaq.com`
- Click "Save"

### 6. Verify
```bash
curl -I https://vision.choirulhaq.com
```

---

## DNS Configuration

### Current State
- CNAME `vision` -> `objectdetection-streamlit.streamlit.app` (added by user)

### Recommendation: REMOVE the CNAME
Worker routes with custom domain do NOT need DNS CNAME. Cloudflare routes traffic to the Worker based on the route pattern. The CNAME is unnecessary and may cause confusion.

### Steps to Remove
1. Cloudflare Dashboard -> DNS -> Records
2. Find CNAME record for `vision`
3. Click "Delete"

### What Happens Without CNAME
- DNS query for vision.choirulhaq.com returns Cloudflare IP (from A/AAAA records or CNAME flattening)
- Cloudflare edge matches request to Worker route `vision.choirulhaq.com/*`
- Worker proxies to Streamlit origin

---

## Verification Checklist

After deployment, verify:

- [ ] `curl -I https://vision.choirulhaq.com` returns 200
- [ ] Browser: https://vision.choirulhaq.com loads Streamlit shell
- [ ] Browser: App connects (no "Connecting..." hang)
- [ ] Browser: WebSocket at /_stcore/stream works (check DevTools Network tab)
- [ ] Cookies set on .choirulhaq.com domain
- [ ] No X-Frame-Options or CSP errors in console

---

## Troubleshooting

### App loads but hangs on "Connecting..."
- WebSocket not proxying correctly
- Check Worker logs (Dashboard -> Workers -> vision-proxy -> Logs)
- Verify WebSocketPair code is deployed

### 502 Bad Gateway
- Origin unreachable
- Check Streamlit app is live: https://objectdetection-streamlit.streamlit.app
- Check Worker logs for error details

### Cookies not persisting
- Set-Cookie domain rewrite not working
- Check response headers: `curl -I https://vision.choirulhaq.com | grep -i set-cookie`

### SSL/TLS errors
- Cloudflare SSL mode should be "Full" or "Full (strict)"
- Check: Dashboard -> SSL/TLS -> Overview
