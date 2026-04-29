from __future__ import annotations

import fnmatch
import json
import os
import re
from pathlib import Path
from typing import Any

from .io import read_data, read_frontmatter, read_text
from .state import assignment_root, bootstrap_gate_errors, lease_path_errors, load_assignment, load_lease

DESTRUCTIVE_GIT = ["git reset --hard", "git clean", "git push", "git merge", "git worktree remove", "rm -rf"]
EDIT_TOOLS = {"apply_patch", "Edit", "Write", "MultiEdit"}
CONTROLLER_ALLOWED_PATHS = ["ai-dlc/plans/**", "ai-dlc/work-items/**", "ai-dlc/decisions/**", "ai-dlc/handoff/**", "ai-dlc/quality/**"]
WRITE_LIKE_BASH_PATTERNS = ["sed -i", "perl -pi", "python -c", "python3 -c", "ruby -pi", "tee ", " cat > ", " > ", " >> "]
AGENT_TOOLS = {"spawn_agent", "send_input"}
READ_ONLY_BASH_PREFIXES = (
    "git status",
    "git diff",
    "git rev-parse",
    "git log",
    "git show",
    "git branch",
    "git ls-files",
    "git -C ",
    "ls",
    "pwd",
    "cat ",
    "find ",
    "rg ",
    "ai-dlc status",
    "ai-dlc validate",
    "ai-dlc validate-overlay",
    "ai-dlc overlay-status",
    "ai-dlc deadlock-check",
    "ai-dlc clean-state-check",
)


def _find_workspace(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "workspace.yaml").exists():
            return candidate
    return None


def _load_payload() -> dict[str, Any]:
    try:
        raw = input()
    except EOFError:
        return {}
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _extract_command(payload: dict[str, Any]) -> str:
    for key in ["command", "cmd"]:
        if isinstance(payload.get(key), str):
            return payload[key]
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ["cmd", "command"]:
            if isinstance(tool_input.get(key), str):
                return tool_input[key]
    return ""


def _extract_tool(payload: dict[str, Any]) -> str:
    return str(payload.get("tool_name") or payload.get("tool") or os.environ.get("CODEX_TOOL_NAME") or "")


def _relativize(workspace: Path, value: str) -> str | None:
    path = Path(value)
    if not path.is_absolute():
        return value
    try:
        return str(path.resolve().relative_to(workspace.resolve()))
    except Exception:
        try:
            return os.path.relpath(path.resolve(), workspace.resolve())
        except Exception:
            return None


