from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .io import read_data, read_frontmatter

ORIGIN_MODES = {"new_workspace_from_plan", "from_remote_ref", "resume_existing_workspace", "docs_only_no_workspace"}
EXECUTION_INTENTS = {"docs_only", "plan_then_stop", "docs_then_impl", "autonomous_until_git_boundary"}
SAFETY_DOMAINS = {"source_change", "codex_config_edit", "docs_report", "git_finish"}
WORKFLOW_TYPES = {
    "plan_implementation",
    "remote_ref_adoption",
    "resume_existing",
    "docs_report",
    "codex_config_edit",
    "git_finish",
}
CONFIG_EDIT_STAGES = {"repair_preflight", "staged_authoring", "active"}
PLAN_CONTRACT_SECTIONS = {"paths", "targets", "phases", "approval_boundary", "rollback"}
PLAN_PATH_KEYS = {"plan", "decisions", "work_items", "evidence", "handoff", "quality"}
PLAN_TARGET_KEYS = {"repos", "worktrees", "writable", "forbidden"}

DEFAULT_WORKFLOW = {
    "origin_mode": "new_workspace_from_plan",
    "execution_intent": "docs_then_impl",
    "safety_domain": "source_change",
    "workflow_type": "plan_implementation",
    "config_edit_stage": None,
}

WORKFLOW_TRANSITIONS: dict[str, dict[str, set[str]]] = {
    "plan_implementation": {
        "intake": {"initializing", "needs_decision", "repairing", "blocked", "abandoned"},
        "initializing": {"planning", "needs_decision", "repairing", "blocked", "abandoned"},
        "planning": {"plan_ready", "needs_decision", "repairing", "blocked", "abandoned"},
        "plan_ready": {"assigning", "needs_decision", "repairing", "blocked", "abandoned"},
        "assigning": {"executing", "needs_decision", "repairing", "blocked", "abandoned"},
        "executing": {"verifying", "needs_decision", "repairing", "blocked", "abandoned"},
        "verifying": {"evaluating", "needs_decision", "repairing", "blocked", "abandoned"},
        "evaluating": {"executing", "verifying", "handoff_ready", "needs_decision", "repairing", "blocked", "abandoned"},
        "handoff_ready": {"ready_to_finish", "needs_decision", "repairing", "blocked", "abandoned"},
        "ready_to_finish": {"done", "needs_decision", "repairing", "blocked", "abandoned"},
        "done": set(),
    },
    "remote_ref_adoption": {
        "intake": {"planning", "needs_decision", "repairing", "blocked", "abandoned"},
        "planning": {"plan_ready", "needs_decision", "repairing", "blocked", "abandoned"},
        "plan_ready": {"assigning", "needs_decision", "repairing", "blocked", "abandoned"},
        "assigning": {"executing", "needs_decision", "repairing", "blocked", "abandoned"},
        "executing": {"verifying", "needs_decision", "repairing", "blocked", "abandoned"},
        "verifying": {"evaluating", "needs_decision", "repairing", "blocked", "abandoned"},
        "evaluating": {"handoff_ready", "needs_decision", "repairing", "blocked", "abandoned"},
        "handoff_ready": {"ready_to_finish", "needs_decision", "repairing", "blocked", "abandoned"},
        "ready_to_finish": {"done", "needs_decision", "repairing", "blocked", "abandoned"},
        "done": set(),
    },
    "resume_existing": {
        "intake": {"planning", "repairing", "needs_decision", "blocked", "abandoned"},
        "repairing": {"planning", "assigning", "blocked", "abandoned"},
        "planning": {"assigning", "needs_decision", "repairing", "blocked", "abandoned"},
        "assigning": {"executing", "needs_decision", "repairing", "blocked", "abandoned"},
        "executing": {"verifying", "needs_decision", "repairing", "blocked", "abandoned"},
        "verifying": {"evaluating", "needs_decision", "repairing", "blocked", "abandoned"},
        "evaluating": {"handoff_ready", "needs_decision", "repairing", "blocked", "abandoned"},
        "handoff_ready": {"ready_to_finish", "needs_decision", "repairing", "blocked", "abandoned"},
        "ready_to_finish": {"done", "needs_decision", "repairing", "blocked", "abandoned"},
        "done": set(),
    },
    "docs_report": {
        "intake": {"planning", "needs_decision", "blocked", "abandoned"},
        "planning": {"executing", "needs_decision", "blocked", "abandoned"},
        "executing": {"verifying", "needs_decision", "blocked", "abandoned"},
        "verifying": {"handoff_ready", "needs_decision", "blocked", "abandoned"},
        "handoff_ready": {"done", "needs_decision", "blocked", "abandoned"},
        "done": set(),
    },
    "codex_config_edit": {
        "intake": {"initializing", "needs_decision", "repairing", "blocked", "abandoned"},
        "initializing": {"planning", "needs_decision", "repairing", "blocked", "abandoned"},
        "planning": {"plan_ready", "needs_decision", "repairing", "blocked", "abandoned"},
        "plan_ready": {"assigning", "needs_decision", "repairing", "blocked", "abandoned"},
        "assigning": {"executing", "needs_decision", "repairing", "blocked", "abandoned"},
        "executing": {"verifying", "needs_decision", "repairing", "blocked", "abandoned"},
        "verifying": {"evaluating", "needs_decision", "repairing", "blocked", "abandoned"},
        "evaluating": {"handoff_ready", "needs_decision", "repairing", "blocked", "abandoned"},
        "handoff_ready": {"ready_to_finish", "needs_decision", "repairing", "blocked", "abandoned"},
        "ready_to_finish": {"done", "needs_decision", "repairing", "blocked", "abandoned"},
        "done": set(),
    },
    "git_finish": {
        "intake": {"planning", "needs_decision", "blocked", "abandoned"},
        "planning": {"verifying", "needs_decision", "blocked", "abandoned"},
        "verifying": {"evaluating", "needs_decision", "blocked", "abandoned"},
        "evaluating": {"handoff_ready", "needs_decision", "blocked", "abandoned"},
        "handoff_ready": {"ready_to_finish", "needs_decision", "blocked", "abandoned"},
        "ready_to_finish": {"done", "needs_decision", "blocked", "abandoned"},
        "done": set(),
    },
}

