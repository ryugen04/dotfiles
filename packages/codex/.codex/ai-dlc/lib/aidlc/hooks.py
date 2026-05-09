from __future__ import annotations

import ast
import fnmatch
import json
import os
import re
import shlex
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    tomllib = None  # type: ignore[assignment]

from .io import read_data, read_frontmatter, read_text
from .block_ledger import ACTION_TYPES, open_block_events_for, record_block_event, ref_allowed
from .state import assignment_root, bootstrap_gate_errors, lease_path_errors, load_assignment, load_lease
from .workflow_contracts import scoped_break_glass_allowed, stop_missing_obligation, workflow_type
from .workspace import ai_dlc_context, resolve_task_workspace

DESTRUCTIVE_GIT = ["git reset --hard", "git clean", "git push", "git merge", "git worktree remove", "rm -rf", "sango worktree remove"]
EDIT_TOOLS = {"apply_patch", "Edit", "Write", "MultiEdit"}
CONTROLLER_ALLOWED_PATHS = ["ai-dlc/plans/**", "ai-dlc/work-items/**", "ai-dlc/decisions/**", "ai-dlc/handoff/**", "ai-dlc/quality/**"]
DEFAULT_BOOTSTRAP_EDIT_PATHS = [".codex/config.toml", "AGENTS.md", "ai-dlc/**"]
GUARDRAIL_LIST_KEYS = {"bootstrap_edit_paths", "bootstrap_extra_commands"}
WRITE_LIKE_BASH_PATTERNS = ["sed -i", "perl -pi", "python -c", "python3 -c", "ruby -pi", "tee ", " cat > ", " > ", " >> "]
AGENT_TOOLS = {"spawn_agent", "send_input"}
READ_ONLY_BASH_COMMANDS = {"ls", "pwd", "cat", "find", "rg", "sed", "head", "tail", "wc", "sort", "uniq", "cut", "nl"}
PYTHON_VALIDATION_COMMANDS = {"python", "python3"}
PY_COMPILE_ALLOWED_PATH_PATTERNS = ("packages/codex/.codex/ai-dlc/lib/aidlc/*.py", "tests/test_aidlc.py")
UNITTEST_ALLOWED_MODULE = "tests.test_aidlc"
READ_ONLY_AIDLC_COMMANDS = {
    ("ai-dlc", "doctor"),
    ("ai-dlc", "status"),
    ("ai-dlc", "inspect"),
    ("ai-dlc", "context"),
    ("ai-dlc", "validate"),
    ("ai-dlc", "validate-overlay"),
    ("ai-dlc", "overlay-status"),
    ("ai-dlc", "deadlock-check"),
    ("ai-dlc", "clean-state-check"),
}
READ_ONLY_AIDLC_SUBCOMMANDS = {
    ("ai-dlc", "assignment", "list"),
    ("ai-dlc", "block-diagnose"),
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
READ_ONLY_GIT_SUBCOMMANDS = {"status", "diff", "rev-parse", "log", "show", "branch", "ls-files"}
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
GIT_FINISH_GIT_SUBCOMMANDS = {"add", "commit", "switch", "checkout", "push"}
GIT_FINISH_GH_SUBCOMMAND_PAIRS = {("pr", "create"), ("pr", "view"), ("pr", "status")}
INSTALL_APPROVAL_ENV = "AI_DLC_INSTALL_APPROVED"
DISALLOWED_SHELL_FRAGMENTS = ("`", "$(", "\n", "\r", ";", "&&", "||")
DISALLOWED_SHELL_TOKENS = {"|", "&", ">", ">>", "<", "<<", "<<<"}
SHELL_PUNCTUATION = set("();<>|&")
READ_ONLY_FIND_FORBIDDEN_PREFIXES = ("-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fls")
WORKSPACE_LESS_FORBIDDEN_WRITABLE_PREFIXES = (".git", ".codex", "ai-dlc")
WORKSPACE_LESS_FORBIDDEN_WRITABLES = {".", "*", "**", "workspace.yaml"}
WORKSPACE_LESS_BOOTSTRAP_ROLES = {"dlc_initializer", "dlc_repairer"}
WORKSPACE_LESS_BOOTSTRAP_WRITABLE = {
    "dlc_initializer": ["ai-dlc/bootstrap/**", "ai-dlc/overlay/**", "../.local/**", ".codex/config.toml", ".gitignore"],
    "dlc_repairer": ["ai-dlc/bootstrap/**", "ai-dlc/overlay/**", "ai-dlc/decisions/**", "../.local/**", ".codex/config.toml", ".gitignore"],
}
_LEDGER_CONTEXT: dict[str, Any] = {}
WORKING_DIRECTORY_KEYS = (
    "workdir",
    "cwd",
    "working_dir",
    "workingDirectory",
    "current_working_directory",
    "currentWorkingDirectory",
)
WORKSPACE_TARGET_OPTION_KEYS = {"--workspace", "--workspace-root"}


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


def _extract_prompt(payload: dict[str, Any]) -> str:
    for key in ["prompt", "user_prompt", "message"]:
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def _relativize(workspace: Path, value: str, base_cwd: Path | None = None) -> str | None:
    path = Path(value)
    if not path.is_absolute() and base_cwd is not None:
        path = base_cwd / path
    elif not path.is_absolute():
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


def _extract_raw_paths(payload: dict[str, Any]) -> list[str]:
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

    return raw_paths


def _extract_paths(payload: dict[str, Any], workspace: Path, base_cwd: Path | None = None) -> list[str]:
    raw_paths = _extract_raw_paths(payload)

    result: list[str] = []
    for raw_path in raw_paths:
        relative = _relativize(workspace, raw_path, base_cwd)
        if relative:
            result.append(relative)
    return sorted(set(result))


def _find_workspace_from_payload_paths(payload: dict[str, Any], base_cwd: Path) -> Path | None:
    workspaces: set[Path] = set()
    for raw_path in _extract_raw_paths(payload):
        path = Path(raw_path)
        if not path.is_absolute():
            path = base_cwd / path
        probe = path if path.is_dir() else path.parent
        for candidate in [probe, *probe.parents]:
            if (candidate / "workspace.yaml").exists():
                try:
                    workspaces.add(candidate.resolve())
                except Exception:
                    workspaces.add(candidate)
                break
    if len(workspaces) == 1:
        return next(iter(workspaces))
    return None


def _paths_match(paths: list[str], patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for path in paths for pattern in patterns)


def _allow(reason: str = "ok") -> dict[str, str]:
    return {"decision": "allow", "reason": reason}


def _block(reason: str) -> dict[str, str]:
    return {"decision": "block", "reason": reason}


def _noop() -> dict[str, Any]:
    return {}


def _block_diagnosis(
    block_type: str,
    route: str,
    actions: list[str],
    reason: str,
    *,
    recoverable: bool = True,
    suggested_agent: str = "",
    requires_user_approval: bool = False,
) -> dict[str, Any]:
    return {
        "block_type": block_type,
        "recoverable": recoverable,
        "suggested_route": route,
        "suggested_agent": suggested_agent,
        "allowed_next_actions": actions,
        "requires_user_approval": requires_user_approval,
        "reason": reason,
    }


def _parse_block_reason(message: str) -> dict[str, Any] | None:
    if not message.startswith("AI-DLC_BLOCK "):
        return None
    header, _, reason = message.partition(" :: ")
    parsed: dict[str, Any] = {
        "block_type": "unknown",
        "recoverable": True,
        "suggested_route": "inspect_block",
        "suggested_agent": "",
        "allowed_next_actions": [],
        "requires_user_approval": False,
        "reason": reason or message,
    }
    for token in header.split()[1:]:
        key, _, value = token.partition("=")
        if not key or not value:
            continue
        if key == "type":
            parsed["block_type"] = value
        elif key == "recoverable":
            parsed["recoverable"] = value == "true"
        elif key == "route":
            parsed["suggested_route"] = value
        elif key == "approval":
            parsed["requires_user_approval"] = value == "true"
        elif key == "agent":
            parsed["suggested_agent"] = "" if value == "-" else value
        elif key == "actions":
            parsed["allowed_next_actions"] = [] if value == "-" else value.split("|")
    return parsed


def _format_block_reason(diagnosis: dict[str, Any]) -> str:
    actions = diagnosis.get("allowed_next_actions") or []
    action_text = "|".join(str(action) for action in actions) if actions else "-"
    agent = str(diagnosis.get("suggested_agent") or "-")
    fields = [
        f"type={diagnosis.get('block_type', 'unknown')}",
        f"recoverable={str(bool(diagnosis.get('recoverable', True))).lower()}",
        f"route={diagnosis.get('suggested_route', 'inspect_block')}",
        f"approval={str(bool(diagnosis.get('requires_user_approval', False))).lower()}",
        f"agent={agent}",
        f"actions={action_text}",
    ]
    return f"AI-DLC_BLOCK {' '.join(fields)} :: {diagnosis.get('reason', '')}"


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
        return {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {"behavior": "allow"},
            }
        }
    if event_name in {"PostToolUse", "Stop"}:
        return _noop()
    return _allow(reason)


