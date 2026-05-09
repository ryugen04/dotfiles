from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io import ensure_dir, now_iso, read_data
from .workspace import ai_dlc_context, stable_project_id

ACTION_TYPES = {"durable_record", "external_fix_plan", "repair_task_created", "resolved", "deferred_by_user"}
FINISH_BOUNDARY_ACTIONS = ACTION_TYPES
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{12,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{12,}"),
    re.compile(r"xox[a-zA-Z]-[A-Za-z0-9-]{12,}"),
    re.compile(r"(?i)([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|KEY)[A-Z0-9_]*=)([^\s]+)"),
    re.compile(r"(?i)(Authorization:\s*Bearer\s+)([^\s]+)"),
    re.compile(r"\b[0-9a-fA-F]{40,}\b"),
    re.compile(r"\b[A-Za-z0-9+/]{48,}={0,2}\b"),
]


def ledger_root() -> Path:
    return Path.home() / ".codex" / "ai-dlc" / "block-ledger"


def events_path() -> Path:
    return ledger_root() / "events.jsonl"


def actions_path() -> Path:
    return ledger_root() / "actions.jsonl"


def redact(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _append_jsonl(path: Path, item: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True, ensure_ascii=True) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            items.append(data)
    return items


def _utc_event_id(seed: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(f"{stamp}:{seed}:{uuid.uuid4().hex}".encode("utf-8")).hexdigest()[:8]
    return f"B{stamp}-{digest}"


def _extract_command(payload: dict[str, Any]) -> str:
    for key in ["command", "cmd"]:
        value = payload.get(key)
        if isinstance(value, str):
            return value
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ["command", "cmd"]:
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    return ""


def _workspace_id(workspace: Path | None) -> str:
    if workspace is None:
        return ""
    try:
        data = read_data(workspace / "workspace.yaml")
    except Exception:
        return workspace.resolve().name
    return str(data.get("id") or workspace.resolve().name)


def _project_id(effective_cwd: Path, workspace: Path | None) -> str:
    if workspace is not None:
        return ""
    try:
        context = ai_dlc_context(effective_cwd, ensure_user_local=True)
        root = context.get("root")
        if root:
            context_path = Path(root) / "context.yaml"
            if context_path.exists():
                data = read_data(context_path)
                return str(data.get("project_id") or stable_project_id(effective_cwd))
        return stable_project_id(effective_cwd)
    except Exception:
        return stable_project_id(effective_cwd)


def scope_for(root_or_cwd: Path, workspace: Path | None = None) -> dict[str, str]:
    workspace_path = workspace or (root_or_cwd if (root_or_cwd / "workspace.yaml").exists() else None)
    workspace_id = _workspace_id(workspace_path)
    project_id = "" if workspace_id else _project_id(root_or_cwd, None)
    if workspace_id and workspace_path is not None:
        scope_digest = hashlib.sha256(str(workspace_path.expanduser().resolve()).encode("utf-8")).hexdigest()[:12]
        scope_key = f"workspace:{workspace_id}:{scope_digest}"
    else:
        scope_key = f"project:{project_id}"
    return {
        "workspace_id": workspace_id,
        "project_id": project_id,
        "scope_key": scope_key,
    }


def record_block_event(
    *,
    payload: dict[str, Any],
    event_name: str,
    effective_cwd: Path,
    workspace: Path | None,
    diagnosis: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    scope = scope_for(effective_cwd, workspace)
    command = _extract_command(payload)
    event = {
        "event_id": _utc_event_id(reason),
        "timestamp": now_iso(),
        "session_id": str(payload.get("session_id") or os.environ.get("CODEX_SESSION_ID") or ""),
        "turn_id": str(payload.get("turn_id") or ""),
        "event": event_name,
        "source_cwd": str(Path.cwd()),
        "effective_cwd": str(effective_cwd.expanduser().resolve()),
        "workspace_id": scope["workspace_id"],
        "project_id": scope["project_id"],
        "scope_key": scope["scope_key"],
        "repo_hint": effective_cwd.expanduser().resolve().name,
        "block_type": str(diagnosis.get("block_type") or "unknown"),
        "route": str(diagnosis.get("suggested_route") or ""),
        "tool": str(payload.get("tool_name") or payload.get("tool") or ""),
        "command": redact(command),
        "reason": redact(reason),
        "suggested_actions": list(diagnosis.get("allowed_next_actions") or []),
        "requires_durable_record": True,
    }
    _append_jsonl(events_path(), event)
    return event


def list_events(*, include_recorded: bool = False, scope_key: str | None = None) -> list[dict[str, Any]]:
    events = _read_jsonl(events_path())
    actioned = actioned_event_ids()
    result = []
    for event in events:
        if scope_key and event.get("scope_key") != scope_key:
            continue
        recorded = event.get("event_id") in actioned
        if recorded and not include_recorded:
            continue
        item = dict(event)
        item["recorded"] = recorded
        result.append(item)
    return result


def list_actions() -> list[dict[str, Any]]:
    return _read_jsonl(actions_path())


def actioned_event_ids() -> set[str]:
    return {str(action.get("block_event_id")) for action in list_actions() if action.get("block_event_id")}


def open_block_events_for(root: Path) -> list[dict[str, Any]]:
    scope = scope_for(root)
    return list_events(scope_key=scope["scope_key"])


def open_blocker_errors(root: Path, boundary: str) -> list[str]:
    events = open_block_events_for(root)
    if not events:
        return []
    ids = ", ".join(str(event.get("event_id")) for event in events[:5])
    more = "" if len(events) <= 5 else f" (+{len(events) - 5} more)"
    return [f"open AI-DLC block events must be actioned before {boundary}: {ids}{more}"]


def record_block_action(event_id: str, action_type: str, ref: str, reason: str = "") -> dict[str, Any]:
    if action_type not in ACTION_TYPES:
        raise ValueError(f"invalid block action type: {action_type}")
    if action_type == "deferred_by_user" and not reason:
        raise ValueError("deferred_by_user requires --reason")
    action = {
        "timestamp": now_iso(),
        "block_event_id": event_id,
        "action_type": action_type,
        "ref": ref,
        "reason": redact(reason),
    }
    _append_jsonl(actions_path(), action)
    return action


def _ref_allowed(ref: str) -> bool:
    if ref.startswith(("http://", "https://")):
        return True
    normalized = ref.replace("\\", "/")
    allowed_prefixes = ("ai-dlc/decisions/", "ai-dlc/evidence/", ".codex/plans/")
    return normalized.startswith(allowed_prefixes) or normalized.startswith("/")


def write_block_ref(ref: Path, event_id: str, action_type: str, reason: str = "") -> None:
    ensure_dir(ref.parent)
    existing = ref.read_text(encoding="utf-8") if ref.exists() else ""
    if event_id in existing:
        return
    suffix = "\n" if existing and not existing.endswith("\n") else ""
    if ref.suffix.lower() in {".yaml", ".yml"}:
        text = f"{suffix}block_events:\n- event_id: {event_id}\n  action_type: {action_type}\n"
    else:
        text = f"{suffix}- block_event_id: {event_id}; action_type: {action_type}"
        if reason:
            text += f"; reason: {redact(reason)}"
        text += "\n"
    ref.write_text(existing + text, encoding="utf-8")


def record_block_ref(event_id: str, action_type: str, ref: str, reason: str = "", *, base: Path | None = None) -> dict[str, Any]:
    if not _ref_allowed(ref):
        raise ValueError("block ref must be ai-dlc/decisions/**, ai-dlc/evidence/**, .codex/plans/**, an absolute path, or a URL")
    if not ref.startswith(("http://", "https://")):
        path = Path(ref)
        if not path.is_absolute():
            path = (base or Path.cwd()) / path
        write_block_ref(path, event_id, action_type, reason)
        ref = str(path)
    return record_block_action(event_id, action_type, ref, reason)


def sync_block_actions(root: Path) -> list[dict[str, Any]]:
    events = list_events(include_recorded=False)
    if not events:
        return []
    candidates = [
        root / "ai-dlc" / "decisions",
        root / "ai-dlc" / "evidence",
        root / ".codex" / "plans",
    ]
    created: list[dict[str, Any]] = []
    for event in events:
        event_id = str(event.get("event_id"))
        for directory in candidates:
            if not directory.exists():
                continue
            for path in directory.rglob("*"):
                if not path.is_file():
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if event_id in text:
                    created.append(record_block_action(event_id, "durable_record", str(path), "synced from durable artifact"))
                    break
            if event_id in actioned_event_ids():
                break
    return created


def export_block_plan(event_id: str, destination: Path) -> Path:
    event = next((item for item in list_events(include_recorded=True) if item.get("event_id") == event_id), None)
    if event is None:
        raise ValueError(f"block event not found: {event_id}")
    ensure_dir(destination.parent)
    body = {
        "event_id": event_id,
        "block_type": event.get("block_type"),
        "route": event.get("route"),
        "effective_cwd": event.get("effective_cwd"),
        "reason": event.get("reason"),
        "suggested_actions": event.get("suggested_actions", []),
    }
    destination.write_text(
        "# AI-DLC Block Repair Plan\n\n"
        "```json\n"
        + json.dumps(body, indent=2, ensure_ascii=True)
        + "\n```\n",
        encoding="utf-8",
    )
    record_block_action(event_id, "external_fix_plan", str(destination), "exported repair plan")
    return destination