PHASE_OWNERS = {
    "initializing": "dlc_initializer",
    "planning": "dlc_plan_writer",
    "plan_ready": "dlc_scope_manager",
    "assigning": "dlc_scope_manager",
    "executing": "dlc_repo_worker",
    "verifying": "dlc_verifier",
    "evaluating": "dlc_evaluator",
    "handoff_ready": "dlc_handoff_writer",
    "ready_to_finish": "dlc_git_operator",
}

ROLE_PHASE_ALLOWLIST = {
    "dlc_initializer": {"initializing", "repairing"},
    "dlc_plan_writer": {"planning"},
    "dlc_scope_manager": {"plan_ready", "assigning"},
    "dlc_repo_worker": {"executing"},
    "dlc_verifier": {"verifying"},
    "dlc_evaluator": {"evaluating"},
    "dlc_handoff_writer": {"handoff_ready"},
    "dlc_git_operator": {"ready_to_finish"},
    "dlc_repairer": {"repairing"},
    "dlc_docs_writer": {"planning", "executing"},
    "dlc_explorer": {"planning", "plan_ready", "assigning", "repairing"},
}

STOP_BLOCKING_STATUSES = {
    "planning",
    "plan_ready",
    "assigning",
    "executing",
    "verifying",
    "evaluating",
    "handoff_ready",
    "ready_to_finish",
}

WORKFLOW_AXIS_COMPATIBILITY = {
    "plan_implementation": {"origin_mode": {"new_workspace_from_plan"}, "safety_domain": {"source_change"}},
    "remote_ref_adoption": {"origin_mode": {"from_remote_ref"}},
    "resume_existing": {"origin_mode": {"resume_existing_workspace"}},
    "docs_report": {"origin_mode": {"docs_only_no_workspace"}, "execution_intent": {"docs_only"}, "safety_domain": {"docs_report"}},
    "codex_config_edit": {"safety_domain": {"codex_config_edit"}},
    "git_finish": {"safety_domain": {"git_finish"}},
}


def workflow_from_plan(meta: dict[str, Any]) -> dict[str, Any]:
    workflow = dict(DEFAULT_WORKFLOW)
    configured = meta.get("workflow")
    if isinstance(configured, dict):
        workflow.update(configured)
    return workflow


def workflow_type(meta: dict[str, Any]) -> str:
    value = workflow_from_plan(meta).get("workflow_type")
    return value if isinstance(value, str) and value in WORKFLOW_TYPES else "plan_implementation"


