from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .io import now_iso, read_data, read_frontmatter, write_data, write_frontmatter
from .overlay import git, validate_overlay
from .schemas import validate_required
from .workspace import ai_dlc_context
from .workflow_contracts import (
    apply_transition_side_effects,
    next_agent_for_status,
    role_allowed_for_phase,
    validate_transition,
    validate_workflow,
    workflow_type,
)

WORK_ITEM_TRANSITIONS = {
    "not_started": {"active", "blocked", "cancelled"},
    "active": {"blocked", "passing", "cancelled"},
    "blocked": {"active", "cancelled"},
    "passing": set(),
    "cancelled": set(),
}

EXECUTION_PLAN_STATUSES = {"executing"}
CONTROL_PLANE_ROLE_WRITABLE = {
    "dlc_initializer": ["ai-dlc/bootstrap/**", "ai-dlc/overlay/**", "../.local/**"],
    "dlc_plan_writer": ["ai-dlc/plans/**", "ai-dlc/decisions/**"],
    "dlc_scope_manager": ["ai-dlc/work-items/**", "ai-dlc/decisions/**"],
    "dlc_verifier": ["ai-dlc/evidence/**", "../.local/ai-dlc/logs/**"],
    "dlc_evaluator": ["ai-dlc/evidence/**", "ai-dlc/quality/**", "../.local/ai-dlc/logs/**"],
    "dlc_handoff_writer": ["ai-dlc/handoff/**"],
    "dlc_docs_writer": ["ai-dlc/docs/**"],
    "dlc_git_operator": ["ai-dlc/evidence/**", "ai-dlc/handoff/**", "ai-dlc/quality/**", "../.local/**"],
    "dlc_repairer": ["ai-dlc/bootstrap/**", "ai-dlc/overlay/**", "ai-dlc/decisions/**", "../.local/**"],
}
CONTROL_PLANE_LOCKS = {
    "dlc_plan_writer": "plan.lock",
    "dlc_scope_manager": "work-items.lock",
    "dlc_verifier": "evidence.lock",
    "dlc_evaluator": "evidence.lock",
    "dlc_handoff_writer": "handoff.lock",
    "dlc_docs_writer": "docs.lock",
    "dlc_git_operator": "git.lock",
    "dlc_initializer": "bootstrap.lock",
    "dlc_repairer": "bootstrap.lock",
}


def _has_workspace(root: Path) -> bool:
    return (root / "workspace.yaml").exists()


def _workspace_less_context(root: Path) -> dict[str, Any]:
    context = ai_dlc_context(root, ensure_user_local=True)
    if context.get("control_plane_scope") != "user_local" or not context.get("root"):
        raise FileNotFoundError("workspace.yaml not found")
    return context


def _workspace_less_project_id(root: Path) -> str:
    context_path = assignment_root(root) / "context.yaml"
    context = read_data(context_path)
    return str(context.get("project_id") or Path(root).resolve().name)


