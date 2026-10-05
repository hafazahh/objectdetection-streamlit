/**
 * vision.choirulhaq.com — Cloudflare Worker
 *
 * Serves the Streamlit ANPR app at the custom domain.
 *
 * WHY THIS IS A WRAPPER, NOT A REVERSE PROXY:
 * Streamlit Community Cloud validates the `redirect_uri` of its session
 * bootstrap (share.streamlit.io/-/auth/app) and only accepts its own
 * *.streamlit.app origin. A pure reverse proxy therefore cannot work: the
 * browser is bounced out to the raw origin and leaves the custom domain
 * (and rewriting redirect_uri makes the endpoint answer `{}` instead of 303).
 *
 * The supported workaround (Streamlit docs + community forum) is to embed
 * the app with `?embed=true`, which skips the auth redirect entirely and
 * returns 200. This Worker serves a full-viewport iframe pointing at the
 * embedded app, so visitors see the app at https://vision.choirulhaq.com
 * while the Streamlit origin stays behind the frame.
 *
 * TRADE-OFFS (accepted for a portfolio demo):
 *  - The browser address bar stays on vision.choirulhaq.com, but the inner
 *    app's own navigation does not update the outer URL.
 *  - Streamlit's deploy/share chrome is hidden in embed mode; the
 *    "Fullscreen" affordance remains.
 *
 * SECURITY HEADERS:
 *  The Content-Security-Policy is deliberately narrow. This page's only job is
 *  to render one iframe, so `default-src 'none'` is used and each capability is
 *  re-enabled explicitly:
 *    - frame-src  -> the Streamlit origin (the only thing we frame)
 *    - style-src  -> 'unsafe-inline' for the inline <style> block below
 *    - img-src    -> data: for the inline SVG favicon
 *  `frame-ancestors 'none'` + `X-Frame-Options: DENY` stop anyone from framing
 *  THIS page. They do not affect the iframe we load ourselves.
 */

const STREAMLIT_ORIGIN =
  "https://objectdetection-app-qoaxopqhhzmjufnhqsfzty.streamlit.app";
const APP_URL = `${STREAMLIT_ORIGIN}/?embed=true`;

const FAVICON =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%236C5CE7'/%3E%3Ctext x='50' y='68' font-size='32' font-family='Arial' font-weight='bold' fill='white' text-anchor='middle'%3EANPR%3C/text%3E%3C/svg%3E";

// default-src 'none' + explicit re-enable. No script-src is declared at all,
// so scripts are blocked outright (default-src 'none' covers it) — this page
// needs no JavaScript.
const CSP = [
  "default-src 'none'",
  `frame-src ${STREAMLIT_ORIGIN}`,
  "style-src 'unsafe-inline'",
  "img-src data:",
  "base-uri 'none'",
  "form-action 'none'",
  "frame-ancestors 'none'",
  "object-src 'none'",
].join("; ");

const SECURITY_HEADERS = {
  "Content-Security-Policy": CSP,
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "X-Frame-Options": "DENY",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  // camera MUST name the embedded origin explicitly.
  // `camera=(self)` only allows the page's OWN origin — the iframe lives on a
  // different origin (*.streamlit.app), so `self` alone blocks the webcam.
  // The allowlist entry is what actually grants camera to the frame; the
  // iframe's allow="camera" attribute is only a request, not a grant.
  "Permissions-Policy": `camera=(self "${STREAMLIT_ORIGIN}"), microphone=(), geolocation=(), payment=()`,
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "same-origin",
};

const PAGE = `<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ANPR — Deteksi Plat Nomor</title>
  <meta name="description" content="Deteksi plat nomor kendaraan (ANPR) dengan Python, OpenCV, dan EasyOCR." />
  <link rel="icon" href="${FAVICON}" />
  <style>
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden;
      background: #0F0E17;
    }
    iframe {
      display: block;
      width: 100vw;
      height: 100vh;
      border: 0;
    }
  </style>
</head>
<body>
  <iframe
    src="${APP_URL}"
    title="ANPR — Deteksi Plat Nomor"
    allow="camera; microphone; clipboard-write; fullscreen"
    referrerpolicy="no-referrer-when-downgrade"
  ></iframe>
</body>
</html>`;

export default {
  async fetch(request) {
    const headers = {
      ...SECURITY_HEADERS,
      "Cache-Control": "public, max-age=300",
    };

    // The iframe loads the Streamlit origin directly, so every request that
    // reaches this host is a page view: render the wrapper.
    if (request.method === "HEAD") {
      return new Response(null, {
        status: 200,
        headers: { ...headers, "Content-Type": "text/html; charset=utf-8" },
      });
    }

    return new Response(PAGE, {
      status: 200,
      headers: { ...headers, "Content-Type": "text/html; charset=utf-8" },
    });
  },
};