def allowed_transitions(meta: dict[str, Any], status: str) -> set[str]:
    return WORKFLOW_TRANSITIONS.get(workflow_type(meta), WORKFLOW_TRANSITIONS["plan_implementation"]).get(status, set())


def next_agent_for_status(status: str, plan_workflow_type: str = "plan_implementation") -> str | None:
    if plan_workflow_type == "docs_report":
        return {
            "planning": "dlc_docs_writer",
            "executing": "dlc_docs_writer",
            "verifying": "dlc_verifier",
            "handoff_ready": "dlc_handoff_writer",
        }.get(status)
    if plan_workflow_type == "git_finish":
        return {
            "planning": "dlc_verifier",
            "verifying": "dlc_verifier",
            "evaluating": "dlc_evaluator",
            "handoff_ready": "dlc_handoff_writer",
            "ready_to_finish": "dlc_git_operator",
        }.get(status)
    return PHASE_OWNERS.get(status)


def role_allowed_for_phase(meta: dict[str, Any], role: str, status: str | None = None) -> bool:
    phase = str(status or meta.get("status"))
    expected = next_agent_for_status(phase, workflow_type(meta))
    if expected and role == expected:
        return True
    allowed_phases = ROLE_PHASE_ALLOWLIST.get(role, set())
    if phase not in allowed_phases:
        return False
    if workflow_type(meta) == "docs_report":
        return role in {"dlc_docs_writer", "dlc_verifier", "dlc_handoff_writer", "dlc_explorer"}
    if workflow_type(meta) == "git_finish":
        return role in {"dlc_verifier", "dlc_evaluator", "dlc_handoff_writer", "dlc_git_operator", "dlc_explorer"}
    return role != "dlc_docs_writer"