def _block_hook(event_name: str, reason: str, diagnosis: dict[str, Any] | None = None) -> dict[str, Any]:
    if diagnosis is not None:
        reason = _format_block_reason(diagnosis)
        if event_name in {"PreToolUse", "PermissionRequest", "Stop"} and diagnosis.get("block_type") != "open_blockers":
            payload = _LEDGER_CONTEXT.get("payload")
            effective_cwd = _LEDGER_CONTEXT.get("effective_cwd")
            workspace = _LEDGER_CONTEXT.get("workspace")
            if isinstance(payload, dict) and isinstance(effective_cwd, Path):
                try:
                    record_block_event(
                        payload=payload,
                        event_name=event_name,
                        effective_cwd=effective_cwd,
                        workspace=workspace if isinstance(workspace, Path) else None,
                        diagnosis=diagnosis,
                        reason=reason,
                    )
                except Exception:
                    pass
    if event_name == "PreToolUse":
        output = _block(reason)
        output["hookSpecificOutput"] = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
        return output
    if event_name == "PermissionRequest":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {"behavior": "deny", "message": reason},
            }
        }
    if event_name == "PostToolUse":
        return _noop()
    if event_name == "Stop":
        return {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "decision": "block",
                "reason": reason,
            }
        }
    return _block(reason)


