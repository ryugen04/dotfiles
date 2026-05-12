#!/usr/bin/env python3
"""
Open kagent Agent Lens in kitty quick-access-terminal.

Normal use expects the kagent binary to be installed:
    cargo install --path crates/kagent-cli --locked --force

Override command with:
    KAGENT_QUICK_ACCESS_COMMAND='cargo run -p kagent-cli -- quick-access'
    KAGENT_QUICK_ACCESS_CWD="$HOME/dev/projects/kagent"

Pin placement to a kitty output name:
    KAGENT_QUICK_ACCESS_MONITOR=DP-1
"""

import os
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

    output_name = os.environ.get("KAGENT_QUICK_ACCESS_MONITOR", "DP-1")
    quick_access_args = [
        "kitten",
        "quick-access-terminal",
        "--instance-group",
        "kagent-agent-lens",
        "-o",
        f"output_name={output_name}",
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