def validate_workflow(meta: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    configured = meta.get("workflow")
    if not isinstance(configured, dict):
        return ["plan.workflow is required"]

    workflow = workflow_from_plan(meta)
    if workflow.get("origin_mode") not in ORIGIN_MODES:
        errors.append("plan.workflow.origin_mode is invalid")
    if workflow.get("execution_intent") not in EXECUTION_INTENTS:
        errors.append("plan.workflow.execution_intent is invalid")
    if workflow.get("safety_domain") not in SAFETY_DOMAINS:
        errors.append("plan.workflow.safety_domain is invalid")
    if workflow.get("workflow_type") not in WORKFLOW_TYPES:
        errors.append("plan.workflow.workflow_type is invalid")
    stage = workflow.get("config_edit_stage")
    if stage is not None and stage not in CONFIG_EDIT_STAGES:
        errors.append("plan.workflow.config_edit_stage is invalid")

    compatibility = WORKFLOW_AXIS_COMPATIBILITY.get(str(workflow.get("workflow_type")), {})
    for key, allowed in compatibility.items():
        if workflow.get(key) not in allowed:
            errors.append(f"plan.workflow.{key} is incompatible with {workflow.get('workflow_type')}")

    if workflow.get("workflow_type") == "codex_config_edit" and not meta.get("hook_contract"):
        errors.append("codex_config_edit requires hook_contract")

    for section in sorted(PLAN_CONTRACT_SECTIONS):
        if section not in meta:
            errors.append(f"plan.{section} is required")

    paths = meta.get("paths")
    if isinstance(paths, dict):
        for key in sorted(PLAN_PATH_KEYS):
            if not paths.get(key):
                errors.append(f"plan.paths.{key} is required")
    elif "paths" in meta:
        errors.append("plan.paths must be an object")

    targets = meta.get("targets")
    if isinstance(targets, dict):
        for key in sorted(PLAN_TARGET_KEYS):
            value = targets.get(key)
            if not isinstance(value, list):
                errors.append(f"plan.targets.{key} must be a list")
    elif "targets" in meta:
        errors.append("plan.targets must be an object")

    phases = meta.get("phases")
    if isinstance(phases, list):
        if not phases:
            errors.append("plan.phases must not be empty")
        for index, phase in enumerate(phases):
            if not isinstance(phase, dict):
                errors.append(f"plan.phases[{index}] must be an object")
                continue
            for key in ["name", "owner", "checkpoints", "outputs", "verification"]:
                if key not in phase:
                    errors.append(f"plan.phases[{index}].{key} is required")
    elif "phases" in meta:
        errors.append("plan.phases must be a list")

    approval_boundary = meta.get("approval_boundary")
    if isinstance(approval_boundary, dict):
        for key in ["allowed_without_user", "requires_user_approval"]:
            if not isinstance(approval_boundary.get(key), list):
                errors.append(f"plan.approval_boundary.{key} must be a list")
    elif "approval_boundary" in meta:
        errors.append("plan.approval_boundary must be an object")

    rollback = meta.get("rollback")
    if isinstance(rollback, dict):
        if not isinstance(rollback.get("commands_or_steps"), list):
            errors.append("plan.rollback.commands_or_steps must be a list")
    elif "rollback" in meta:
        errors.append("plan.rollback must be an object")

    orchestration = meta.get("orchestration")
    if not isinstance(orchestration, dict):
        errors.append("plan.orchestration is required")
    elif orchestration.get("controller_mode") != "orchestrate_only":
        errors.append("plan.orchestration.controller_mode must be orchestrate_only")

    expected_agent = next_agent_for_status(str(meta.get("status")), workflow_type(meta))
    current = meta.get("current") or {}
    if expected_agent and isinstance(current, dict) and current.get("next_agent") != expected_agent:
        errors.append(f"plan.current.next_agent must be {expected_agent} for {workflow_type(meta)} phase {meta.get('status')}")
    return errors


def validate_transition(meta: dict[str, Any], target_status: str) -> list[str]:
    current = str(meta.get("status"))
    if target_status not in allowed_transitions(meta, current):
        return [f"invalid plan transition for {workflow_type(meta)}: {current} -> {target_status}"]
    return []


def apply_transition_side_effects(meta: dict[str, Any], target_status: str) -> None:
    current = meta.setdefault("current", {})
    current["phase"] = target_status
    next_agent = next_agent_for_status(target_status, workflow_type(meta))
    if next_agent:
        current["next_action_type"] = "delegate"
        current["next_agent"] = next_agent
        current["next_action"] = f"Delegate {target_status} phase to {next_agent}."
        current["stop_condition"] = f"{next_agent} report for {target_status} is recorded."


def stop_missing_obligation(root: Path, meta: dict[str, Any]) -> str | None:
    status = str(meta.get("status"))
    if status not in STOP_BLOCKING_STATUSES:
        return None
    if scoped_break_glass_allowed(root, "validator_bypass_once"):
        return None
    current = meta.get("current") or {}
    if not isinstance(current, dict):
        return f"AI-DLC: plan status {status} is missing current phase context before Stop."
    next_agent = current.get("next_agent") or next_agent_for_status(status, workflow_type(meta))
    stop_condition = current.get("stop_condition") or "phase deliverable is recorded"
    if not next_agent:
        return f"AI-DLC: plan status {status} has no next_agent; record a decision or transition before Stop."
    return f"AI-DLC: phase {status} requires {next_agent}; Stop is blocked until {stop_condition}."


def scoped_break_glass_allowed(root: Path, override_type: str, rel_paths: list[str] | None = None) -> bool:
    try:
        workspace = read_data(root / "workspace.yaml")
        decisions_path = root / workspace["paths"]["decisions"]
    except Exception:
        decisions_path = root / "ai-dlc" / "decisions.md"
    if not decisions_path.exists():
        return False

    _, text = read_frontmatter(decisions_path)
    fields = _break_glass_fields(text, override_type)
    if fields is None:
        return False
    if not fields.get("reason"):
        return False
    expires_at = fields.get("expires_at")
    if not expires_at:
        return False
    try:
        if datetime.fromisoformat(expires_at) <= datetime.now().astimezone():
            return False
    except ValueError:
        return False
    scope = fields.get("scope")
    if rel_paths is not None:
        if not scope:
            return False
        return all(path == scope or path.startswith(scope.rstrip("/") + "/") for path in rel_paths)
    return True


def _break_glass_fields(text: str, override_type: str) -> dict[str, str] | None:
    marker = f"allow-break-glass: {override_type}"
    lines = text.splitlines()
    for index in range(len(lines) - 1, -1, -1):
        if marker not in lines[index]:
            continue
        fields: dict[str, str] = {}
        for raw_line in lines[index + 1:]:
            line = raw_line.strip()
            if not line:
                break
            if "allow-break-glass:" in line:
                break
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields[key.strip().lstrip("- ").strip()] = value.strip()
        return fields
    return None
