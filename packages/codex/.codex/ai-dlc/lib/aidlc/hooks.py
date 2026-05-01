from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
from pathlib import Path
from typing import Any

from .io import read_data, read_frontmatter, read_text
from .state import assignment_root, bootstrap_gate_errors, lease_path_errors, load_assignment, load_lease

DESTRUCTIVE_GIT = ["git reset --hard", "git clean", "git push", "git merge", "git worktree remove", "rm -rf", "sango worktree remove"]
EDIT_TOOLS = {"apply_patch", "Edit", "Write", "MultiEdit"}
CONTROLLER_ALLOWED_PATHS = ["ai-dlc/plans/**", "ai-dlc/work-items/**", "ai-dlc/decisions/**", "ai-dlc/handoff/**", "ai-dlc/quality/**"]
DEFAULT_BOOTSTRAP_EDIT_PATHS = [".codex/config.toml", "AGENTS.md", "ai-dlc/**"]
WRITE_LIKE_BASH_PATTERNS = ["sed -i", "perl -pi", "python -c", "python3 -c", "ruby -pi", "tee ", " cat > ", " > ", " >> "]
AGENT_TOOLS = {"spawn_agent", "send_input"}
READ_ONLY_BASH_COMMANDS = {"ls", "pwd", "cat", "find", "rg", "sed", "head", "tail", "wc", "sort", "uniq", "cut"}
READ_ONLY_AIDLC_COMMANDS = {
    ("ai-dlc", "doctor"),
    ("ai-dlc", "status"),
    ("ai-dlc", "validate"),
    ("ai-dlc", "validate-overlay"),
    ("ai-dlc", "overlay-status"),
    ("ai-dlc", "deadlock-check"),
    ("ai-dlc", "clean-state-check"),
}
BOOTSTRAP_AIDLC_COMMANDS = {
    ("ai-dlc", "install"),
    ("ai-dlc", "init-project"),
    ("ai-dlc", "init-workspace"),
    ("ai-dlc", "install-project-hooks"),
    ("ai-dlc", "overlay-init"),
    ("ai-dlc", "overlay-repair"),
    ("ai-dlc", "bootstrap"),
    ("sango", "worktree"),
    ("sango", "status"),
    ("sango", "doctor"),
    ("sango", "bootstrap"),
}
READ_ONLY_GIT_SUBCOMMANDS = {"status", "diff", "rev-parse", "log", "show", "branch", "ls-files", "worktree"}
READ_ONLY_GH_SUBCOMMAND_PAIRS = {
    ("pr", "view"),
    ("pr", "list"),
    ("pr", "diff"),
    ("pr", "checks"),
    ("pr", "status"),
    ("issue", "view"),
    ("issue", "list"),
    ("issue", "status"),
    ("run", "view"),
    ("run", "list"),
    ("release", "view"),
    ("release", "list"),
    ("repo", "view"),
    ("api",),
}
DISALLOWED_SHELL_FRAGMENTS = ("`", "$(", "\n", "\r", ";", "&&", "||")
DISALLOWED_SHELL_TOKENS = {"|", "&", ">", ">>", "<", "<<", "<<<"}
READ_ONLY_FIND_FORBIDDEN_PREFIXES = ("-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fls")


def _find_workspace(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "workspace.yaml").exists():
            return candidate
    return None


def _find_project_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "ai-dlc" / "project-metadata.yaml").exists():
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


def _extract_event_name(payload: dict[str, Any]) -> str:
    for key in ["hook_event_name", "hookEventName", "event", "event_name"]:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    hook_event = payload.get("hook_event")
    if isinstance(hook_event, dict):
        for key in ["name", "event_name", "hookEventName"]:
            value = hook_event.get(key)
            if isinstance(value, str) and value:
                return value
    return str(os.environ.get("CODEX_HOOK_EVENT_NAME") or "")


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

    command_text = _extract_command(payload)
    if command_text:
        raw_paths.extend(_extract_paths_from_patch(command_text))

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


def _noop() -> dict[str, Any]:
    return {}


def _hook_output(event_name: str, additional_context: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": additional_context,
        }
    }


def _allow_hook(event_name: str, reason: str = "ok") -> dict[str, Any]:
    if event_name == "PreToolUse":
        return _noop()
    if event_name == "PermissionRequest":
        return {"permissionDecision": "allow", "permissionDecisionReason": reason}
    if event_name in {"PostToolUse", "Stop"}:
        return _noop()
    return _allow(reason)


