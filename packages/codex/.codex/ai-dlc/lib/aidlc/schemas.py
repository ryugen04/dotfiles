from __future__ import annotations

from pathlib import Path

from .io import read_data

SCHEMA_REQUIREMENTS = {
    "ai-dlc.workspace.v1": ["id", "issue", "workspace", "branch", "layout", "repos", "paths", "controller", "workflow", "hardening"],
    "ai-dlc.overlay.v1": ["workspace_id", "mode", "baseline", "embedded_repos"],
    "ai-dlc.bootstrap.v1": ["workspace_id", "status", "readiness", "overlay", "repos"],
    "ai-dlc.work_items.v1": ["workspace_id", "wip_limit", "active_item", "items"],
    "ai-dlc.evidence.v1": ["workspace_id", "items", "diff_inspection", "clean_state"],
    "ai-dlc.assignment.v1": [
        "id",
        "workspace_id",
        "role",
        "agent",
        "phase",
        "workflow_type",
        "phase_owner",
        "controller_mode",
        "lock_scope",
        "writable",
        "forbidden",
        "deliverables",
        "status",
        "issue",
        "branch",
        "result_ref",
    ],
    "ai-dlc.lease.v1": [
        "session_id",
        "assignment_id",
        "role",
        "status",
        "plan_status",
        "lock_scope",
        "issue",
        "branch",
        "writable",
        "forbidden",
        "created_at",
        "expires_at",
    ],
    "ai-dlc.plan.v2": [
        "id",
        "status",
        "issue",
        "workspace_ref",
        "overlay_ref",
        "bootstrap_ref",
        "work_items_ref",
        "evidence_ref",
        "handoff_ref",
        "root_export",
        "current",
        "workflow",
        "orchestration",
        "paths",
        "targets",
        "phases",
        "approval_boundary",
        "rollback",
    ],
}

SCHEMA_NONEMPTY_PATHS = {
    "ai-dlc.workspace.v1": [
        ["issue", "url"],
        ["workspace", "root"],
        ["workspace", "root_system_path"],
        ["branch", "issue"],
        ["branch", "root_export", "target_ref"],
        ["branch", "root_export", "target_remote"],
    ],
    "ai-dlc.plan.v2": [["issue", "url"], ["current", "next_agent"], ["current", "next_action"], ["current", "stop_condition"]],
    "ai-dlc.work_items.v1": [["issue", "url"], ["item_template", "repo"], ["item_template", "title"], ["item_template", "status"], ["item_template", "source_ref"], ["item_template", "verifier_gate", "assignment_role"]],
    "ai-dlc.evidence.v1": [["entry_template", "repo"], ["entry_template", "issue_branch"], ["entry_template", "recorded_by"], ["entry_template", "command"], ["entry_template", "expected_outcome"], ["entry_template", "actual_result"], ["entry_template", "log_ref"], ["entry_template", "verdict"]],
}


def schema_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas"


def load_schema(name: str) -> dict:
    filename = f"{name.replace('.', '_')}.json"
    return read_data(schema_dir() / filename)


def validate_required(data: dict) -> None:
    schema_name = data.get("schema")
    if not schema_name:
        raise ValueError("schema is required")
    required = SCHEMA_REQUIREMENTS.get(schema_name, [])
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{schema_name}: missing required keys: {', '.join(missing)}")
    for path in SCHEMA_NONEMPTY_PATHS.get(schema_name, []):
        cursor = data
        for key in path:
            if not isinstance(cursor, dict) or key not in cursor:
                raise ValueError(f"{schema_name}: missing required path: {'.'.join(path)}")
            cursor = cursor[key]
        if cursor in ("", None, [], {}):
            raise ValueError(f"{schema_name}: empty required path: {'.'.join(path)}")
    if schema_name == "ai-dlc.workspace.v1":
        repos = data.get("repos", {})
        for name, repo in repos.items():
            if not isinstance(repo, dict):
                raise ValueError(f"{schema_name}: repo entry must be object: {name}")
            for key in ["canonical_repo_path", "canonical_repo_url", "base_sha", "head_sha"]:
                if repo.get(key) in ("", None):
                    raise ValueError(f"{schema_name}: repo {name} missing {key}")
    if schema_name == "ai-dlc.work_items.v1":
        template = data.get("item_template", {})
        for key in ["writable", "deliverables", "blocked_by", "verifier_gate", "evaluator_gate"]:
            if key not in template:
                raise ValueError(f"{schema_name}: item_template missing {key}")
    if schema_name == "ai-dlc.evidence.v1":
        template = data.get("entry_template", {})
        for key in ["head_sha", "tree_clean", "artifact_refs", "command", "expected_outcome", "actual_result", "log_ref", "verdict"]:
            if key not in template:
                raise ValueError(f"{schema_name}: entry_template missing {key}")
    if schema_name == "ai-dlc.assignment.v1":
        for key in ["writable", "forbidden", "deliverables"]:
            if not isinstance(data.get(key), list):
                raise ValueError(f"{schema_name}: {key} must be list")
    if schema_name == "ai-dlc.lease.v1":
        for key in ["writable", "forbidden"]:
            if not isinstance(data.get(key), list):
                raise ValueError(f"{schema_name}: {key} must be list")
