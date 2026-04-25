#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


KEYWORD_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bfeedback\b",
        r"\bpost[- ]?mortem\b",
        r"\bretrospective\b",
        r"\bapprove\b",
        r"フィードバック",
        r"指摘",
        r"再発防止",
        r"ルール",
        r"見直し",
        r"改善",
        r"運用",
    ]
]


def repo_root() -> Path:
    value = os.environ.get("CODEX_PROJECT_ROOT", "").strip()
    if value:
        return Path(value).resolve()

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return Path.cwd().resolve()


def load_input() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def prompt_text(payload: dict) -> str:
    value = payload.get("prompt")
    if isinstance(value, str):
        return value
    value = payload.get("tool_input", {}).get("prompt")
    if isinstance(value, str):
        return value
    return ""


def matched_keywords(text: str) -> list[str]:
    matches: list[str] = []
    for pattern in KEYWORD_PATTERNS:
        if pattern.search(text):
            matches.append(pattern.pattern)
    return matches


def read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def next_feedback_id(events: list[dict], now: datetime) -> str:
    prefix = now.strftime("fb-%Y%m%d-")
    max_seq = 0
    for event in events:
        feedback_id = str(event.get("feedback_id", ""))
        if not feedback_id.startswith(prefix):
            continue
        maybe_seq = feedback_id.replace(prefix, "", 1)
        if maybe_seq.isdigit():
            max_seq = max(max_seq, int(maybe_seq))
    return f"{prefix}{max_seq + 1:03d}"


def main() -> None:
    payload = load_input()
    prompt = prompt_text(payload).strip()
    if not prompt:
        return

    matched = matched_keywords(prompt)
    if not matched:
        return

    root = repo_root()
    log_path = root / ".codex" / "artifacts" / "learnings" / "feedback-loop.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    events = read_events(log_path)
    feedback_id = next_feedback_id(events, now)
    event = {
        "event": "feedback_opened",
        "feedback_id": feedback_id,
        "created_at": now.isoformat(),
        "session_id": payload.get("session_id"),
        "keywords": matched,
        "prompt_excerpt": prompt[:400],
        "required_scope": ".codex",
        "status": "open",
    }
    persisted = True
    try:
        with log_path.open("a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        persisted = False

    rel = log_path.relative_to(root)
    persist_note = "" if persisted else " (persistence failed: check filesystem permissions)"
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                f"User feedback captured as {feedback_id} in {rel}. "
                "Before ending the session, update .codex files and close the feedback loop."
                f"{persist_note}"
            ),
        }
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
