#!/usr/bin/env python3
"""Backend Server - データ処理 + 意図的なエラー発生"""
import http.server
import json
import time
import random
import logging
from datetime import datetime

PORT = 9002

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [Backend] %(levelname)s %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ダミーデータ
USERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "purchase_count": 10},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "purchase_count": 0},  # バグの原因
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "purchase_count": 5},
]

class BackendHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s %s", self.address_string(), format % args)

    def do_GET(self):
        logger.info(f"Request: {self.path}")

        if self.path == "/users":
            self.handle_users()
        elif self.path.startswith("/users/"):
            self.handle_user_detail()
        elif self.path == "/error":
            self.handle_error()
        elif self.path == "/slow":
            self.handle_slow()
        elif self.path == "/random-fail":
            self.handle_random_fail()
        elif self.path == "/health":
            self.send_json_response({"status": "ok", "service": "backend"})
        else:
            logger.warning(f"Not found: {self.path}")
            self.send_error(404, "Not Found")

    def handle_users(self):
        """ユーザー一覧を返す"""
        logger.info("Fetching users from database...")
        self.send_json_response({"users": USERS, "count": len(USERS)})

    def handle_user_detail(self):
        """ユーザー詳細と割引率を返す"""
        try:
            user_id = int(self.path.split("/")[-1])
            logger.info(f"Fetching user detail for id={user_id}")

            user = next((u for u in USERS if u["id"] == user_id), None)
            if not user:
                logger.warning(f"User not found: id={user_id}")
                self.send_error(404, "User not found")
                return

            logger.info(f"Found user: {user['name']}")
            logger.info(f"Calculating discount rate for user {user['name']}...")

            # バグ: purchase_countが0のユーザーでゼロ除算エラー
            # 割引率 = 100 / purchase_count (購入回数が多いほど割引率が下がる想定)
            discount_rate = 100 / user["purchase_count"]

            logger.info(f"Discount rate calculated: {discount_rate}%")

            response = {
                "user": user,
                "discount_rate": discount_rate,
                "message": f"{user['name']}の割引率は{discount_rate}%です"
            }
            self.send_json_response(response)

        except ZeroDivisionError as e:
            logger.error(f"ZeroDivisionError: Cannot calculate discount for user {user['name']}")
            logger.error(f"  user_id={user_id}, purchase_count={user['purchase_count']}")
            logger.error(f"  Fix: Add check for purchase_count == 0 in handle_user_detail()")
            self.send_error(500, f"Internal Server Error: Division by zero for user {user_id}")
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            self.send_error(500, str(e))

    def handle_error(self):
        """意図的に500エラーを発生"""
        logger.error("Database connection failed!")
        logger.error("Traceback: ConnectionRefusedError: [Errno 111] Connection refused")
        logger.error("Failed to execute query: SELECT * FROM users")
        self.send_error(500, "Internal Server Error - Database connection failed")

    def handle_slow(self):
        """遅いレスポンス（タイムアウトのシミュレーション）"""
        delay = random.uniform(3, 6)
        logger.warning(f"Slow query detected, estimated time: {delay:.1f}s")
        logger.info("Executing heavy database query...")
        time.sleep(delay)
        logger.info("Query completed")
        self.send_json_response({"message": "Slow response", "delay": delay})

    def handle_random_fail(self):
        """ランダムに失敗"""
        if random.random() < 0.5:
            logger.error("Random failure occurred!")
            self.send_error(500, "Random failure")
        else:
            logger.info("Request succeeded")
            self.send_json_response({"status": "success"})

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), BackendHandler)
    logger.info(f"Backend server starting on port {PORT}")
    server.serve_forever()