def _safe_shell_tokens(command: str, *, allow_pipe: bool = False) -> list[str]:
    normalized = command.strip()
    if not normalized:
        return []
    if any(fragment in normalized for fragment in DISALLOWED_SHELL_FRAGMENTS):
        return []
    try:
        lexer = shlex.shlex(normalized, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []
    if not tokens:
        return []
    for token in tokens:
        if token == "|" and allow_pipe:
            continue
        if token in DISALLOWED_SHELL_TOKENS:
            return []
        if set(token).issubset(SHELL_PUNCTUATION):
            return []
    return tokens


def _safe_tokens(command: str) -> list[str]:
    tokens = _safe_shell_tokens(command)
    if any(token == "|" for token in tokens):
        return []
    return tokens


def _project_relative_path(cwd: Path, value: str) -> str | None:
    if not value or value.startswith("-"):
        return None
    config_path = _find_codex_config(cwd)
    if config_path is None:
        return None
    project_root = config_path.parent.parent
    path = Path(value)
    candidate = path if path.is_absolute() else cwd / path
    try:
        return candidate.resolve().relative_to(project_root.resolve()).as_posix()
    except Exception:
        return None


def _is_allowed_py_compile_target(cwd: Path, value: str) -> bool:
    relative = _project_relative_path(cwd, value)
    if relative is None:
        return False
    return any(Path(relative).match(pattern) for pattern in PY_COMPILE_ALLOWED_PATH_PATTERNS)


def _is_allowed_project_validation_command(command: str, cwd: Path) -> bool:
    tokens = _safe_tokens(command)
    if not tokens or tokens[0] not in PYTHON_VALIDATION_COMMANDS:
        return False
    if tokens[1:3] == ["-m", "py_compile"]:
        targets = tokens[3:]
        return bool(targets) and all(_is_allowed_py_compile_target(cwd, target) for target in targets)
    if tokens[1:3] != ["-m", "unittest"]:
        return False
    targets = tokens[3:]
    if targets and all(target == UNITTEST_ALLOWED_MODULE or target.startswith(f"{UNITTEST_ALLOWED_MODULE}.") for target in targets):
        return True
    if len(tokens) == 6 and tokens[3] == "-k" and tokens[5] == UNITTEST_ALLOWED_MODULE:
        pattern = tokens[4]
        return bool(re.match(r"^[A-Za-z0-9_.:-]+$", pattern))
    return False


def _pipeline_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token == "|":
            if not current:
                return []
            segments.append(current)
            current = []
        else:
            current.append(token)
    if not current:
        return []
    segments.append(current)
    return segments


def _strip_leading_env(tokens: list[str]) -> tuple[dict[str, str], list[str]]:
    env: dict[str, str] = {}
    index = 0
    for token in tokens:
        if "=" not in token or token.startswith("-"):
            break
        key, value = token.split("=", 1)
        if not key or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            break
        env[key] = value
        index += 1
    return env, tokens[index:]


def _is_git_finish_approved_command(command: str) -> bool:
    tokens = _safe_tokens(command)
    env, command_tokens = _strip_leading_env(tokens)
    if env.get("AI_DLC_GIT_FINISH_APPROVED") != "1":
        return False
    if not command_tokens:
        return False
    if command_tokens[0] == "git":
        if len(command_tokens) >= 4 and command_tokens[1] == "-C":
            subcommand = command_tokens[3]
        elif len(command_tokens) >= 2:
            subcommand = command_tokens[1]
        else:
            return False
        if subcommand in {"reset", "clean"}:
            return False
        return subcommand in GIT_FINISH_GIT_SUBCOMMANDS
    if command_tokens[0] == "gh":
        if len(command_tokens) >= 3:
            return (command_tokens[1], command_tokens[2]) in GIT_FINISH_GH_SUBCOMMAND_PAIRS
    return False


def _is_known_read_only_candidate(command: str) -> bool:
    _, tokens = _strip_leading_env(_safe_tokens(command))
    if not tokens:
        return False
    if tokens[0] in READ_ONLY_BASH_COMMANDS:
        return True
    if tokens[0] == "gh":
        return _is_read_only_gh(tokens)
    if tokens[0] == "git":
        return _is_read_only_git(tokens)
    if tokens[0] == "ai-dlc":
        return _is_read_only_aidlc(tokens)
    return False


def diagnose_block(cwd: Path, event_name: str = "", tool: str = "", command: str = "", message: str = "") -> dict[str, Any]:
    parsed = _parse_block_reason(message)
    if parsed is not None:
        return parsed

    lowered = message.lower()
    reason = message or "Hook/tool block requires recovery."
    expected_match = re.search(r"next agent must be ([a-z0-9_]+)", message)

    if any(pattern in command for pattern in DESTRUCTIVE_GIT) or "destructive" in lowered:
        return _block_diagnosis(
            "destructive_forbidden",
            "stop_for_user",
            ["collect_read_only_evidence", "ask_explicit_user_approval"],
            reason,
            recoverable=False,
            requires_user_approval=True,
        )
    if expected_match:
        return _block_diagnosis(
            "wrong_next_agent",
            "delegate_phase_owner",
            ["inspect_current_phase", "create_assignment", "delegate_to_subagent", "report_delegation_deadlock"],
            reason,
            suggested_agent=expected_match.group(1),
        )
    if "bootstrap/delegation deadlock" in lowered:
        return _block_diagnosis(
            "needs_assignment",
            "delegate_phase_owner",
            ["report_delegation_deadlock"],
            reason,
            recoverable=False,
            suggested_agent="phase_owner",
        )
    if "workspace.yaml not found" in lowered or "workspace ではありません" in message or "task workspace" in lowered:
        return _block_diagnosis(
            "missing_workspace",
            "locate_or_bootstrap_workspace",
            ["run_read_only_status", "locate_workspace_yaml", "use_workflow_bootstrap"],
            reason,
        )
    if "schema" in lowered or "could not be determined" in lowered:
        return _block_diagnosis(
            "hook_schema_error",
            "repair_hook_config",
            ["inspect_hook_payload", "retry_with_explicit_paths", "run_runtime_probe"],
            reason,
        )
    if "requires explicit approval" in lowered or "requires user approval" in lowered:
        return _block_diagnosis(
            "approval_required",
            "request_approval",
            ["request_user_approval", "document_approval_gate"],
            reason,
            requires_user_approval=True,
        )
    if "mutating bash" in lowered:
        if command and _is_known_read_only_candidate(command):
            return _block_diagnosis(
                "read_only_false_positive",
                "retry_read_only",
                ["retry_command", "extend_read_only_allowlist", "add_regression_test"],
                reason,
            )
        if "install.sh" in command:
            return _block_diagnosis(
                "approval_required",
                "request_approval",
                ["use_dry_run", "request_user_approval", f"retry_with_{INSTALL_APPROVAL_ENV}=1"],
                reason,
                requires_user_approval=True,
            )
        return _block_diagnosis(
            "needs_assignment",
            "delegate_phase_owner",
            ["inspect_current_phase", "create_assignment", "delegate_to_subagent", "report_delegation_deadlock"],
            reason,
            suggested_agent="phase_owner",
        )
    if "claimed lease" in lowered or "delegate to a subagent" in lowered or "requires a claimed" in lowered:
        return _block_diagnosis(
            "needs_assignment",
            "delegate_phase_owner",
            ["inspect_current_phase", "create_assignment", "delegate_to_subagent", "report_delegation_deadlock"],
            reason,
            suggested_agent="phase_owner",
        )
    if "bootstrap" in lowered:
        return _block_diagnosis(
            "bootstrap_config_gap",
            "repair_hook_config",
            ["inspect_guardrails", "update_bootstrap_edit_paths", "run_dry_run"],
            reason,
        )
    return _block_diagnosis(
        "unknown",
        "inspect_block",
        ["inspect_payload", "classify_block", "report_to_user"],
        reason,
        recoverable=False,
    )


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


def _guardrail_config_paths(start: Path) -> list[Path]:
    candidates = [Path.home() / ".codex" / "config.toml"]
    project_config = _find_codex_config(start)
    if project_config is not None:
        candidates.append(project_config)

    paths: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if not path.exists():
            continue
        try:
            resolved = path.resolve()
        except Exception:
            resolved = path
        if resolved in seen:
            continue
        seen.add(resolved)
        paths.append(path)
    return paths


def _strip_toml_comment(line: str) -> str:
    quote = ""
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote:
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = ""
            elif not quote:
                quote = char
            continue
        if char == "#" and not quote:
            return line[:index]
    return line


def _parse_guardrail_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, str)]
    return value.strip("\"'")


def _parse_guardrails_fallback(text: str) -> dict[str, Any]:
    in_guardrails = False
    pending_key = ""
    pending_lines: list[str] = []
    guardrails: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = _strip_toml_comment(raw_line).strip()
        if not line:
            continue
        if pending_key:
            pending_lines.append(line)
            if line.endswith("]"):
                guardrails[pending_key] = _parse_guardrail_value(" ".join(pending_lines))
                pending_key = ""
                pending_lines = []
            continue
        if line.startswith("[") and line.endswith("]"):
            in_guardrails = line == "[guardrails]"
            continue
        if not in_guardrails or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if value == "[":
            pending_key = key
            pending_lines = [value]
            continue
        guardrails[key] = _parse_guardrail_value(value)
    return guardrails


def _read_guardrails(config_path: Path) -> dict[str, Any]:
    try:
        text = read_text(config_path)
    except Exception:
        return {}
    if tomllib is None:
        return _parse_guardrails_fallback(text)
    try:
        data = tomllib.loads(text)
    except Exception:
        return {}
    guardrails = data.get("guardrails")
    if isinstance(guardrails, dict):
        return guardrails
    return {}


