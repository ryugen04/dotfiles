#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


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


def latest_execution_for(plan_path: Path) -> Path | None:
    execution_dir = repo_root() / ".codex" / "artifacts" / "execution"
    stem = plan_path.stem
    matches = sorted(
        execution_dir.glob(f"{stem}*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def checked_count(text: str) -> int:
    return len(re.findall(r"^- \[x\] ", text, re.MULTILINE | re.IGNORECASE))


def unchecked_count(text: str) -> int:
    return len(re.findall(r"^- \[ \] ", text, re.MULTILINE))


def feedback_log_path() -> Path:
    return repo_root() / ".codex" / "artifacts" / "learnings" / "feedback-loop.jsonl"


def feedback_state_by_id(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    state: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        feedback_id = str(event.get("feedback_id", ""))
        if not feedback_id:
            continue

        name = str(event.get("event", ""))
        if name == "feedback_opened":
            state[feedback_id] = "open"
        elif name == "feedback_closed":
            state[feedback_id] = "closed"
    return state


def codex_changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root()), "status", "--porcelain", "-uall", ".codex"],
        check=False,
        capture_output=True,
        text=True,
    )
    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        if len(line) > 3:
            files.append(line[3:].strip())
    return files


def plan_touched_in_worktree(plan: Path, changed_files: list[str]) -> bool:
    try:
        plan_rel = plan.relative_to(repo_root()).as_posix()
    except ValueError:
        return False

    active_plan_prefix = ".codex/plans/active/"
    for path in changed_files:
        normalized = path.replace("\\", "/")
        if normalized == plan_rel:
            return True
        if normalized.startswith(active_plan_prefix):
            return True
    return False


def append_feedback_closed(path: Path, feedback_ids: list[str], files: list[str]) -> None:
    if not feedback_ids:
        return

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        closed_at = datetime.now(timezone.utc).isoformat()
        with path.open("a") as f:
            for feedback_id in feedback_ids:
                event = {
                    "event": "feedback_closed",
                    "feedback_id": feedback_id,
                    "closed_at": closed_at,
                    "status": "closed",
                    "close_reason": "codex_files_changed",
                    "changed_files": files[:20],
                }
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        return


def main() -> None:
    plan = latest_plan()
    if not plan:
        return

    text = plan.read_text()
    meta = frontmatter(text)
    execution = latest_execution_for(plan)
    status = meta.get("status", "").strip()
    checked = checked_count(text)
    unchecked = unchecked_count(text)
    changed = codex_changed_files()
    plan_touched = plan_touched_in_worktree(plan, changed)

    notes = []
    if status in {"approved", "in_progress"} and checked == 0:
        notes.append("No completed checklist items are recorded in the active plan.")
    if status == "in_progress" and unchecked > 0 and not plan_touched:
        notes.append("Before ending the session, update the plan checklist or execution notes.")
    if status in {"approved", "in_progress"} and checked > 0 and unchecked == 0 and not execution:
        notes.append(
            "Execution artifact is required before closing a completed plan. "
            "Create one under .codex/artifacts/execution/."
        )

    feedback_log = feedback_log_path()
    feedback_state = feedback_state_by_id(feedback_log)
    open_feedback_ids = sorted([k for k, v in feedback_state.items() if v == "open"])
    if open_feedback_ids:
        if changed:
            append_feedback_closed(feedback_log, open_feedback_ids, changed)
        else:
            notes.append(
                "Open user feedback items exist in .codex/artifacts/learnings/feedback-loop.jsonl. "
                "Update .codex files before ending the session."
            )

    if notes:
        payload = {
            "decision": "block",
            "reason": " ".join(notes),
        }
        print(json.dumps(payload))


if __name__ == "__main__":
    main()