def _block_hook(event_name: str, reason: str) -> dict[str, Any]:
    if event_name == "PreToolUse":
        return _block(reason)
    if event_name == "PermissionRequest":
        return {"permissionDecision": "deny", "permissionDecisionReason": reason}
    if event_name in {"PostToolUse", "Stop"}:
        return _noop()
    return _block(reason)


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


def _find_codex_config(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        config_path = candidate / ".codex" / "config.toml"
        if config_path.exists():
            return config_path
    return None


def _parse_guardrail_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value.strip("\"'")
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, str)]
    return value.strip("\"'")


def _load_guardrails(start: Path) -> dict[str, Any]:
    config_path = _find_codex_config(start)
    if config_path is None:
        return {}
    try:
        text = read_text(config_path)
    except Exception:
        return {}
    in_guardrails = False
    guardrails: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            in_guardrails = line == "[guardrails]"
            continue
        if not in_guardrails or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        guardrails[key] = _parse_guardrail_value(value)
    return guardrails


def _subagent_required_outside_workspace(start: Path) -> bool:
    guardrails = _load_guardrails(start)
    if "subagent_required" in guardrails:
        return bool(guardrails["subagent_required"])
    return _find_project_root(start) is not None


def _bootstrap_extra_commands(start: Path) -> list[str]:
    value = _load_guardrails(start).get("bootstrap_extra_commands")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def _bootstrap_edit_paths(start: Path) -> list[str]:
    value = _load_guardrails(start).get("bootstrap_edit_paths")
    if isinstance(value, list):
        configured = [item for item in value if isinstance(item, str) and item.strip()]
        if configured:
            return configured
    return list(DEFAULT_BOOTSTRAP_EDIT_PATHS)


def _all_paths_match(paths: list[str], patterns: list[str]) -> bool:
    if not paths:
        return False
    return all(any(fnmatch.fnmatch(path, pattern) for pattern in patterns) for path in paths)


def _is_read_only_sed(tokens: list[str]) -> bool:
    quiet = False
    for token in tokens[1:]:
        if token == "--in-place" or token.startswith("--in-place="):
            return False
        if token.startswith("--"):
            if token in {"--quiet", "--silent"}:
                quiet = True
            continue
        if token.startswith("-") and token != "-":
            flags = token[1:]
            if "i" in flags:
                return False
            if "n" in flags:
                quiet = True
    return quiet


def _is_read_only_find(tokens: list[str]) -> bool:
    return not any(token.startswith(READ_ONLY_FIND_FORBIDDEN_PREFIXES) for token in tokens[1:])


def _is_read_only_sort(tokens: list[str]) -> bool:
    for token in tokens[1:]:
        if token == "-o" or token == "--output" or token.startswith("-o") or token.startswith("--output="):
            return False
    return True


def _is_read_only_gh(tokens: list[str]) -> bool:
    # gh <subcommand> [<action>] の組み合わせで判定
    if len(tokens) < 2:
        return False
    sub = tokens[1]
    if (sub,) in READ_ONLY_GH_SUBCOMMAND_PAIRS:
        return True
    if len(tokens) >= 3 and (sub, tokens[2]) in READ_ONLY_GH_SUBCOMMAND_PAIRS:
        return True
    return False


def _is_safe_aidlc_command(command: str) -> bool:
    normalized = command.strip()
    if any(fragment in normalized for fragment in DISALLOWED_SHELL_FRAGMENTS):
        return False
    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return False
    if not tokens or any(token in DISALLOWED_SHELL_TOKENS for token in tokens):
        return False
    return tokens[0] == "ai-dlc"


def _is_read_only_bash(command: str) -> bool:
    normalized = command.strip()
    if not normalized:
        return True
    if any(fragment in normalized for fragment in DISALLOWED_SHELL_FRAGMENTS):
        return False
    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return False
    if not tokens or any(token in DISALLOWED_SHELL_TOKENS for token in tokens):
        return False
    if tokens[0] == "ai-dlc":
        return True
    command_name = tokens[0]
    if command_name in READ_ONLY_BASH_COMMANDS:
        if command_name == "sed":
            return _is_read_only_sed(tokens)
        if command_name == "find":
            return _is_read_only_find(tokens)
        if command_name == "sort":
            return _is_read_only_sort(tokens)
        return True
    if command_name == "gh":
        return _is_read_only_gh(tokens)
    if command_name != "git":
        return False
    if len(tokens) >= 4 and tokens[1] == "-C":
        subcommand = tokens[3]
    elif len(tokens) >= 2:
        subcommand = tokens[1]
    else:
        return False
    if subcommand != "worktree":
        return subcommand in READ_ONLY_GIT_SUBCOMMANDS
    return len(tokens) >= 5 and tokens[4] == "list"


