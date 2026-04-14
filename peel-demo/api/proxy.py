"""Vercel serverless function: CORS proxy for the Hack Club sticker CDN.

The CDN sometimes returns `Access-Control-Allow-Origin: *` twice, which
browsers reject as invalid. This refetches the asset server-side and
re-emits clean CORS headers so the peel-demo can load textures.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
ALLOWED_PREFIXES = (
    "https://cdn.hackclub.com/",
    "https://user-cdn.hackclub-assets.com/",
)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        target = qs.get("url", [None])[0]
        if not target:
            self.send_error(400, "missing ?url=")
            return
        target = unquote(target)
        if not any(target.startswith(p) for p in ALLOWED_PREFIXES):
            self.send_error(403, "refusing to proxy non-hackclub host")
            return
        try:
            req = urllib.request.Request(target, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
                ct = r.headers.get("Content-Type", "application/octet-stream")
        except Exception as exc:
            self.send_error(502, f"upstream error: {exc}")
            return
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=86400, immutable")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