def _load_guardrails(start: Path) -> dict[str, Any]:
    guardrails: dict[str, Any] = {}
    for config_path in _guardrail_config_paths(start):
        for key, value in _read_guardrails(config_path).items():
            if key in GUARDRAIL_LIST_KEYS and isinstance(value, list):
                existing = guardrails.get(key)
                merged = existing if isinstance(existing, list) else []
                guardrails[key] = [*merged, *value]
            else:
                guardrails[key] = value
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


def _is_read_only_codex_runtime_probe(tokens: list[str]) -> bool:
    return tokens in (
        ["which", "codex"],
        ["command", "-v", "codex"],
        ["codex", "--version"],
        ["codex", "-V"],
        ["codex", "--help"],
    )


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


def _git_args(tokens: list[str]) -> list[str]:
    if not tokens or tokens[0] != "git":
        return []
    if len(tokens) >= 4 and tokens[1] == "-C":
        return tokens[3:]
    return tokens[1:]


def _is_read_only_git(tokens: list[str]) -> bool:
    args = _git_args(tokens)
    if not args:
        return False
    subcommand = args[0]
    if subcommand == "worktree":
        return len(args) == 2 and args[1] == "list"
    if subcommand == "remote":
        return args == ["remote", "-v"] or args == ["remote", "get-url", "origin"]
    return subcommand in READ_ONLY_GIT_SUBCOMMANDS


def _is_read_only_aidlc_block(tokens: list[str]) -> bool:
    if len(tokens) < 3 or tokens[:2] != ["ai-dlc", "block"]:
        return False
    subcommand = tokens[2]
    flags = tokens[3:]
    if subcommand == "list":
        return all(flag in {"--json", "--all"} for flag in flags)
    if subcommand == "actions":
        return all(flag == "--json" for flag in flags)
    return False


def _option_value(tokens: list[str], option: str) -> str:
    for index, token in enumerate(tokens):
        if token == option and index + 1 < len(tokens):
            return tokens[index + 1]
        if token.startswith(f"{option}="):
            return token.split("=", 1)[1]
    return ""


def _strip_workspace_target_tokens(tokens: list[str]) -> list[str]:
    stripped: list[str] = []
    skip_next = False
    for index, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if token in WORKSPACE_TARGET_OPTION_KEYS:
            if index + 1 < len(tokens):
                skip_next = True
            continue
        if any(token.startswith(f"{key}=") for key in WORKSPACE_TARGET_OPTION_KEYS):
            continue
        stripped.append(token)
    return stripped


def _command_target_workspace(command: str, fallback: Path) -> Path | None:
    tokens = _safe_tokens(command)
    if not tokens or tokens[0] != "ai-dlc":
        return None
    workspace = _option_value(tokens, "--workspace")
    workspace_root = _option_value(tokens, "--workspace-root")
    if not workspace and not workspace_root:
        return None
    return resolve_task_workspace(fallback, workspace=workspace, workspace_root=workspace_root)


def _is_safe_aidlc_command(command: str) -> bool:
    tokens = _safe_tokens(command)
    if not tokens:
        return False
    return tokens[0] == "ai-dlc"


def _is_read_only_aidlc(tokens: list[str]) -> bool:
    if not tokens or tokens[0] != "ai-dlc":
        return False
    tokens = _strip_workspace_target_tokens(tokens)
    if any(token in {"-h", "--help"} for token in tokens[1:]):
        return True
    if _is_read_only_aidlc_block(tokens):
        return True
    if len(tokens) >= 3 and tuple(tokens[:3]) in READ_ONLY_AIDLC_SUBCOMMANDS:
        return True
    if len(tokens) >= 2 and tuple(tokens[:2]) in READ_ONLY_AIDLC_SUBCOMMANDS:
        return True
    return len(tokens) >= 2 and (tokens[0], tokens[1]) in READ_ONLY_AIDLC_COMMANDS


def _parse_long_options(tokens: list[str]) -> tuple[dict[str, list[str]], list[str]] | None:
    options: dict[str, list[str]] = {}
    positionals: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("--"):
            key, separator, value = token.partition("=")
            if not key or key == "--":
                return None
            if separator:
                options.setdefault(key, []).append(value)
            elif index + 1 < len(tokens) and not tokens[index + 1].startswith("--"):
                options.setdefault(key, []).append(tokens[index + 1])
                index += 1
            else:
                options.setdefault(key, []).append("")
        elif token.startswith("-"):
            return None
        else:
            positionals.append(token)
        index += 1
    return options, positionals


def _single_option(options: dict[str, list[str]], name: str, default: str = "") -> str | None:
    values = options.get(name)
    if values is None:
        return default
    if len(values) != 1:
        return None
    return values[0]


def _has_only_options(options: dict[str, list[str]], allowed: set[str]) -> bool:
    return set(options).issubset(allowed)


def _event_id_looks_safe(event_id: str) -> bool:
    return bool(re.match(r"^B[A-Za-z0-9TtZz_-]{8,}$", event_id))


def _is_allowed_block_record(tokens: list[str]) -> bool:
    parsed = _parse_long_options(tokens[3:])
    if parsed is None:
        return False
    options, positionals = parsed
    if positionals or not _has_only_options(options, {"--event-id", "--type", "--ref", "--reason"}):
        return False
    event_id = _single_option(options, "--event-id")
    action_type = _single_option(options, "--type", "durable_record")
    ref = _single_option(options, "--ref")
    reason = _single_option(options, "--reason", "")
    if event_id is None or action_type is None or ref is None or reason is None:
        return False
    if not event_id or not _event_id_looks_safe(event_id):
        return False
    if action_type not in ACTION_TYPES:
        return False
    if action_type == "deferred_by_user" and not reason:
        return False
    return ref_allowed(ref)


def _is_allowed_block_export(tokens: list[str]) -> bool:
    parsed = _parse_long_options(tokens[3:])
    if parsed is None:
        return False
    options, positionals = parsed
    if positionals or not _has_only_options(options, {"--event-id", "--plan"}):
        return False
    event_id = _single_option(options, "--event-id")
    plan = _single_option(options, "--plan")
    if event_id is None or plan is None:
        return False
    if not event_id or not _event_id_looks_safe(event_id):
        return False
    if plan.startswith(("http://", "https://")) or Path(plan).suffix.lower() not in {".md", ".markdown"}:
        return False
    return ref_allowed(plan)


