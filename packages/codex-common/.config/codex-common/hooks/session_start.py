#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


REQUIRED_SECTIONS = [
    "## Context",
    "## 完了基準",
    "## Phase Checklist",
    "## Agent Assignment",
    "## Review Loop",
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


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}
    data = {}
    for line in parts[0].splitlines()[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def latest_plan() -> Path | None:
    active_dir = repo_root() / ".codex" / "plans" / "active"
    candidates = sorted(
        [p for p in active_dir.glob("*.md") if p.name != "README.md"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def latest_review_for(plan_path: Path) -> Path | None:
    review_dir = repo_root() / ".codex" / "artifacts" / "reviews"
    stem = plan_path.stem
    matches = sorted(
        review_dir.glob(f"{stem}*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def unchecked_tasks(text: str) -> list[str]:
    return re.findall(r"^- \[ \] (.+)$", text, re.MULTILINE)


def missing_sections(text: str) -> list[str]:
    return [section for section in REQUIRED_SECTIONS if section not in text]


def main() -> None:
    plan = latest_plan()
    if not plan:
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    "No active plan found in .codex/plans/active. "
                    "Before editing implementation files, create an active plan in .codex/plans/active."
                ),
            }
        }
        print(json.dumps(payload))
        return

    text = plan.read_text()
    meta = frontmatter(text)
    review = latest_review_for(plan)
    lines = [
        f"Active plan: {plan.relative_to(repo_root())}",
        f"Status: {meta.get('status', 'unknown')}",
    ]
    missing = missing_sections(text)
    if missing:
        lines.append("Missing required sections: " + ", ".join(missing))
    if review:
        lines.append(f"Latest Claude review: {review.relative_to(repo_root())}")
    else:
        lines.append("Latest Claude review: none")
    tasks = unchecked_tasks(text)[:5]
    if tasks:
        lines.append("Next unchecked tasks:")
        lines.extend(f"- {task}" for task in tasks)

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
