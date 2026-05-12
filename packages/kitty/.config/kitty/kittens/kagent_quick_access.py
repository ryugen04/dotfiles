#!/usr/bin/env python3
"""
Open kagent Agent Lens in kitty quick-access-terminal.

Normal use expects the kagent binary to be installed:
    cargo install --path crates/kagent-cli --locked --force

Override command with:
    KAGENT_QUICK_ACCESS_COMMAND='cargo run -p kagent-cli -- quick-access'
    KAGENT_QUICK_ACCESS_CWD="$HOME/dev/projects/kagent"
"""

import os
import json
import platform
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import List, Optional, Tuple


def main(args: List[str]) -> str:
    return ""


def resolve_command(args: List[str], target_cwd: Optional[str]) -> Tuple[List[str], Optional[str]]:
    if len(args) > 1:
        return args[1:], target_cwd

    configured = os.environ.get("KAGENT_QUICK_ACCESS_COMMAND")
    configured_cwd = os.environ.get("KAGENT_QUICK_ACCESS_CWD")
    if configured:
        return shlex.split(configured), configured_cwd or target_cwd

    if shutil.which("kagent"):
        return ["kagent", "quick-access"], target_cwd

    cargo_kagent = Path.home() / ".cargo/bin/kagent"
    if cargo_kagent.exists():
        return [str(cargo_kagent), "quick-access"], target_cwd

    dev_root = Path.home() / "dev/projects/kagent"
    if (dev_root / "Cargo.toml").exists():
        return ["cargo", "run", "-p", "kagent-cli", "--", "quick-access"], str(dev_root)

    return [
        "bash",
        "-lc",
        "printf 'kagent was not found in PATH. Set KAGENT_QUICK_ACCESS_COMMAND.\\n'; read -n 1 -s -r -p 'Press any key to close...'",
    ], target_cwd


def get_window_geometry() -> Optional[Tuple[int, int, int, int]]:
    system = platform.system()

    if system == "Darwin":
        return get_geometry_macos()
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return get_geometry_hyprland()
    if os.environ.get("DISPLAY"):
        return get_geometry_x11()

    return None


def get_geometry_x11() -> Optional[Tuple[int, int, int, int]]:
    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowgeometry", "--shell"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        geo = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                geo[key] = int(value)

        if all(key in geo for key in ["X", "Y", "WIDTH", "HEIGHT"]):
            return (geo["X"], geo["Y"], geo["WIDTH"], geo["HEIGHT"])
    except Exception:
        return None

    return None


def get_geometry_macos() -> Optional[Tuple[int, int, int, int]]:
    try:
        script = """
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
        """
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split()
            if len(parts) == 4:
                return tuple(int(float(part)) for part in parts)
    except Exception:
        return None

    return None


def get_geometry_hyprland() -> Optional[Tuple[int, int, int, int]]:
    try:
        result = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        if data.get("class") == "kitty":
            at = data.get("at", [0, 0])
            size = data.get("size", [800, 600])
            return (at[0], at[1], size[0], size[1])
    except Exception:
        return None

    return None


def calculate_popup_geometry(
    x: int, y: int, width: int, height: int, ratio: float
) -> Tuple[int, int, int, int]:
    popup_width = int(width * ratio)
    popup_height = int(height * ratio)
    popup_x = x + (width - popup_width) // 2
    popup_y = y + (height - popup_height) // 2
    return (popup_x, popup_y, popup_width, popup_height)


def handle_result(args: List[str], answer: str, target_window_id: int, boss) -> None:
    cwd = None
    target_window = boss.window_id_map.get(target_window_id)
    if target_window:
        cwd = target_window.cwd_of_child

    command, command_cwd = resolve_command(args, cwd)

    if command_cwd and os.path.isdir(command_cwd):
        shell_command = [
            "bash",
            "-lc",
            f"cd {shlex.quote(command_cwd)} && exec {' '.join(shlex.quote(part) for part in command)}",
        ]
    else:
        shell_command = command

    geometry = get_window_geometry()
    if geometry:
        x, y, width, height = geometry
        popup_x, popup_y, popup_width, popup_height = calculate_popup_geometry(
            x, y, width, height, 0.86
        )
        quick_access_args = [
            "kitten",
            "quick-access-terminal",
            "--instance-group",
            "kagent-agent-lens",
            "-o",
            "edge=none",
            "-o",
            f"margin_left={popup_x}",
            "-o",
            f"margin_top={popup_y}",
            "-o",
            f"columns={popup_width}px",
            "-o",
            f"lines={popup_height}px",
            "-o",
            "hide_on_focus_loss=no",
            "-o",
            "background_opacity=0.96",
        ]
    else:
        quick_access_args = [
            "kitten",
            "quick-access-terminal",
            "--instance-group",
            "kagent-agent-lens",
            "-o",
            "edge=center-sized",
            "-o",
            "columns=140",
            "-o",
            "lines=42",
            "-o",
            "hide_on_focus_loss=no",
            "-o",
            "background_opacity=0.96",
        ]

    subprocess.Popen([*quick_access_args, *shell_command])


handle_result.no_ui = True