def _is_allowed_bootstrap_command(command: str, cwd: Path) -> bool:
    normalized = command.strip()
    if not normalized:
        return False
    if any(fragment in normalized for fragment in DISALLOWED_SHELL_FRAGMENTS):
        return False
    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return False
    if not tokens or any(token in DISALLOWED_SHELL_TOKENS for token in tokens):
        return False
    if tokens[0] == "ai-dlc":
        return True
    if len(tokens) >= 3 and tokens[0] == "sango" and tokens[1] == "worktree":
        return tokens[2] in {"create", "list", "status"}
    if len(tokens) >= 2 and (tokens[0], tokens[1]) in BOOTSTRAP_AIDLC_COMMANDS:
        return True
    return normalized in _bootstrap_extra_commands(cwd)


def _is_git_commit(command: str) -> bool:
    normalized = command.strip()
    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return False
    if not tokens or tokens[0] != "git":
        return False
    if len(tokens) >= 4 and tokens[1] == "-C":
        return tokens[3] == "commit"
    return len(tokens) >= 2 and tokens[1] == "commit"


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


def _session_start_context(workspace: Path | None) -> str:
    if workspace is None:
        return "AI-DLC workspace ではありません。"

    workspace_data = read_data(workspace / "workspace.yaml")
    plan_meta, _ = read_frontmatter(workspace / workspace_data["paths"]["plan"])
    lines = [
        f"Workspace: {workspace.name}",
        f"Plan status: {plan_meta.get('status', 'unknown')}",
    ]
    current = plan_meta.get("current") or {}
    if isinstance(current, dict):
        active_item = current.get("active_work_item")
        next_agent = current.get("next_agent")
        if active_item:
            lines.append(f"Active work item: {active_item}")
        if next_agent:
            lines.append(f"Next agent: {next_agent}")
    return "\n".join(lines)


def _prompt_delta_context(workspace: Path | None) -> str:
    if workspace is None:
        return ""

    workspace_data = read_data(workspace / "workspace.yaml")
    plan_meta, _ = read_frontmatter(workspace / workspace_data["paths"]["plan"])
    current = plan_meta.get("current") or {}
    if not isinstance(current, dict):
        return ""

    parts: list[str] = []
    if current.get("active_work_item"):
        parts.append(f"Active: {current['active_work_item']}")
    if current.get("next_agent"):
        parts.append(f"Next: {current['next_agent']}")
    return " / ".join(parts)


def _non_workspace_context(cwd: Path) -> str:
    project_root = _find_project_root(cwd)
    if project_root is not None:
        return (
            "AI-DLC root-system projectです。task workspaceではありません。"
            " 対象 worktree の workspace.yaml がある場所へ移動するか、workflow-bootstrap で既存 worktree を採用してください。"
            " 直接編集は禁止です。"
        )
    if _subagent_required_outside_workspace(cwd):
        extras = _bootstrap_extra_commands(cwd)
        if extras:
            return (
                "Controller-only bootstrap phase: 直接編集は禁止です。"
                " 初期構築用コマンドと bootstrap_extra_commands のみ許可されます。"
            )
        return (
            "Controller-only bootstrap phase: 直接編集は禁止です。"
            " ai-dlc install/init-project/init-workspace/install-project-hooks と read-only コマンドのみ許可されます。"
        )
    return "AI-DLC workspace ではありません。"


