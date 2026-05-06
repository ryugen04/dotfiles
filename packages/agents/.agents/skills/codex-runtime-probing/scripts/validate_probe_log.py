#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_KEYS = {
    "schema",
    "recorded_at",
    "codex_version",
    "probe",
    "event",
    "command",
    "cwd",
    "input_payload",
    "stdout",
    "stderr",
    "exit_code",
    "verdict",
    "notes",
}

ALLOWED_EVENTS = {
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "Stop",
    "config",
}

ALLOWED_VERDICTS = {"pass", "fail", "inconclusive"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Codex runtime probe JSONL log.")
    parser.add_argument("path", help="Path to the JSONL probe log.")
    return parser.parse_args()


def validate_record(record: object, line_number: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"line {line_number}: record is not an object"]

    missing = sorted(REQUIRED_KEYS - set(record))
    if missing:
        errors.append(f"line {line_number}: missing keys: {', '.join(missing)}")

    if record.get("schema") != "codex.runtime_probe.v1":
        errors.append(f"line {line_number}: invalid schema")

    if record.get("event") not in ALLOWED_EVENTS:
        errors.append(f"line {line_number}: invalid event")

    if record.get("verdict") not in ALLOWED_VERDICTS:
        errors.append(f"line {line_number}: invalid verdict")

    if not isinstance(record.get("command"), list):
        errors.append(f"line {line_number}: command must be a list")

    if not isinstance(record.get("exit_code"), int):
        errors.append(f"line {line_number}: exit_code must be an integer")

    return errors


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"{path}: file does not exist"]

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                errors.append(f"line {line_number}: empty line")
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc}")
                continue
            errors.extend(validate_record(record, line_number))

    return errors


def main() -> int:
    args = parse_args()
    errors = validate_file(Path(args.path))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("probe log valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
