#!/usr/bin/env python3
"""BFF Server - Backend for Frontend, リクエスト集約 + ログ出力"""
import http.server
import json
import urllib.request
import urllib.error
import logging
from datetime import datetime

PORT = 9003
BACKEND_URL = "http://localhost:9002"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [BFF] %(levelname)s %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class BFFHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s %s", self.address_string(), format % args)

    def do_GET(self):
        logger.info(f"Request: {self.path}")

        if self.path == "/api/users":
            self.proxy_to_backend("/users")
        elif self.path.startswith("/api/users/"):
            # /api/users/1 → /users/1
            user_id = self.path.split("/")[-1]
            self.proxy_to_backend(f"/users/{user_id}")
        elif self.path == "/api/error":
            self.proxy_to_backend("/error")
        elif self.path == "/api/slow":
            self.proxy_to_backend("/slow")
        elif self.path == "/api/random-fail":
            self.proxy_to_backend("/random-fail")
        elif self.path == "/health":
            self.send_json_response({"status": "ok", "service": "bff"})
        else:
            logger.warning(f"Unknown API endpoint: {self.path}")
            self.send_error(404, "API endpoint not found")

    def proxy_to_backend(self, path):
        """Backendにリクエストを転送"""
        try:
            url = f"{BACKEND_URL}{path}"
            logger.info(f"Forwarding to Backend: {url}")

            with urllib.request.urlopen(url, timeout=10) as response:
                data = response.read()
                logger.info(f"Backend response: {response.status}")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            logger.error(f"Backend error: {e.code} - {e.reason}")
            logger.error(f"Error details: {error_body}")
            self.send_error(e.code, f"Backend Error: {e.reason}")

        except urllib.error.URLError as e:
            logger.critical(f"Backend unavailable: {e.reason}")
            logger.critical("Circuit breaker: Backend service is down!")
            self.send_error(503, "Service Unavailable - Backend is down")

        except TimeoutError:
            logger.error(f"Backend timeout on {path}")
            logger.warning("Consider increasing timeout or checking Backend health")
            self.send_error(504, "Gateway Timeout")

        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            self.send_error(500, str(e))

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), BFFHandler)
    logger.info(f"BFF server starting on port {PORT}")
    server.serve_forever()
