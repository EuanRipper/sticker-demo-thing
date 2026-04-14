"""Tiny static file server with a /proxy endpoint for the Hack Club CDN.

The CDN sometimes responds with duplicated `Access-Control-Allow-Origin: *`
headers, which modern browsers reject. This proxy refetches the asset and
re-emits clean CORS headers so the peel-demo can load textures.

Run from the peel-demo directory:
    python serve.py 8000
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import urllib.request
import sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/api/proxy", "/proxy"):
            qs = parse_qs(parsed.query)
            target = qs.get("url", [None])[0]
            if not target:
                self.send_error(400, "missing ?url=")
                return
            target = unquote(target)
            if not (target.startswith("https://cdn.hackclub.com/")
                    or target.startswith("https://user-cdn.hackclub-assets.com/")):
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
            self.send_header("Cache-Control", "public, max-age=86400")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def log_message(self, fmt, *args):
        msg = args[0] if args else ""
        if "/proxy" in msg or "/api/proxy" in msg:
            return
        super().log_message(fmt, *args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"serving peel-demo on http://localhost:{port}")
    HTTPServer(("", port), Handler).serve_forever()