def _is_allowed_block_recovery_command(tokens: list[str]) -> bool:
    if len(tokens) < 3 or tokens[:2] != ["ai-dlc", "block"]:
        return False
    subcommand = tokens[2]
    if subcommand == "record":
        return _is_allowed_block_record(tokens)
    if subcommand == "sync":
        return len(tokens) == 3
    if subcommand == "export":
        return _is_allowed_block_export(tokens)
    return False


def _workspace_less_assignment_for_command(cwd: Path, assignment_id: str, allowed_statuses: set[str]) -> dict[str, Any] | None:
    if not re.match(r"^A\d{3}$", assignment_id):
        return None
    try:
        assignment = load_assignment(cwd, assignment_id)
    except Exception:
        return None
    if not assignment.get("workspace_less"):
        return None
    if str(assignment.get("status")) not in allowed_statuses:
        return None
    return assignment


def _workspace_less_lifecycle_lease_matches(cwd: Path, assignment_id: str, session_id: str = "") -> bool:
    try:
        explicit_session_id = session_id or os.environ.get("CODEX_SESSION_ID") or ""
        if explicit_session_id:
            lease_path = assignment_root(cwd) / "leases" / f"{explicit_session_id}.json"
            if not lease_path.exists():
                return False
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
        else:
            lease = load_lease(cwd, None)
    except Exception:
        return False
    return bool(
        lease
        and lease.get("workspace_less")
        and lease.get("assignment_id") == assignment_id
        and lease.get("status") == "claimed"
    )


def _is_allowed_workspace_less_agent_claim(tokens: list[str], cwd: Path) -> bool:
    parsed = _parse_long_options(tokens[2:])
    if parsed is None:
        return False
    options, positionals = parsed
    if positionals or not _has_only_options(options, {"--assignment", "--session-id"}):
        return False
    assignment_id = _single_option(options, "--assignment")
    session_id = _single_option(options, "--session-id", "")
    if assignment_id is None or session_id is None:
        return False
    return _workspace_less_assignment_for_command(cwd, assignment_id, {"created", "accepted"}) is not None


def _is_allowed_workspace_less_agent_report(tokens: list[str], cwd: Path) -> bool:
    parsed = _parse_long_options(tokens[2:])
    if parsed is None:
        return False
    options, positionals = parsed
    if positionals or not _has_only_options(options, {"--assignment", "--status", "--report"}):
        return False
    assignment_id = _single_option(options, "--assignment")
    status = _single_option(options, "--status")
    report = _single_option(options, "--report", "")
    if assignment_id is None or status is None or report is None:
        return False
    if status not in {"reported", "blocked", "failed", "cancelled"}:
        return False
    if _workspace_less_assignment_for_command(cwd, assignment_id, {"claimed", "reported", "blocked", "failed", "cancelled"}) is None:
        return False
    return _workspace_less_lifecycle_lease_matches(cwd, assignment_id)


def _is_allowed_workspace_less_agent_release(tokens: list[str], cwd: Path) -> bool:
    parsed = _parse_long_options(tokens[2:])
    if parsed is None:
        return False
    options, positionals = parsed
    if positionals or not _has_only_options(options, {"--assignment", "--session-id"}):
        return False
    assignment_id = _single_option(options, "--assignment")
    session_id = _single_option(options, "--session-id", "")
    if assignment_id is None or session_id is None:
        return False
    if _workspace_less_assignment_for_command(cwd, assignment_id, {"claimed", "reported", "blocked", "failed", "cancelled"}) is None:
        return False
    return _workspace_less_lifecycle_lease_matches(cwd, assignment_id, session_id)


def _is_allowed_workspace_less_lifecycle_command(tokens: list[str], cwd: Path) -> bool:
    if len(tokens) < 2 or tokens[0] != "ai-dlc":
        return False
    if tokens[1] == "agent-claim":
        return _is_allowed_workspace_less_agent_claim(tokens, cwd)
    if tokens[1] == "agent-report":
        return _is_allowed_workspace_less_agent_report(tokens, cwd)
    if tokens[1] == "agent-release":
        return _is_allowed_workspace_less_agent_release(tokens, cwd)
    return False


def _workspace_less_assignment_options(tokens: list[str]) -> dict[str, Any] | None:
    if tokens[:3] != ["ai-dlc", "assignment", "create"]:
        return None

    options: dict[str, Any] = {"role": None, "repo": None, "work_item": None, "writable": []}
    index = 3
    while index < len(tokens):
        token = tokens[index]
        if token in {"-h", "--help"}:
            return None
        if token == "--role" and index + 1 < len(tokens):
            options["role"] = tokens[index + 1]
            index += 2
            continue
        if token == "--repo" and index + 1 < len(tokens):
            options["repo"] = tokens[index + 1]
            index += 2
            continue
        if token == "--work-item" and index + 1 < len(tokens):
            options["work_item"] = tokens[index + 1]
            index += 2
            continue
        if token == "--writable" and index + 1 < len(tokens):
            options["writable"].append(tokens[index + 1])
            index += 2
            continue
        return None
    return options


def _is_workspace_less_writable_path_safe(path: str) -> bool:
    normalized = path.strip().strip("/")
    if not normalized or path.strip() in WORKSPACE_LESS_FORBIDDEN_WRITABLES:
        return False
    if path.startswith("/") or normalized.startswith("../") or "/../" in normalized:
        return False
    if normalized in WORKSPACE_LESS_FORBIDDEN_WRITABLES:
        return False
    if normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    for prefix in WORKSPACE_LESS_FORBIDDEN_WRITABLE_PREFIXES:
        if normalized == prefix or normalized.startswith(f"{prefix}/"):
            return False
    return True


def _workspace_less_bootstrap_writable_path_safe(role: str, path: str) -> bool:
    normalized = path.strip().rstrip("/")
    if not normalized or normalized in WORKSPACE_LESS_FORBIDDEN_WRITABLES:
        return False
    if normalized.startswith("/") or normalized == ".." or (normalized.startswith("../") and not normalized.startswith("../.local/")):
        return False
    allowed = WORKSPACE_LESS_BOOTSTRAP_WRITABLE.get(role, [])
    return any(fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(f"{normalized}/", pattern) for pattern in allowed)


def _is_allowed_workspace_less_assignment_create(tokens: list[str]) -> bool:
    options = _workspace_less_assignment_options(tokens)
    if options is None:
        return False
    role = options["role"]
    writable = options["writable"]
    if role in WORKSPACE_LESS_BOOTSTRAP_ROLES:
        if options["repo"] or options["work_item"] or not writable:
            return False
        return all(_workspace_less_bootstrap_writable_path_safe(role, path) for path in writable)
    if role != "dlc_repo_worker":
        return False
    if not options["repo"] or not options["work_item"]:
        return False
    if not writable:
        return False
    return all(_is_workspace_less_writable_path_safe(path) for path in writable)