def _workspace_less_branch(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    branch = result.stdout.strip()
    return branch if result.returncode == 0 and branch else "workspace-less"


def workspace_paths(root: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    workspace = read_data(root / "workspace.yaml")
    paths = {key: root / value for key, value in workspace["paths"].items() if key != "local"}
    return workspace, paths


def workspace_issue(root: Path) -> dict[str, Any]:
    workspace, _ = workspace_paths(root)
    return workspace.get("issue", {})


def load_plan(root: Path) -> tuple[Path, dict[str, Any], str]:
    _, paths = workspace_paths(root)
    path = paths["plan"]
    meta, body = read_frontmatter(path)
    return path, meta, body


def save_plan(path: Path, meta: dict[str, Any], body: str) -> None:
    write_frontmatter(path, meta, body)


def transition(root: Path, status: str) -> dict[str, Any]:
    path, meta, body = load_plan(root)
    workflow_errors = validate_transition(meta, status)
    workflow_errors.extend(_phase_completion_errors(root, meta, status))
    if workflow_errors:
        raise ValueError("\n".join(workflow_errors))
    meta["status"] = status
    apply_transition_side_effects(meta, status)
    save_plan(path, meta, body)
    return meta


def _phase_completion_errors(root: Path, meta: dict[str, Any], target_status: str) -> list[str]:
    current_status = str(meta.get("status"))
    if target_status in {"needs_decision", "repairing", "blocked", "abandoned"}:
        return []
    if current_status in {"intake", "initializing", "done"}:
        return []
    expected_role = next_agent_for_status(current_status, workflow_type(meta))
    if not expected_role:
        return []
    if _phase_report_exists(root, current_status, expected_role):
        return []
    return [f"phase {current_status} requires {expected_role} report before transition to {target_status}"]


def _phase_report_exists(root: Path, phase: str, role: str) -> bool:
    reports_dir = assignment_root(root) / "reports"
    if not reports_dir.exists():
        return False
    for path in reports_dir.glob("A*.json"):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if report.get("role") != role:
            continue
        if report.get("phase") != phase:
            continue
        if report.get("status") in {"blocked", "failed", "cancelled"}:
            continue
        return True
    return False


def validate(root: Path) -> list[str]:
    _, paths = workspace_paths(root)
    errors = validate_overlay(root)
    for key in ["overlay", "bootstrap", "work_items", "evidence"]:
        try:
            validate_required(read_data(paths[key]))
        except Exception as exc:
            errors.append(str(exc))
    _, plan_meta, _ = load_plan(root)
    if plan_meta.get("schema") != "ai-dlc.plan.v2":
        errors.append("plan schema must be ai-dlc.plan.v2")
    errors.extend(validate_workflow(plan_meta))
    for key in ["next_agent", "next_action"]:
        if not (plan_meta.get("current") or {}).get(key):
            errors.append(f"plan.current.{key} is required")

    handoff_meta, handoff_text = read_frontmatter(paths["handoff"])
    if handoff_meta.get("schema") != "ai-dlc.handoff.v1":
        errors.append("handoff schema must be ai-dlc.handoff.v1")
    for key in ["workspace_id", "issue_url", "issue_branch", "root_export_target", "active_assignments", "lease_sessions", "branch_map", "pending_obligations"]:
        if key not in handoff_meta:
            errors.append(f"handoff missing key: {key}")
    for marker in ["active assignments", "lease detail", "root-export status", "Pending obligations"]:
        if marker not in handoff_text:
            errors.append(f"handoff missing marker: {marker}")
    decisions_meta, decisions_text = read_frontmatter(paths["decisions"])
    if decisions_meta.get("schema") != "ai-dlc.decisions.v1":
        errors.append("decisions schema must be ai-dlc.decisions.v1")
    for key in ["workspace_id", "issue_url", "timestamp", "actor_role", "affected_stage", "approval_boundary", "allow_next_agent"]:
        if key not in decisions_meta:
            errors.append(f"decisions missing key: {key}")
    for marker in ["workspace_id:", "actor_role:", "approval_boundary:", "allow-next-agent:"]:
        if marker not in decisions_text:
            errors.append(f"decisions missing marker: {marker}")

    work_items = read_data(paths["work_items"])
    active_items = [item for item in work_items["items"] if item.get("state") == "active"]
    if len(active_items) > work_items["wip_limit"]:
        errors.append("WIP limit exceeded")
    if work_items.get("active_item") and len(active_items) != 1:
        errors.append("active_item must point to exactly one active item")
    for item in work_items["items"]:
        if item.get("state") == "passing" and not item.get("completion_evidence", {}).get("evidence_ref"):
            errors.append(f"{item['id']}: passing requires completion evidence")
    return errors


def _save_work_items(path: Path, data: dict[str, Any]) -> None:
    write_data(path, data)


def work_item_activate(root: Path, item_id: str) -> dict[str, Any]:
    _, paths = workspace_paths(root)
    data = read_data(paths["work_items"])
    active = [item for item in data["items"] if item["state"] == "active" and item["id"] != item_id]
    if len(active) >= data["wip_limit"]:
        raise ValueError("WIP limit exceeded")
    found = None
    for item in data["items"]:
        if item["id"] == item_id:
            if item["state"] not in WORK_ITEM_TRANSITIONS or "active" not in WORK_ITEM_TRANSITIONS[item["state"]]:
                raise ValueError(f"cannot activate item from {item['state']}")
            item["state"] = "active"
            found = item
        elif item["state"] == "active":
            item["state"] = "blocked"
    if not found:
        raise ValueError(f"work item not found: {item_id}")
    data["active_item"] = item_id
    _save_work_items(paths["work_items"], data)
    path, meta, body = load_plan(root)
    meta.setdefault("current", {})["active_item"] = item_id
    save_plan(path, meta, body)
    return found


def work_item_block(root: Path, item_id: str, reason: str) -> dict[str, Any]:
    _, paths = workspace_paths(root)
    data = read_data(paths["work_items"])
    for item in data["items"]:
        if item["id"] == item_id:
            if "blocked" not in WORK_ITEM_TRANSITIONS.get(item["state"], set()):
                raise ValueError(f"cannot block item from {item['state']}")
            item["state"] = "blocked"
            item.setdefault("blockers", []).append(reason)
            if data.get("active_item") == item_id:
                data["active_item"] = None
            _save_work_items(paths["work_items"], data)
            return item
    raise ValueError(f"work item not found: {item_id}")


def work_item_cancel(root: Path, item_id: str, reason: str) -> dict[str, Any]:
    _, paths = workspace_paths(root)
    data = read_data(paths["work_items"])
    for item in data["items"]:
        if item["id"] == item_id:
            if "cancelled" not in WORK_ITEM_TRANSITIONS.get(item["state"], set()):
                raise ValueError(f"cannot cancel item from {item['state']}")
            item["state"] = "cancelled"
            item.setdefault("blockers", []).append(reason)
            if data.get("active_item") == item_id:
                data["active_item"] = None
            _save_work_items(paths["work_items"], data)
            return item
    raise ValueError(f"work item not found: {item_id}")


def verify_gate(root: Path, item_id: str, summary: str) -> dict[str, Any]:
    _, paths = workspace_paths(root)
    data = read_data(paths["work_items"])
    evidence = read_data(paths["evidence"])
    target_item = next((item for item in data["items"] if item["id"] == item_id), None)
    if target_item is None:
        raise ValueError(f"work item not found: {item_id}")
    if target_item.get("state") != "active":
        raise ValueError("verify-gate requires active item")
    repo = target_item.get("repo")
    repo_state = {}
    if repo:
        repo_path = root / repo
        repo_state = {
            "repo": repo,
            "workspace_id": read_data(root / "workspace.yaml")["id"],
            "issue_branch": read_data(root / "workspace.yaml")["branch"]["issue"],
            "branch": git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path),
            "head_sha": git(["rev-parse", "HEAD"], repo_path),
            "tree_clean": git(["status", "--short"], repo_path) == "",
        }
    for item in data["items"]:
        if item["id"] == item_id:
            item["state"] = "passing"
            item.setdefault("completion_evidence", {})["status"] = "recorded"
            item["completion_evidence"]["evidence_ref"] = str(paths["evidence"].relative_to(root))
            data["active_item"] = None
            write_data(paths["work_items"], data)
            evidence["items"][item_id] = {
                "status": "passing",
                "summary": summary,
                "recorded_at": now_iso(),
                "recorded_by": "dlc_verifier",
                "work_item": item_id,
                **repo_state,
            }
            write_data(paths["evidence"], evidence)
            return item
    raise ValueError(f"work item not found: {item_id}")


def load_assignment(root: Path, assignment_id: str) -> dict[str, Any]:
    base = assignment_root(root)
    return read_data(base / "assignments" / f"{assignment_id}.yaml")


def load_lease(root: Path, session_id: str | None) -> dict[str, Any] | None:
    base = assignment_root(root)
    if session_id:
        path = base / "leases" / f"{session_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    # session_id が未設定または一致しない場合、有効な claimed lease を探す
    leases_dir = base / "leases"
    if not leases_dir.exists():
        return None
    candidates: list[dict[str, Any]] = []
    for lease_path in leases_dir.glob("*.json"):
        try:
            data = json.loads(lease_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("status") != "claimed":
            continue
        if _lease_expired(data):
            continue
        candidates.append(data)
    if len(candidates) == 1:
        return candidates[0]
    return None


def _lock_path(base: Path, repo: str) -> Path:
    return base / "locks" / f"repo-{repo}.lock"


def _named_lock_path(base: Path, lock_name: str) -> Path:
    return base / "locks" / lock_name


def _read_lock(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"session_id": raw}


def _decisions_text(root: Path) -> str:
    _, paths = workspace_paths(root)
    return paths["decisions"].read_text(encoding="utf-8")


def _decision_allows(root: Path, token: str) -> bool:
    return token in _decisions_text(root)


def _lease_expired(lease: dict[str, Any]) -> bool:
    expires_at = lease.get("expires_at")
    if not expires_at:
        return False
    try:
        return datetime.fromisoformat(expires_at) <= datetime.now().astimezone()
    except ValueError:
        return False


def _active_items(work_items: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in work_items["items"] if item.get("state") == "active"]


def bootstrap_gate_errors(root: Path, lease: dict[str, Any] | None = None) -> list[str]:
    _, paths = workspace_paths(root)
    errors = validate_overlay(root)
    bootstrap_data = read_data(paths["bootstrap"])
    if bootstrap_data.get("status") != "ready":
        errors.append("bootstrap.status must be ready")

    _, plan_meta, _ = load_plan(root)
    if plan_meta.get("status") not in EXECUTION_PLAN_STATUSES:
        errors.append("plan.status must be executing")

    work_items = read_data(paths["work_items"])
    active_items = _active_items(work_items)
    if len(active_items) != 1:
        errors.append("exactly one active work item is required")

    if lease:
        if _lease_expired(lease):
            errors.append("lease expired")
        assignment = load_assignment(root, lease["assignment_id"])
        if assignment.get("role") != "dlc_repo_worker":
            return errors
        if assignment.get("status") != "claimed":
            errors.append("repo worker assignment must be claimed")
        active_item = active_items[0]["id"] if len(active_items) == 1 else None
        if not assignment.get("work_item"):
            errors.append("repo worker assignment must reference a work item")
        elif active_item != assignment.get("work_item"):
            errors.append("repo worker assignment must match the active work item")
        if lease.get("active_item") != assignment.get("work_item"):
            errors.append("repo worker lease must match the active work item")
        if assignment.get("repo"):
            lock_path = assignment_root(root) / "locks" / f"repo-{assignment['repo']}.lock"
            if not lock_path.exists():
                errors.append(f"repo lock missing for {assignment['repo']}")
            else:
                lock = _read_lock(lock_path)
                if not lock or lock.get("session_id") != lease["session_id"]:
                    errors.append(f"repo lock mismatch for {assignment['repo']}")
                elif lock.get("expires_at") and _lease_expired(lock):
                    errors.append(f"repo lock expired for {assignment['repo']}")
    return errors


def path_is_allowed(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def lease_path_errors(root: Path, lease: dict[str, Any], rel_paths: list[str]) -> list[str]:
    errors: list[str] = []
    if _lease_expired(lease):
        errors.append("lease expired")
    writable = lease.get("writable", [])
    forbidden = lease.get("forbidden", [])
    for rel_path in rel_paths:
        if path_is_allowed(rel_path, forbidden):
            errors.append(f"path is forbidden by lease: {rel_path}")
            continue
        if writable and not path_is_allowed(rel_path, writable):
            errors.append(f"path is outside writable lease: {rel_path}")
    if lease.get("repo") and not lease.get("workspace_less"):
        repo_prefix = f"{lease['repo']}/"
        for rel_path in rel_paths:
            if not rel_path.startswith(repo_prefix):
                errors.append(f"path is outside assigned repo {lease['repo']}: {rel_path}")
    return errors


def invalidate(root: Path, item_id: str) -> None:
    _, paths = workspace_paths(root)
    evidence = read_data(paths["evidence"])
    evidence["items"].pop(item_id, None)
    write_data(paths["evidence"], evidence)


def bootstrap(root: Path, status: str | None = None) -> dict[str, Any]:
    workspace, paths = workspace_paths(root)
    data = read_data(paths["bootstrap"])
    if status is None:
        data["overlay"]["status"] = "ready" if not validate_overlay(root) else "blocked"
        data["status"] = "ready" if data["overlay"]["status"] == "ready" else "blocked"
        readiness = "ready" if data["status"] == "ready" else "blocked"
        for key in data["readiness"]:
            data["readiness"][key] = readiness
    else:
        data["status"] = status
    write_data(paths["bootstrap"], data)
    return data


def evidence_record(root: Path, key: str, status: str, note: str) -> dict[str, Any]:
    _, paths = workspace_paths(root)
    evidence = read_data(paths["evidence"])
    evidence["items"][key] = {"status": status, "summary": note, "recorded_at": now_iso()}
    write_data(paths["evidence"], evidence)
    return evidence["items"][key]


def clean_state_check(root: Path) -> dict[str, Any]:
    import subprocess

    workspace, paths = workspace_paths(root)
    evidence = read_data(paths["evidence"])
    embedded_paths = [meta["path"] for name, meta in workspace["repos"].items() if name != "root-system"]
    status_cmd = ["git", "status", "--short"]
    if embedded_paths:
        status_cmd.extend(["--", *embedded_paths])
    status = subprocess.run(status_cmd, cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    clean = status == ""
    evidence["clean_state"]["artifacts"]["status"] = "passing" if clean else "blocked"
    write_data(paths["evidence"], evidence)
    return evidence["clean_state"]


def deadlock_check(root: Path) -> dict[str, Any]:
    _, paths = workspace_paths(root)
    _, plan_meta, _ = load_plan(root)
    result = {
        "status": "ok" if plan_meta.get("current", {}).get("next_action") else "blocked",
        "next_action": plan_meta.get("current", {}).get("next_action"),
    }
    return result


def lock_list(root: Path) -> list[dict[str, Any]]:
    base = assignment_root(root)
    locks_dir = base / "locks"
    if not locks_dir.exists():
        return []
    locks: list[dict[str, Any]] = []
    for path in sorted(locks_dir.glob("*.lock")):
        lock = _read_lock(path) or {}
        lock["name"] = path.name
        locks.append(lock)
    return locks


def lock_release(root: Path, lock_name: str, session_id: str | None = None) -> None:
    base = assignment_root(root)
    path = base / "locks" / lock_name
    if not path.exists():
        raise ValueError(f"lock not found: {lock_name}")
    lock = _read_lock(path) or {}
    session_id = session_id or os.environ.get("CODEX_SESSION_ID")
    if lock.get("session_id") and session_id and lock.get("session_id") != session_id:
        if not (_lease_expired(lock) and _has_workspace(root) and _decision_allows(root, f"allow-stale-lock-release: {lock_name}")):
            raise ValueError("lock is owned by a different session")
    path.unlink()


def workspace_status(root: Path) -> dict[str, Any]:
    workspace, paths = workspace_paths(root)
    _, plan_meta, _ = load_plan(root)
    work_items = read_data(paths["work_items"])
    return {
        "workspace_id": workspace["id"],
        "plan_status": plan_meta.get("status"),
        "next_agent": (plan_meta.get("current") or {}).get("next_agent"),
        "active_item": work_items.get("active_item"),
        "active_assignments": [item["id"] for item in assignment_list(root) if item.get("status") == "claimed"],
        "locks": lock_list(root),
        "validation_errors": validate(root),
    }


def finish(root: Path) -> dict[str, Any]:
    errors = validate(root)
    if errors:
        raise ValueError("\n".join(errors))
    active_assignments = [item["id"] for item in assignment_list(root) if item.get("status") == "claimed"]
    if active_assignments:
        raise ValueError(f"cannot finish with claimed assignments: {', '.join(active_assignments)}")
    if lock_list(root):
        raise ValueError("cannot finish while locks remain")
    _, paths = workspace_paths(root)
    evidence = read_data(paths["evidence"])
    if not evidence.get("verifier_log"):
        raise ValueError("cannot finish without verifier evidence log")
    if not evidence.get("evaluator_log"):
        raise ValueError("cannot finish without evaluator verdict log")
    clean_state = clean_state_check(root)
    if clean_state["artifacts"]["status"] != "passing":
        raise ValueError("clean-state-check failed")
    _, plan_meta, _ = load_plan(root)
    if plan_meta.get("status") == "evaluating":
        transition(root, "handoff_ready")
    transition(root, "ready_to_finish")
    transition(root, "done")
    _, plan_meta, _ = load_plan(root)
    return {"status": plan_meta["status"], "clean_state": clean_state["artifacts"]["status"]}


def assignment_root(root: Path) -> Path:
    if not _has_workspace(root):
        return Path(_workspace_less_context(root)["root"])
    workspace = read_data(root / "workspace.yaml")
    return (root / workspace["paths"]["local"]).resolve() / "ai-dlc"


def _next_assignment_id(assignments_dir: Path) -> str:
    numbers = []
    for path in assignments_dir.glob("A*.yaml"):
        try:
            numbers.append(int(path.stem[1:]))
        except ValueError:
            pass
    return f"A{(max(numbers, default=0) + 1):03d}"


def assignment_create(root: Path, role: str, repo: str | None, writable: list[str], work_item: str | None) -> dict[str, Any]:
    if not _has_workspace(root):
        return _workspace_less_assignment_create(root, role, repo, writable, work_item)

    workspace, paths = workspace_paths(root)
    _, plan_meta, _ = load_plan(root)
    plan_status = plan_meta.get("status")
    phase_owner = next_agent_for_status(str(plan_status), workflow_type(plan_meta))
    if not role_allowed_for_phase(plan_meta, role):
        raise ValueError(f"assignment role {role} is not allowed during {workflow_type(plan_meta)} phase {plan_status}; expected {phase_owner}")
    base = assignment_root(root)
    assignments_dir = base / "assignments"
    assignments_dir.mkdir(parents=True, exist_ok=True)
    assignment_id = _next_assignment_id(assignments_dir)
    role_writable = CONTROL_PLANE_ROLE_WRITABLE.get(role)
    resolved_writable = writable or role_writable or []
    forbidden = [name + "/**" for name in workspace["repos"] if name not in {"root-system", repo}]
    if role == "dlc_repo_worker":
        forbidden.extend(["ai-dlc/**", "workspace.yaml", ".codex/**"])
    elif role_writable:
        forbidden.extend(["workspace.yaml", ".codex/**"])
    else:
        forbidden.extend(["ai-dlc/**", "workspace.yaml", ".codex/**"])
    payload = {
        "schema": "ai-dlc.assignment.v1",
        "id": assignment_id,
        "workspace_id": workspace["id"],
        "role": role,
        "agent": role,
        "phase": plan_status,
        "workflow_type": workflow_type(plan_meta),
        "phase_owner": phase_owner,
        "controller_mode": (plan_meta.get("orchestration") or {}).get("controller_mode", "orchestrate_only"),
        "repo": repo,
        "lock_scope": f"repo:{repo}" if repo else CONTROL_PLANE_LOCKS.get(role),
        "work_item": work_item,
        "writable": resolved_writable,
        "forbidden": forbidden,
        "deliverables": _role_deliverables(role),
        "issue": workspace.get("issue", {}),
        "branch": {
            "issue": workspace["branch"]["issue"],
            "base_ref": workspace["repos"].get(repo, {}).get("base_ref", workspace["branch"]["base_ref"]) if repo else workspace["branch"]["base_ref"],
        },
        "result_ref": str((assignment_root(root) / "reports" / f"{assignment_id}.json").relative_to(base.parent)),
        "status": "created",
        "created_at": now_iso(),
    }
    if work_item:
        work_items = read_data(paths["work_items"])
        for item in work_items["items"]:
            if item["id"] == work_item:
                payload["next_recommendation"] = item.get("verifier_gate", {"phase": "executing", "assignment_role": role})
                break
    write_data(assignments_dir / f"{assignment_id}.yaml", payload)
    return payload


def _workspace_less_assignment_create(root: Path, role: str, repo: str | None, writable: list[str], work_item: str | None) -> dict[str, Any]:
    if role != "dlc_repo_worker":
        raise ValueError("workspace-less source_change assignments currently require role dlc_repo_worker")
    if not writable:
        raise ValueError("workspace-less dlc_repo_worker assignment requires at least one --writable path")

    root = root.expanduser().resolve()
    base = assignment_root(root)
    assignments_dir = base / "assignments"
    assignments_dir.mkdir(parents=True, exist_ok=True)
    assignment_id = _next_assignment_id(assignments_dir)
    repo_name = repo or "source"
    project_id = _workspace_less_project_id(root)
    branch = _workspace_less_branch(root)
    forbidden = [".codex/**", ".git/**", "ai-dlc/**", "workspace.yaml"]
    payload = {
        "schema": "ai-dlc.assignment.v1",
        "id": assignment_id,
        "workspace_id": project_id,
        "workspace_less": True,
        "source_root": str(root),
        "role": role,
        "agent": role,
        "phase": "executing",
        "workflow_type": "plan_implementation",
        "phase_owner": "dlc_repo_worker",
        "controller_mode": "orchestrate_only",
        "repo": repo_name,
        "lock_scope": f"repo:{repo_name}",
        "work_item": work_item,
        "writable": writable,
        "forbidden": forbidden,
        "deliverables": _role_deliverables(role),
        "issue": {"tracker": "workspace-less", "id": project_id, "url": ""},
        "branch": {"issue": branch, "base_ref": ""},
        "result_ref": f"reports/{assignment_id}.json",
        "status": "created",
        "created_at": now_iso(),
        "next_recommendation": {"phase": "verifying", "assignment_role": "dlc_verifier"},
    }
    write_data(assignments_dir / f"{assignment_id}.yaml", payload)
    return payload


def _role_deliverables(role: str) -> list[str]:
    return {
        "dlc_plan_writer": ["plan_delta"],
        "dlc_scope_manager": ["work_items_delta"],
        "dlc_repo_worker": ["worker_report"],
        "dlc_verifier": ["evidence_ref"],
        "dlc_evaluator": ["evaluator_verdict"],
        "dlc_handoff_writer": ["handoff_ref"],
        "dlc_docs_writer": ["docs_ref"],
        "dlc_git_operator": ["git_result_ref"],
        "dlc_initializer": ["bootstrap_readiness"],
        "dlc_repairer": ["repair_report"],
    }.get(role, ["report"])


def assignment_list(root: Path) -> list[dict[str, Any]]:
    base = assignment_root(root)
    return [read_data(path) for path in sorted((base / "assignments").glob("A*.yaml"))]


def assignment_update_status(root: Path, assignment_id: str, status: str) -> dict[str, Any]:
    base = assignment_root(root)
    path = base / "assignments" / f"{assignment_id}.yaml"
    data = read_data(path)
    data["status"] = status
    data["updated_at"] = now_iso()
    write_data(path, data)
    return data


def agent_claim(root: Path, assignment_id: str, session_id: str | None = None) -> dict[str, Any]:
    session_id = session_id or os.environ.get("CODEX_SESSION_ID") or uuid.uuid4().hex
    base = assignment_root(root)
    assignment = read_data(base / "assignments" / f"{assignment_id}.yaml")
    if assignment.get("status") not in {"created", "accepted"}:
        raise ValueError(f"assignment is not claimable: {assignment.get('status')}")
    lock_owner = None
    lock_path: Path | None = None
    if assignment.get("repo"):
        lock_path = _lock_path(base, assignment["repo"])
    elif assignment.get("lock_scope"):
        lock_path = _named_lock_path(base, assignment["lock_scope"])
    if lock_path is not None:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        if lock_path.exists():
            existing = _read_lock(lock_path) or {}
            if _lease_expired(existing) and _decision_allows(root, f"allow-stale-lock-release: {lock_path.name}"):
                lock_path.unlink()
            else:
                label = assignment.get("repo") or assignment.get("lock_scope")
                raise ValueError(f"lock already held for {label}")
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        lock_owner = {
            "session_id": session_id,
            "nonce": uuid.uuid4().hex,
            "created_at": now_iso(),
            "expires_at": (datetime.now().astimezone() + timedelta(minutes=30)).isoformat(timespec="seconds"),
            "repo": assignment.get("repo"),
            "lock_scope": assignment.get("lock_scope"),
        }
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(lock_owner, indent=2, ensure_ascii=True) + "\n")
    lease = {
        "schema": "ai-dlc.lease.v1",
        "session_id": session_id,
        "assignment_id": assignment_id,
        "role": assignment["role"],
        "status": "claimed",
        "plan_status": assignment.get("phase") if assignment.get("workspace_less") else load_plan(root)[1].get("status"),
        "active_item": assignment.get("work_item"),
        "repo": assignment.get("repo"),
        "lock_scope": assignment.get("lock_scope"),
        "workspace_less": bool(assignment.get("workspace_less")),
        "source_root": assignment.get("source_root"),
        "issue": assignment.get("issue", {}),
        "branch": assignment.get("branch", {}),
        "writable": assignment.get("writable", []),
        "forbidden": assignment.get("forbidden", ["ai-dlc/**", "workspace.yaml"]),
        "created_at": now_iso(),
        "expires_at": lock_owner["expires_at"] if lock_owner else (datetime.now().astimezone() + timedelta(minutes=30)).isoformat(timespec="seconds"),
    }
    lease_path = base / "leases" / f"{session_id}.json"
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lease_path.write_text(json.dumps(lease, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    except Exception:
        if lock_path is not None:
            lock_path.unlink(missing_ok=True)
        raise
    assignment_update_status(root, assignment_id, "claimed")
    return lease


def agent_report(root: Path, assignment_id: str, status: str, report_file: str | None = None) -> dict[str, Any]:
    base = assignment_root(root)
    assignment = load_assignment(root, assignment_id)
    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{assignment_id}.json"
    payload = {
        "assignment_id": assignment_id,
        "workspace_id": assignment.get("workspace_id"),
        "role": assignment.get("role"),
        "status": status,
        "repo": assignment.get("repo"),
        "work_item": assignment.get("work_item"),
        "workflow_type": assignment.get("workflow_type"),
        "phase": assignment.get("phase"),
        "deliverables": assignment.get("deliverables", []),
        "issue": assignment.get("issue", {}),
        "branch": assignment.get("branch", {}),
        "reported_at": now_iso(),
        "next_recommendation": assignment.get("next_recommendation"),
    }
    if report_file:
        payload["source"] = report_file
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if assignment.get("role") in {"dlc_verifier", "dlc_evaluator"} and not assignment.get("workspace_less"):
        _, paths = workspace_paths(root)
        evidence = read_data(paths["evidence"])
        evidence["items"][f"assignment:{assignment_id}"] = {
            "status": status,
            "summary": f"assignment {assignment_id} reported",
            "recorded_at": now_iso(),
            "recorded_by": assignment.get("role"),
            "repo": assignment.get("repo"),
            "work_item": assignment.get("work_item"),
        }
        if assignment.get("role") == "dlc_evaluator":
            evidence.setdefault("evaluator_log", []).append(payload)
        else:
            evidence.setdefault("verifier_log", []).append(payload)
        write_data(paths["evidence"], evidence)
    assignment_update_status(root, assignment_id, status)
    return payload


def agent_release(root: Path, assignment_id: str, session_id: str | None = None) -> None:
    base = assignment_root(root)
    assignment = read_data(base / "assignments" / f"{assignment_id}.yaml")
    session_id = session_id or os.environ.get("CODEX_SESSION_ID")
    if not session_id:
        raise ValueError("session_id is required to release an assignment")
    lease_path = base / "leases" / f"{session_id}.json"
    if not lease_path.exists():
        raise ValueError(f"lease not found for session {session_id}")
    lease = json.loads(lease_path.read_text(encoding="utf-8"))
    if lease.get("assignment_id") != assignment_id:
        raise ValueError("lease does not own the requested assignment")
    lease_path.unlink()
    lock_path: Path | None = None
    if assignment.get("repo"):
        lock_path = _lock_path(base, assignment["repo"])
    elif assignment.get("lock_scope"):
        lock_path = _named_lock_path(base, assignment["lock_scope"])
    if lock_path is not None:
        lock = _read_lock(lock_path)
        if lock and lock.get("session_id") != session_id:
            raise ValueError("repo lock is owned by a different session")
        if lock_path.exists():
            lock_path.unlink()
    assignment_update_status(root, assignment_id, "released")
