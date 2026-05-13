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
import json
import shlex
import shutil
import subprocess
import tempfile
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
    kitty_ls_json_path = ""
    target_window = boss.window_id_map.get(target_window_id)
    if target_window:
        cwd = target_window.cwd_of_child
        try:
            ls_payload = boss.call_remote_control(target_window, ("ls",))
            if isinstance(ls_payload, str):
                ls_text = ls_payload
            elif ls_payload is not None:
                ls_text = json.dumps(ls_payload)
            else:
                ls_text = ""
            if ls_text:
                with tempfile.NamedTemporaryFile(
                    mode="w", prefix="kagent-kitty-ls-", suffix=".json", delete=False
                ) as fp:
                    fp.write(ls_text)
                    kitty_ls_json_path = fp.name
        except Exception:
            kitty_ls_json_path = ""

    command, command_cwd = resolve_command(args, cwd)

    source_listen_on = ""
    if target_window:
        try:
            source_listen_on = target_window.child.environ.get("KITTY_LISTEN_ON", "")
        except Exception:
            pass
    env_prefix = ""
    if source_listen_on:
        env_prefix = f"KAGENT_KITTY_TO={shlex.quote(source_listen_on)} "
    if kitty_ls_json_path:
        env_prefix = (
            f"{env_prefix}KAGENT_KITTY_LS_JSON_PATH={shlex.quote(kitty_ls_json_path)} "
        )

    run_command = " ".join(shlex.quote(part) for part in command)
    launch_prefix = f"{env_prefix}exec "
    if command_cwd and os.path.isdir(command_cwd):
        shell_command = [
            "bash",
            "-lc",
            f"cd {shlex.quote(command_cwd)} && {launch_prefix}{run_command}",
        ]
    else:
        shell_command = [
            "bash",
            "-lc",
            f"{launch_prefix}{run_command}",
        ]

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
        "hide_on_focus_loss=yes",
        "-o",
        "background_opacity=0.96",
    ]

    subprocess.Popen([*quick_access_args, *shell_command])


handle_result.no_ui = True