def _extract_paths_from_patch(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        match = re.match(r"\*\*\* (?:Add|Update|Delete) File: (.+)", line)
        if match:
            paths.append(match.group(1).strip())
    return paths


def _extract_paths(payload: dict[str, Any], workspace: Path) -> list[str]:
    raw_paths: list[str] = []
    for key in ["file_path", "path"]:
        value = payload.get(key)
        if isinstance(value, str):
            raw_paths.append(value)
    for key in ["paths", "files"]:
        value = payload.get(key)
        if isinstance(value, list):
            raw_paths.extend(item for item in value if isinstance(item, str))

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ["file_path", "path"]:
            value = tool_input.get(key)
            if isinstance(value, str):
                raw_paths.append(value)
        for key in ["paths", "files"]:
            value = tool_input.get(key)
            if isinstance(value, list):
                raw_paths.extend(item for item in value if isinstance(item, str))
        if isinstance(tool_input.get("patch"), str):
            raw_paths.extend(_extract_paths_from_patch(tool_input["patch"]))
    elif isinstance(tool_input, str):
        raw_paths.extend(_extract_paths_from_patch(tool_input))

    result: list[str] = []
    for raw_path in raw_paths:
        relative = _relativize(workspace, raw_path)
        if relative:
            result.append(relative)
    return sorted(set(result))


def _paths_match(paths: list[str], patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for path in paths for pattern in patterns)


def _allow(reason: str = "ok") -> dict[str, str]:
    return {"decision": "allow", "reason": reason}


def _block(reason: str) -> dict[str, str]:
    return {"decision": "block", "reason": reason}


def _is_write_like_bash(command: str) -> bool:
    normalized = f" {command} "
    return any(pattern in normalized for pattern in WRITE_LIKE_BASH_PATTERNS)


def _extract_agent_target(payload: dict[str, Any]) -> str:
    for key in ["agent_name", "agent", "target_agent", "name"]:
        value = payload.get(key)
        if isinstance(value, str) and value.startswith("dlc_"):
            return value
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ["agent_name", "agent", "target_agent", "name"]:
            value = tool_input.get(key)
            if isinstance(value, str) and value.startswith("dlc_"):
                return value
        message = tool_input.get("message")
        if isinstance(message, str):
            match = re.search(r"\b(dlc_[a-z0-9_]+)\b", message)
            if match:
                return match.group(1)
    message = payload.get("message")
    if isinstance(message, str):
        match = re.search(r"\b(dlc_[a-z0-9_]+)\b", message)
        if match:
            return match.group(1)
    return ""


def _decision_allows_agent(workspace: Path, agent_name: str) -> bool:
    workspace_data = read_data(workspace / "workspace.yaml")
    path = workspace / workspace_data["paths"]["decisions"]
    text = read_text(path)
    return f"allow-next-agent: {agent_name}" in text


def _recommendation_allows_agent(workspace: Path, agent_name: str) -> bool:
    base = assignment_root(workspace)
    reports_dir = base / "reports"
    if not reports_dir.exists():
        return False
    for path in reports_dir.glob("A*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        recommendation = data.get("next_recommendation") or {}
        if recommendation.get("assignment_role") == agent_name:
            return True
    return False


def _claimed_repo_worker_exists(workspace: Path) -> bool:
    base = assignment_root(workspace)
    assignments_dir = base / "assignments"
    if not assignments_dir.exists():
        return False
    for path in assignments_dir.glob("A*.yaml"):
        assignment = read_data(path)
        if assignment.get("role") == "dlc_repo_worker" and assignment.get("status") == "claimed":
            return True
    return False


def dispatch(cwd: Path) -> dict[str, str]:
    payload = _load_payload()
    workspace = _find_workspace(cwd)
    if workspace is None:
        return _allow("not an AI-DLC workspace")

    tool = _extract_tool(payload)
    command = _extract_command(payload)
    if any(pattern in command for pattern in DESTRUCTIVE_GIT):
        return _block("AI-DLC: destructive git command requires explicit approval.")

    if tool == "Bash" and _is_write_like_bash(command) and os.environ.get("AI_DLC_ALLOW_CONTROLLER_EDIT") != "1":
        return _block("AI-DLC: write-like Bash commands are blocked; use apply_patch/Edit with a claimed lease.")
    if tool == "Bash" and command and not command.startswith(READ_ONLY_BASH_PREFIXES):
        if "ai-dlc root-export" not in command and "ai-dlc overlay-cleanup" not in command and "git commit" not in command:
            return _block("AI-DLC: unknown mutating Bash commands are denied by default in AI-DLC workspaces.")

    if tool in EDIT_TOOLS:
        rel_paths = _extract_paths(payload, workspace)
        if not rel_paths:
            return _block("AI-DLC: edited paths could not be determined.")

        if os.environ.get("AI_DLC_ALLOW_CONTROLLER_EDIT") == "1":
            return _allow("controller override enabled")

        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None:
            if _paths_match(rel_paths, CONTROLLER_ALLOWED_PATHS):
                return _block("AI-DLC: controller must delegate tracked plan or handoff edits to a claimed subagent.")
            return _block("AI-DLC: writable session requires a claimed lease.")

        assignment = load_assignment(workspace, lease["assignment_id"])
        if assignment.get("status") != "claimed":
            return _block("AI-DLC: assignment must be claimed before editing.")

        if lease.get("role") == "dlc_repo_worker":
            errors = bootstrap_gate_errors(workspace, lease)
            if errors:
                return _block(f"AI-DLC: bootstrap gate failed: {'; '.join(errors)}")

        errors = lease_path_errors(workspace, lease, rel_paths)
        if errors:
            return _block(f"AI-DLC: lease violation: {'; '.join(errors)}")

    if tool == "Bash" and "git commit" in command and " -C " not in f" {command} " and "AI_DLC_ALLOW_OVERLAY_BASELINE" not in command:
        workspace_data = read_data(workspace / "workspace.yaml")
        embedded = [name for name in workspace_data["repos"] if name != "root-system"]
        if embedded:
            return _block("AI-DLC: commit embedded repos from child repositories, not from root-system.")

    if tool == "Bash" and "ai-dlc root-export" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            return _block("AI-DLC: root-export requires a claimed git_operator lease.")

    if tool == "Bash" and "ai-dlc overlay-cleanup" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            return _block("AI-DLC: overlay-cleanup requires a claimed git_operator lease.")

    if tool == "Bash" and "git -C " in command and " commit" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            return _block("AI-DLC: child repo commit requires a claimed git_operator lease.")

    if tool == "Bash" and command.startswith("git -C "):
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease and lease.get("repo"):
            repo_prefix = f"git -C {lease['repo']}"
            if repo_prefix not in command:
                return _block(f"AI-DLC: session lease only permits git -C {lease['repo']} commands.")

    if tool in AGENT_TOOLS:
        target_agent = _extract_agent_target(payload)
        if target_agent:
            workspace_data = read_data(workspace / "workspace.yaml")
            plan_meta, _ = read_frontmatter(workspace / workspace_data["paths"]["plan"])
            expected = (plan_meta.get("current") or {}).get("next_agent")
            allowed = False
            if expected and target_agent == expected:
                allowed = True
            if _decision_allows_agent(workspace, target_agent):
                allowed = True
            if _recommendation_allows_agent(workspace, target_agent):
                allowed = True
            if plan_meta.get("status") in {"planning", "plan_ready", "assigning"} and target_agent == "dlc_explorer":
                allowed = True
            if plan_meta.get("status") == "repairing" and target_agent == "dlc_repairer":
                allowed = True
            if not allowed:
                return _block(f"AI-DLC: next agent must be {expected} unless decisions explicitly allow {target_agent}.")
            if target_agent == "dlc_verifier" and _claimed_repo_worker_exists(workspace):
                return _block("AI-DLC: verifier must not run while a repo_worker assignment is still claimed.")

    return _allow()
