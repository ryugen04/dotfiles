#!/usr/bin/env python3
"""Frontend Server - 静的ファイル配信 + BFFへのプロキシ"""
import http.server
import json
import urllib.request
import urllib.error
import logging
from datetime import datetime

PORT = 9001
BFF_URL = "http://localhost:9003"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [Frontend] %(levelname)s %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class FrontendHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s %s", self.address_string(), format % args)

    def do_GET(self):
        logger.info(f"Request: {self.path}")

        if self.path == "/":
            self.send_html_response(self.get_index_html())
        elif self.path.startswith("/api/"):
            self.proxy_to_bff()
        elif self.path == "/health":
            self.send_json_response({"status": "ok", "service": "frontend"})
        else:
            self.send_error(404, "Not Found")

    def proxy_to_bff(self):
        """BFFにリクエストを転送"""
        try:
            url = f"{BFF_URL}{self.path}"
            logger.info(f"Proxying to BFF: {url}")
            with urllib.request.urlopen(url, timeout=5) as response:
                data = response.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            logger.error(f"BFF returned error: {e.code}")
            self.send_error(e.code, f"BFF Error: {e.reason}")
        except urllib.error.URLError as e:
            logger.error(f"Failed to connect to BFF: {e.reason}")
            self.send_error(502, "Bad Gateway - BFF unavailable")
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            self.send_error(500, str(e))

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_html_response(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def get_index_html(self):
        return """<!DOCTYPE html>
<html>
<head><title>Demo Frontend</title></head>
<body>
<h1>Demo Frontend</h1>
<p>Endpoints:</p>
<ul>
    <li><a href="/api/users">/api/users</a> - ユーザー一覧</li>
    <li><a href="/api/users/1">/api/users/1</a> - Alice (正常)</li>
    <li><a href="/api/users/2">/api/users/2</a> - Bob (エラー発生!)</li>
    <li><a href="/api/users/3">/api/users/3</a> - Charlie (正常)</li>
</ul>
</body>
</html>"""

if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), FrontendHandler)
    logger.info(f"Frontend server starting on port {PORT}")
    server.serve_forever()