def dispatch(cwd: Path) -> dict[str, Any]:
    payload = _load_payload()
    event_name = _extract_event_name(payload)
    workspace = _find_workspace(cwd)
    if event_name == "SessionStart":
        return _hook_output("SessionStart", _session_start_context(workspace) if workspace else _non_workspace_context(cwd))
    if event_name == "UserPromptSubmit":
        return _hook_output("UserPromptSubmit", _prompt_delta_context(workspace))
    if event_name in {"PostToolUse", "Stop"}:
        return _noop()
    if workspace is None:
        if _subagent_required_outside_workspace(cwd):
            tool = _extract_tool(payload)
            command = _extract_command(payload)
            if tool in EDIT_TOOLS:
                rel_paths = _extract_paths(payload, cwd)
                if not rel_paths:
                    return _block_hook(event_name, "Controller-only: edited paths could not be determined; delegate to a subagent.")
                if _all_paths_match(rel_paths, _bootstrap_edit_paths(cwd)):
                    return _allow_hook(event_name, "controller-only bootstrap edit allowed")
                return _block_hook(event_name, "Controller-only: direct edits are blocked outside AI-DLC; delegate to a subagent.")
            if tool == "Bash" and not _is_read_only_bash(command) and not _is_allowed_bootstrap_command(command, cwd):
                return _block_hook(event_name, "Controller-only: mutating Bash is blocked outside AI-DLC; delegate to a subagent.")
            return _allow_hook(event_name, "controller-only bootstrap phase")
        return _allow_hook(event_name, "not an AI-DLC workspace")

    tool = _extract_tool(payload)
    command = _extract_command(payload)
    if any(pattern in command for pattern in DESTRUCTIVE_GIT):
        return _block_hook(event_name, "AI-DLC: destructive git command requires explicit approval.")

    if tool == "Bash" and _is_write_like_bash(command) and os.environ.get("AI_DLC_ALLOW_CONTROLLER_EDIT") != "1":
        return _block_hook(event_name, "AI-DLC: write-like Bash commands are blocked; use apply_patch/Edit with a claimed lease.")
    if tool == "Bash" and command and not _is_read_only_bash(command):
        if "ai-dlc root-export" not in command and "ai-dlc overlay-cleanup" not in command and not _is_git_commit(command) and not _is_allowed_bootstrap_command(command, workspace):
            return _block_hook(event_name, "AI-DLC: unknown mutating Bash commands are denied by default in AI-DLC workspaces.")

    if tool in EDIT_TOOLS:
        rel_paths = _extract_paths(payload, workspace)
        if not rel_paths:
            return _block_hook(event_name, "AI-DLC: edited paths could not be determined.")

        if os.environ.get("AI_DLC_ALLOW_CONTROLLER_EDIT") == "1":
            return _allow_hook(event_name, "controller override enabled")

        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None:
            if _paths_match(rel_paths, CONTROLLER_ALLOWED_PATHS):
                return _block_hook(event_name, "AI-DLC: controller must delegate tracked plan or handoff edits to a claimed subagent.")
            return _block_hook(event_name, "AI-DLC: writable session requires a claimed lease.")

        assignment = load_assignment(workspace, lease["assignment_id"])
        if assignment.get("status") != "claimed":
            return _block_hook(event_name, "AI-DLC: assignment must be claimed before editing.")

        if lease.get("role") == "dlc_repo_worker":
            errors = bootstrap_gate_errors(workspace, lease)
            if errors:
                return _block_hook(event_name, f"AI-DLC: bootstrap gate failed: {'; '.join(errors)}")

        errors = lease_path_errors(workspace, lease, rel_paths)
        if errors:
            return _block_hook(event_name, f"AI-DLC: lease violation: {'; '.join(errors)}")

    if tool == "Bash" and "git commit" in command and " -C " not in f" {command} " and "AI_DLC_ALLOW_OVERLAY_BASELINE" not in command:
        workspace_data = read_data(workspace / "workspace.yaml")
        embedded = [name for name in workspace_data["repos"] if name != "root-system"]
        if embedded:
            return _block_hook(event_name, "AI-DLC: commit embedded repos from child repositories, not from root-system.")

    if tool == "Bash" and "ai-dlc root-export" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            return _block_hook(event_name, "AI-DLC: root-export requires a claimed git_operator lease.")

    if tool == "Bash" and "ai-dlc overlay-cleanup" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            return _block_hook(event_name, "AI-DLC: overlay-cleanup requires a claimed git_operator lease.")

    if tool == "Bash" and "git -C " in command and " commit" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            return _block_hook(event_name, "AI-DLC: child repo commit requires a claimed git_operator lease.")

    if tool == "Bash" and command.startswith("git -C "):
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease and lease.get("repo"):
            repo_prefix = f"git -C {lease['repo']}"
            if repo_prefix not in command:
                return _block_hook(event_name, f"AI-DLC: session lease only permits git -C {lease['repo']} commands.")

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
                return _block_hook(event_name, f"AI-DLC: next agent must be {expected} unless decisions explicitly allow {target_agent}.")
            if target_agent == "dlc_verifier" and _claimed_repo_worker_exists(workspace):
                return _block_hook(event_name, "AI-DLC: verifier must not run while a repo_worker assignment is still claimed.")

    return _allow_hook(event_name)