def _repo_install_script() -> Path:
    return Path(__file__).resolve().parents[6] / "install.sh"


def _is_install_sh_command(tokens: list[str], cwd: Path) -> bool:
    if not tokens or Path(tokens[0]).name != "install.sh":
        return False
    script = Path(tokens[0])
    if not script.is_absolute():
        script = cwd / script
    try:
        return script.resolve() == _repo_install_script().resolve()
    except Exception:
        return False


def _is_install_sh_dry_run(tokens: list[str], cwd: Path) -> bool:
    if not _is_install_sh_command(tokens, cwd):
        return False
    dry_run = False
    for token in tokens[1:]:
        if token in {"-n", "--dry-run"}:
            dry_run = True
            continue
        if token in {"-v", "--verbose"}:
            continue
        if token.startswith("-"):
            return False
    return dry_run


def _canonical_bootstrap_tokens(tokens: list[str], cwd: Path) -> list[str]:
    if _is_install_sh_command(tokens, cwd):
        return [str(_repo_install_script().resolve()), *tokens[1:]]
    return tokens


def _matches_bootstrap_extra_command(tokens: list[str], cwd: Path) -> bool:
    expected = _canonical_bootstrap_tokens(tokens, cwd)
    for configured in _bootstrap_extra_commands(cwd):
        configured_tokens = _safe_tokens(configured)
        if not configured_tokens:
            continue
        if _canonical_bootstrap_tokens(configured_tokens, cwd) == expected:
            return True
    return False


def _is_read_only_tokens(tokens: list[str]) -> bool:
    if tokens[0] == "ai-dlc":
        return _is_read_only_aidlc(tokens)
    if _is_read_only_codex_runtime_probe(tokens):
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
    if command_name == "git":
        return _is_read_only_git(tokens)
    return False


def _is_read_only_bash(command: str) -> bool:
    normalized = command.strip()
    if not normalized:
        return True
    tokens = _safe_shell_tokens(normalized, allow_pipe=True)
    if not tokens:
        return False
    segments = _pipeline_segments(tokens)
    if not segments:
        return False
    return all(_is_read_only_tokens(segment) for segment in segments)


def _is_allowed_bootstrap_command(command: str, cwd: Path) -> bool:
    normalized = command.strip()
    if not normalized:
        return False
    tokens = _safe_tokens(normalized)
    if not tokens:
        return False
    env, command_tokens = _strip_leading_env(tokens)
    if not command_tokens:
        return False
    if command_tokens[0] == "ai-dlc":
        if len(command_tokens) >= 2 and command_tokens[1] == "ensure-context":
            return True
        if len(command_tokens) >= 2 and (command_tokens[0], command_tokens[1]) in BOOTSTRAP_AIDLC_COMMANDS:
            return True
        if _is_allowed_block_recovery_command(command_tokens):
            return True
        if _is_allowed_workspace_less_lifecycle_command(command_tokens, cwd):
            return True
        return _is_allowed_workspace_less_assignment_create(command_tokens)
    if len(command_tokens) >= 3 and command_tokens[0] == "sango" and command_tokens[1] == "worktree":
        return command_tokens[2] in {"create", "list", "status"}
    if len(command_tokens) >= 2 and (command_tokens[0], command_tokens[1]) in BOOTSTRAP_AIDLC_COMMANDS:
        return True
    if _is_install_sh_dry_run(command_tokens, cwd):
        return True
    if _matches_bootstrap_extra_command(command_tokens, cwd):
        if _is_install_sh_command(command_tokens, cwd):
            return env.get(INSTALL_APPROVAL_ENV) == "1"
        return True
    return False


