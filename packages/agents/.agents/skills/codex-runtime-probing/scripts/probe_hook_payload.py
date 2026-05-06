#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_EVENTS = {
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "Stop",
    "config",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture one Codex hook payload as a runtime probe JSONL record."
    )
    parser.add_argument("--event", required=True, choices=sorted(ALLOWED_EVENTS))
    parser.add_argument("--output", help="JSONL output path. If omitted, writes to stdout.")
    parser.add_argument("--note", default="", help="Optional probe note.")
    return parser.parse_args()


def read_stdin_json() -> tuple[object, str]:
    if sys.stdin.isatty():
        return {}, "no stdin"

    raw = sys.stdin.read()
    if not raw.strip():
        return {}, "empty stdin"

    try:
        return json.loads(raw), ""
    except json.JSONDecodeError as exc:
        return {"_invalid_json": raw}, f"invalid stdin JSON: {exc}"


def build_record(event: str, note: str) -> dict[str, object]:
    payload, stdin_note = read_stdin_json()
    notes = note
    if stdin_note:
        notes = f"{notes}; {stdin_note}" if notes else stdin_note

    return {
        "schema": "codex.runtime_probe.v1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "codex_version": os.environ.get("CODEX_VERSION", "unknown"),
        "probe": "hook_payload_capture",
        "event": event,
        "command": sys.argv,
        "cwd": os.getcwd(),
        "input_payload": payload,
        "stdout": "",
        "stderr": "",
        "exit_code": 0,
        "verdict": "pass" if not stdin_note.startswith("invalid") else "inconclusive",
        "notes": notes,
    }


def emit(record: dict[str, object], output: str | None) -> None:
    line = json.dumps(record, ensure_ascii=True, sort_keys=True)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return

    print(line)


def main() -> int:
    args = parse_args()
    record = build_record(args.event, args.note)
    emit(record, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
