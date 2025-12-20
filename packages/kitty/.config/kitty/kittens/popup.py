#!/usr/bin/env python3
"""
popup.py - Popup window emulator kitten for kitty terminal

Usage in kitty.conf:
    map ctrl+a>g kitten kittens/popup.py lazygit
    map ctrl+a>h kitten kittens/popup.py htop

Environment variables:
    KITTY_POPUP_RATIO  - Size ratio (default: 0.8)
    KITTY_POPUP_OPACITY - Background opacity (default: 0.95)
"""

import os
import subprocess
import json
import platform
from typing import List, Optional, Tuple


def main(args: List[str]) -> str:
    return ""


def get_geometry_x11() -> Optional[Tuple[int, int, int, int]]:
    """Get active window geometry on X11 using xdotool."""
    try:
        # アクティブウィンドウの位置を直接取得
        result = subprocess.run(
            ['xdotool', 'getactivewindow', 'getwindowgeometry', '--shell'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            geo = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    geo[key] = int(value)

            if all(k in geo for k in ['X', 'Y', 'WIDTH', 'HEIGHT']):
                return (geo['X'], geo['Y'], geo['WIDTH'], geo['HEIGHT'])
    except Exception:
        pass
    return None


def get_geometry_macos() -> Optional[Tuple[int, int, int, int]]:
    """Get kitty window geometry on macOS using AppleScript."""
    try:
        script = '''
        tell application "System Events"
            if (name of processes) contains "kitty" then
                tell process "kitty"
                    if (count of windows) > 0 then
                        set frontWindow to window 1
                        set winPos to position of frontWindow
                        set winSize to size of frontWindow
                        return (item 1 of winPos as text) & " " & (item 2 of winPos as text) & " " & (item 1 of winSize as text) & " " & (item 2 of winSize as text)
                    end if
                end tell
            end if
            return ""
        end tell
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split()
            if len(parts) == 4:
                return tuple(int(float(p)) for p in parts)
    except Exception:
        pass
    return None


def get_geometry_hyprland() -> Optional[Tuple[int, int, int, int]]:
    """Get kitty window geometry on Hyprland."""
    try:
        result = subprocess.run(
            ['hyprctl', 'activewindow', '-j'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('class') == 'kitty':
                at = data.get('at', [0, 0])
                size = data.get('size', [800, 600])
                return (at[0], at[1], size[0], size[1])
    except Exception:
        pass
    return None


def get_window_geometry() -> Optional[Tuple[int, int, int, int]]:
    """Get window geometry based on environment."""
    system = platform.system()

    if system == 'Darwin':
        return get_geometry_macos()
    elif os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return get_geometry_hyprland()
    elif os.environ.get('DISPLAY'):
        return get_geometry_x11()

    return None


def calculate_popup_geometry(
    x: int, y: int, width: int, height: int,
    ratio: float = 0.8
) -> Tuple[int, int, int, int]:
    """Calculate popup position and size centered within parent."""
    popup_width = int(width * ratio)
    popup_height = int(height * ratio)
    popup_x = x + (width - popup_width) // 2
    popup_y = y + (height - popup_height) // 2
    return (popup_x, popup_y, popup_width, popup_height)


def handle_result(args: List[str], answer: str, target_window_id: int, boss) -> None:
    """Handle the kitten result - runs inside kitty process."""
    import subprocess
    import shlex

    # args[0]はkitten名、args[1:]がコマンド
    command = args[1:] if len(args) > 1 else [os.environ.get('SHELL', '/bin/sh')]

    opacity = float(os.environ.get('KITTY_POPUP_OPACITY', '0.95'))

    # CWDを取得
    cwd = None
    target_window = boss.window_id_map.get(target_window_id)
    if target_window:
        cwd = target_window.cwd_of_child

    # X11環境かどうか判定（DISPLAY環境変数があり、Wayland系ではない）
    is_x11 = (
        os.environ.get('DISPLAY') and
        not os.environ.get('WAYLAND_DISPLAY') and
        not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') and
        not os.environ.get('SWAYSOCK')
    )

    if is_x11:
        # X11: 別タブで起動（終了時に自動でタブが閉じる）
        launch_args = ['kitten', '@', 'launch', '--type=tab']
        if cwd and os.path.isdir(cwd):
            launch_args.extend(['--cwd', cwd])
        launch_args.extend(command)
        subprocess.Popen(launch_args)
    else:
        # macOS/Wayland: quick-access-terminalでポップアップ
        if cwd and os.path.isdir(cwd):
            cmd_str = ' '.join(shlex.quote(c) for c in command)
            shell_command = ['bash', '-c', f'cd {shlex.quote(cwd)} && {cmd_str}']
        else:
            shell_command = command

        geometry = get_window_geometry()

        if geometry:
            ratio = float(os.environ.get('KITTY_POPUP_RATIO', '0.8'))
            x, y, width, height = geometry
            popup_x, popup_y, popup_width, popup_height = calculate_popup_geometry(
                x, y, width, height, ratio
            )

            cmd_args = [
                'kitten', 'quick-access-terminal',
                '--instance-group', 'lazygit-popup',
                '-o', 'edge=none',
                '-o', f'margin_top={popup_y}',
                '-o', f'margin_left={popup_x}',
                '-o', f'lines={popup_height}px',
                '-o', f'columns={popup_width}px',
                '-o', f'background_opacity={opacity}',
                '-o', 'hide_on_focus_loss=yes',
            ]
        else:
            cmd_args = [
                'kitten', 'quick-access-terminal',
                '--instance-group', 'lazygit-popup',
                '-o', 'edge=center-sized',
                '-o', 'lines=40',
                '-o', 'columns=140',
                '-o', f'background_opacity={opacity}',
                '-o', 'hide_on_focus_loss=yes',
            ]

        cmd_args.extend(shell_command)
        subprocess.Popen(cmd_args)


handle_result.no_ui = True