def _cwd_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _resolve_cwd_value(value: str, fallback: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (fallback / path).resolve()


def _extract_effective_cwd(payload: dict[str, Any], fallback: Path) -> Path:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in WORKING_DIRECTORY_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return _resolve_cwd_value(value, fallback)
        nested = tool_input.get("command")
        if isinstance(nested, dict):
            for key in WORKING_DIRECTORY_KEYS:
                value = nested.get(key)
                if isinstance(value, str) and value:
                    return _resolve_cwd_value(value, fallback)

    for key in WORKING_DIRECTORY_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return _resolve_cwd_value(value, fallback)

    return fallback


def _is_allowed_verifier_gate_command(workspace: Path, cwd: Path, command: str) -> bool:
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

    session_id = os.environ.get("CODEX_SESSION_ID")
    lease = load_lease(workspace, session_id)
    if lease is None:
        return False
    if lease.get("role") not in {"dlc_verifier", "dlc_repo_worker"}:
        return False

    assignment = load_assignment(workspace, lease["assignment_id"])
    if assignment.get("status") != "claimed":
        return False

    active_item_id = lease.get("active_item")
    if not active_item_id:
        return False

    work_items_data = read_data(workspace / read_data(workspace / "workspace.yaml")["paths"]["work_items"])
    target_item = next((item for item in work_items_data["items"] if item["id"] == active_item_id), None)
    if target_item is None:
        return False

    verifier_gate = target_item.get("verifier_gate")
    if not verifier_gate:
        return False

    for req in verifier_gate.get("required_commands", []):
        req_cwd = req.get("cwd", ".")
        expected_cwd = workspace / req_cwd if req_cwd != "." else workspace
        if not (_cwd_is_within(cwd, expected_cwd) or cwd.resolve() == workspace.resolve()):
            continue
        try:
            req_tokens = shlex.split(req.get("command", ""))
        except ValueError:
            continue
        if tokens == req_tokens:
            return True

    return False


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


def _prompt_safety_context(payload: dict[str, Any]) -> str:
    prompt = _extract_prompt(payload)
    if "AI_DLC_SAFETY_DOMAIN=codex_config_edit" in prompt:
        return "Workflow safety_domain: codex_config_edit"
    return ""


def _prompt_workspace_less_assignment_context(cwd: Path, payload: dict[str, Any], workspace: Path | None) -> str:
    if workspace is not None:
        return ""
    prompt = _extract_prompt(payload)
    match = re.search(r"\bA\d{3}\b", prompt)
    if not match:
        return ""
    assignment_id = match.group(0)
    try:
        assignment = load_assignment(cwd, assignment_id)
    except Exception:
        return ""
    if not assignment.get("workspace_less"):
        return ""
    role = str(assignment.get("role"))
    session_id = _extract_session_id(payload) or "$CODEX_SESSION_ID"
    writable = ", ".join(str(path) for path in assignment.get("writable", [])) or "(none)"
    forbidden = ", ".join(str(path) for path in assignment.get("forbidden", [])) or "(none)"
    return (
        f"Workspace-less {role} assignment: {assignment_id}\n"
        f"Claim first: ai-dlc agent-claim --assignment {assignment_id} --session-id {session_id}\n"
        f"After claim, lease-scoped edits are allowed only for writable paths: {writable}\n"
        f"Forbidden paths: {forbidden}\n"
        f"The controller-only direct edit ban applies before claim and to controller sessions, not to a claimed {role} lease."
    )


def _non_workspace_context(cwd: Path) -> str:
    project_root = _find_project_root(cwd)
    if project_root is not None:
        context = ai_dlc_context(cwd)
        discoverable = context.get("discoverable_workspaces") or []
        workspace_lines = []
        for item in discoverable[:5]:
            if isinstance(item, dict):
                workspace_lines.append(f"- {item.get('id', '')}: {item.get('path', item.get('root', ''))}")
        workspace_hint = ""
        if workspace_lines:
            workspace_hint = (
                " 発見済み task workspaces:\n"
                + "\n".join(workspace_lines)
                + "\n`ai-dlc status --workspace <id>` または `ai-dlc assignment create --workspace <id> ...` を使えます。"
            )
        return (
            "AI-DLC root-system projectです。task workspaceではありません。"
            + workspace_hint
            + " 対象 worktree の workspace.yaml がある場所へ移動するか、workflow-bootstrap で既存 worktree を採用してください。"
            " 直接編集は禁止です。"
        )
    if _subagent_required_outside_workspace(cwd):
        extras = _bootstrap_extra_commands(cwd)
        if extras:
            return (
                "Controller-only bootstrap phase: controller の直接編集は禁止です。"
                " 初期構築用コマンド、bootstrap_extra_commands、bootstrap_edit_paths の編集のみ許可されます。"
                " workspace-less assignments は claim 後に role ごとの lease-scoped paths だけ編集できます。"
            )
        return (
            "Controller-only bootstrap phase: controller の直接編集は禁止です。"
            " ai-dlc install/init-project/init-workspace/install-project-hooks、bootstrap_edit_paths の編集、read-only コマンドのみ許可されます。"
            " workspace-less assignments は claim 後に role ごとの lease-scoped paths だけ編集できます。"
        )
    return (
        "AI-DLC workspace ではありません。"
        " Project-local AI-DLC 設定を推奨します。"
        " 未設定のまま進める場合は Codex user-local fallback として `ai-dlc ensure-context` を使えます。"
    )


def _extract_session_id(payload: dict[str, Any]) -> str:
    for key in ["session_id", "sessionId"]:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CODEX_SESSION_ID") or ""


def _workspace_less_lease(cwd: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
    session_id = _extract_session_id(payload)
    try:
        lease = load_lease(cwd, session_id or None)
    except Exception:
        return None
    if not lease or not lease.get("workspace_less"):
        return None
    return lease


def _workspace_less_edit_block(cwd: Path, payload: dict[str, Any], event_name: str, tool: str, command: str, rel_paths: list[str]) -> dict[str, Any] | None:
    lease = _workspace_less_lease(cwd, payload)
    if lease is None:
        return None
    try:
        assignment = load_assignment(cwd, lease["assignment_id"])
    except Exception as exc:
        reason = f"Controller-only: workspace-less assignment could not be loaded: {exc}"
        return _block_hook(event_name, reason, diagnose_block(cwd, event_name, tool, command, reason))
    if assignment.get("status") != "claimed":
        reason = "Controller-only: workspace-less assignment must be claimed before editing."
        return _block_hook(event_name, reason, diagnose_block(cwd, event_name, tool, command, reason))
    role_phase = {"dlc_repo_worker": "executing", "dlc_initializer": "initializing", "dlc_repairer": "repairing"}
    expected_phase = role_phase.get(str(lease.get("role")))
    if expected_phase is None:
        reason = "Controller-only: workspace-less assignment role is not lease-editable."
        return _block_hook(event_name, reason, diagnose_block(cwd, event_name, tool, command, reason))
    if lease.get("plan_status") != expected_phase:
        reason = f"Controller-only: workspace-less {lease.get('role')} lease requires {expected_phase} phase."
        return _block_hook(event_name, reason, diagnose_block(cwd, event_name, tool, command, reason))
    errors = lease_path_errors(cwd, lease, rel_paths)
    if errors:
        reason = f"Controller-only: workspace-less lease violation: {'; '.join(errors)}"
        return _block_hook(event_name, reason, diagnose_block(cwd, event_name, tool, command, reason))
    return _allow_hook(event_name, f"controller-only workspace-less {lease.get('role')} lease")


def dispatch(cwd: Path) -> dict[str, Any]:
    payload = _load_payload()
    event_name = _extract_event_name(payload)
    effective_cwd = _extract_effective_cwd(payload, cwd)
    command = _extract_command(payload)
    tool = _extract_tool(payload)
    command_workspace = _command_target_workspace(command, effective_cwd)
    path_workspace = _find_workspace_from_payload_paths(payload, effective_cwd) if tool in EDIT_TOOLS else None
    workspace = command_workspace or path_workspace or _find_workspace(effective_cwd)
    if command_workspace is not None:
        effective_cwd = command_workspace
    _LEDGER_CONTEXT.clear()
    _LEDGER_CONTEXT.update({"payload": payload, "effective_cwd": effective_cwd, "workspace": workspace})
    if event_name == "SessionStart":
        return _hook_output("SessionStart", _session_start_context(workspace) if workspace else _non_workspace_context(effective_cwd))
    if event_name == "UserPromptSubmit":
        context_parts = [
            part
            for part in [
                _prompt_delta_context(workspace),
                _prompt_safety_context(payload),
                _prompt_workspace_less_assignment_context(effective_cwd, payload, workspace),
            ]
            if part
        ]
        return _hook_output("UserPromptSubmit", "\n".join(context_parts))
    if event_name == "PostToolUse":
        return _noop()
    if event_name == "Stop":
        if workspace is None:
            return _noop()
        workspace_data = read_data(workspace / "workspace.yaml")
        plan_meta, _ = read_frontmatter(workspace / workspace_data["paths"]["plan"])
        if plan_meta.get("status") in {"ready_to_finish", "done"}:
            open_events = open_block_events_for(workspace)
            if open_events:
                event_ids = ", ".join(str(item.get("event_id")) for item in open_events[:5])
                reason = f"AI-DLC: open block events require action before finish: {event_ids}"
                diagnosis = _block_diagnosis(
                    "open_blockers",
                    "record_block_action",
                    ["ai-dlc block list", "ai-dlc block record", "ai-dlc block sync"],
                    reason,
                    recoverable=True,
                )
                return _block_hook("Stop", reason, diagnosis)
        missing = stop_missing_obligation(workspace, plan_meta)
        if missing:
            return _block_hook("Stop", missing, diagnose_block(workspace, "Stop", "", "", missing))
        return _noop()
    if workspace is None:
        if _subagent_required_outside_workspace(effective_cwd):
            if tool == "Bash" and _is_git_finish_approved_command(command):
                return _allow_hook(event_name, "controller-only git finish command approved")
            if tool in EDIT_TOOLS:
                rel_paths = _extract_paths(payload, effective_cwd, effective_cwd)
                if not rel_paths:
                    reason = "Controller-only: edited paths could not be determined; delegate to a subagent."
                    return _block_hook(event_name, reason, diagnose_block(effective_cwd, event_name, tool, command, reason))
                if _all_paths_match(rel_paths, _bootstrap_edit_paths(effective_cwd)):
                    return _allow_hook(event_name, "controller-only bootstrap edit allowed")
                lease_decision = _workspace_less_edit_block(effective_cwd, payload, event_name, tool, command, rel_paths)
                if lease_decision is not None:
                    return lease_decision
                reason = "Controller-only: direct edits are blocked outside AI-DLC; delegate to a subagent."
                return _block_hook(event_name, reason, diagnose_block(effective_cwd, event_name, tool, command, reason))
            if tool == "Bash" and _is_safe_aidlc_command(command):
                tokens = shlex.split(command.strip())
                if tokens[:3] == ["ai-dlc", "assignment", "create"] and not _is_allowed_workspace_less_assignment_create(tokens):
                    reason = (
                        "Controller-only bootstrap/delegation deadlock: workspace-less assignment create requires "
                        "a supported role and narrow matrix-approved --writable paths."
                    )
                    return _block_hook(event_name, reason, diagnose_block(effective_cwd, event_name, tool, command, reason))
            if (
                tool == "Bash"
                and not _is_read_only_bash(command)
                and not _is_allowed_project_validation_command(command, effective_cwd)
                and not _is_allowed_bootstrap_command(command, effective_cwd)
            ):
                reason = "Controller-only: mutating Bash is blocked outside AI-DLC; delegate to a subagent."
                return _block_hook(event_name, reason, diagnose_block(effective_cwd, event_name, tool, command, reason))
            return _allow_hook(event_name, "controller-only bootstrap phase")
        return _allow_hook(event_name, "not an AI-DLC workspace")

    if any(pattern in command for pattern in DESTRUCTIVE_GIT):
        reason = "AI-DLC: destructive git command requires explicit approval."
        return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

    if tool == "Bash" and _is_write_like_bash(command) and os.environ.get("AI_DLC_ALLOW_CONTROLLER_EDIT") != "1":
        reason = "AI-DLC: write-like Bash commands are blocked; use apply_patch/Edit with a claimed lease."
        return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))
    if tool == "Bash" and command and not _is_read_only_bash(command):
        if _is_safe_aidlc_command(command):
            pass
        elif _is_allowed_project_validation_command(command, effective_cwd):
            return _allow_hook(event_name, "AI-DLC: allowed project validation command")
        elif _is_allowed_verifier_gate_command(workspace, effective_cwd, command):
            return _allow_hook(event_name, "AI-DLC: allowed verifier gate command from work-items")
        elif "ai-dlc root-export" not in command and "ai-dlc overlay-cleanup" not in command and not _is_git_commit(command) and not _is_allowed_bootstrap_command(command, effective_cwd):
            reason = "AI-DLC: unknown mutating Bash commands are denied by default in AI-DLC workspaces."
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

    if tool in EDIT_TOOLS:
        rel_paths = _extract_paths(payload, workspace, effective_cwd)
        if not rel_paths:
            reason = "AI-DLC: edited paths could not be determined."
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

        if os.environ.get("AI_DLC_ALLOW_CONTROLLER_EDIT") == "1":
            return _allow_hook(event_name, "controller override enabled")

        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None:
            if scoped_break_glass_allowed(workspace, "controller_artifact_edit", rel_paths):
                return _allow_hook(event_name, "AI-DLC: scoped break-glass controller artifact edit allowed")
            if _paths_match(rel_paths, CONTROLLER_ALLOWED_PATHS):
                reason = "AI-DLC: controller must delegate tracked plan or handoff edits to a claimed subagent."
                return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))
            reason = "AI-DLC: writable session requires a claimed lease."
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

        assignment = load_assignment(workspace, lease["assignment_id"])
        if assignment.get("status") != "claimed":
            reason = "AI-DLC: assignment must be claimed before editing."
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

        if lease.get("role") == "dlc_repo_worker":
            errors = bootstrap_gate_errors(workspace, lease)
            if errors:
                reason = f"AI-DLC: bootstrap gate failed: {'; '.join(errors)}"
                return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

        errors = lease_path_errors(workspace, lease, rel_paths)
        if errors:
            reason = f"AI-DLC: lease violation: {'; '.join(errors)}"
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

    if tool == "Bash" and "git commit" in command and " -C " not in f" {command} " and "AI_DLC_ALLOW_OVERLAY_BASELINE" not in command:
        workspace_data = read_data(workspace / "workspace.yaml")
        embedded = [name for name in workspace_data["repos"] if name != "root-system"]
        if embedded:
            reason = "AI-DLC: commit embedded repos from child repositories, not from root-system."
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

    if tool == "Bash" and "ai-dlc root-export" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            reason = "AI-DLC: root-export requires a claimed git_operator lease."
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

    if tool == "Bash" and "ai-dlc overlay-cleanup" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            reason = "AI-DLC: overlay-cleanup requires a claimed git_operator lease."
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

    if tool == "Bash" and "git -C " in command and " commit" in command:
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease is None or lease.get("role") != "dlc_git_operator":
            reason = "AI-DLC: child repo commit requires a claimed git_operator lease."
            return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

    if tool == "Bash" and command.startswith("git -C "):
        session_id = os.environ.get("CODEX_SESSION_ID")
        lease = load_lease(workspace, session_id)
        if lease and lease.get("repo"):
            repo_prefix = f"git -C {lease['repo']}"
            if repo_prefix not in command:
                reason = f"AI-DLC: session lease only permits git -C {lease['repo']} commands."
                return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

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
            if scoped_break_glass_allowed(workspace, "force_next_agent"):
                allowed = True
            if not allowed:
                reason = f"AI-DLC: next agent must be {expected} unless decisions explicitly allow {target_agent}."
                return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))
            if target_agent == "dlc_verifier" and _claimed_repo_worker_exists(workspace):
                reason = "AI-DLC: verifier must not run while a repo_worker assignment is still claimed."
                return _block_hook(event_name, reason, diagnose_block(workspace, event_name, tool, command, reason))

    return _allow_hook(event_name)
