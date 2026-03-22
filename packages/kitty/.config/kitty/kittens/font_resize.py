#!/usr/bin/env python3
"""フォントサイズをインタラクティブに変更するkitten

start_resizing_windowのフォントサイズ版。
オーバーレイを開き、キー操作でリアルタイムにサイズ変更する。
"""

import os
import subprocess
import sys
import termios
import tty
from typing import List


def _get_socket() -> str:
    """kittyソケットパスを取得"""
    listen_on = os.environ.get("KITTY_LISTEN_ON", "")
    if listen_on:
        return listen_on
    pid = os.environ.get("KITTY_PID", "")
    return f"unix:/tmp/kitty-socket-{pid}"


def _set_font_size(socket: str, delta: str) -> None:
    """kitty remote controlでフォントサイズを変更"""
    subprocess.run(
        ["kitten", "@", "--to", socket, "set-font-size", "--", delta],
        capture_output=True,
    )


def main(args: List[str]) -> str:
    socket = _get_socket()

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write("  Font Resize Mode\r\n")
        sys.stdout.write("  ----------------\r\n")
        sys.stdout.write("  +/k : larger\r\n")
        sys.stdout.write("  -/j : smaller\r\n")
        sys.stdout.write("  0   : reset\r\n")
        sys.stdout.write("  q/Esc/Enter : exit\r\n")
        sys.stdout.flush()

        while True:
            ch = sys.stdin.read(1)
            if ch in ("q", "\x1b", "\r"):
                break
            elif ch in ("+", "=", "k"):
                _set_font_size(socket, "+1")
            elif ch in ("-", "j"):
                _set_font_size(socket, "-1")
            elif ch == "0":
                _set_font_size(socket, "0")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    return ""


def handle_result(
    args: List[str], answer: str, target_window_id: int, boss: object
) -> None:
    pass
