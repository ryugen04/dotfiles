#!/usr/bin/env python3
"""キー入力を可視化するスクリプト"""
import sys
import tty
import termios
import select

# ANSI色
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RESET = "\033[0m"

def raw_print(msg):
    """rawモードでも正しく改行する"""
    sys.stdout.write(msg + "\r\n")
    sys.stdout.flush()

def get_key():
    """キー入力を取得して表示"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        raw_print(f"\r\n{CYAN}キーを押してください (Ctrl+C で終了):{RESET}")
        raw_print("")

        while True:
            ch = sys.stdin.read(1)
            if ch == '\x03':  # Ctrl+C
                break

            # 受信したバイト列を表示
            byte_val = ord(ch)
            hex_val = hex(byte_val)

            # 制御文字の判定
            if byte_val < 32:
                if byte_val == 9:
                    key_name = "Tab (または Ctrl+I) ← 区別不可!"
                elif byte_val == 13:
                    key_name = "Enter (または Ctrl+M) ← 区別不可!"
                elif byte_val == 27:
                    key_name = "Escape (または Ctrl+[) ← 区別不可!"
                else:
                    key_name = f"Ctrl+{chr(byte_val + 64)}"
            elif byte_val == 127:
                key_name = "Backspace (または Ctrl+?)"
            else:
                key_name = repr(ch)

            raw_print(f"  {GREEN}受信{RESET}: {hex_val} ({byte_val:3d}) → {YELLOW}{key_name}{RESET}")

            # エスケープシーケンスの読み取り
            if byte_val == 27:
                # 追加の文字があるか確認
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    seq = ""
                    while select.select([sys.stdin], [], [], 0.01)[0]:
                        seq += sys.stdin.read(1)
                    if seq:
                        raw_print(f"  {GREEN}シーケンス{RESET}: ESC + {repr(seq)}")

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{CYAN}  キー入力可視化デモ{RESET}")
    print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print()
    print("従来のターミナルでは、以下の入力を区別できません:")
    print(f"  - Ctrl+I と Tab → 両方とも {YELLOW}0x09{RESET}")
    print(f"  - Ctrl+M と Enter → 両方とも {YELLOW}0x0d{RESET}")
    print(f"  - Ctrl+[ と Escape → 両方とも {YELLOW}0x1b{RESET}")
    print()
    print("kitty Keyboard Protocol はこれを解決します。")
    print()
    get_key()
    print(f"\n{GREEN}終了{RESET}\n")
