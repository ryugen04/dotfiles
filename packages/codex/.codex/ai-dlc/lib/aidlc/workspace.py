from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from .git_hooks import install_project_hooks
from .io import ensure_dir, now_iso, write_data, write_frontmatter, write_text


def parse_keyed_args(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid key=value argument: {value}")
        key, parsed_value = value.split("=", 1)
        parsed[key] = parsed_value
    return parsed


def parse_repo_args(values: list[str]) -> dict[str, str]:
    repos = parse_keyed_args(values)
    return {name: str(Path(path).expanduser()) for name, path in repos.items()}


def _abs(value: str | Path) -> str:
    return str(Path(value).expanduser().resolve())


def _ancestor_with(start: Path, relative: str) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / relative).exists():
            return candidate
    return None


def stable_project_id(path: Path) -> str:
    resolved = path.expanduser().resolve()
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", resolved.name).strip("-._").lower() or "project"
    digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{digest}"


def codex_user_workspace_root(path: Path) -> Path:
    return Path.home() / ".codex" / "ai-dlc" / "user-workspaces" / stable_project_id(path)


def cleanup_user_context(start: Path) -> dict:
    current = start.expanduser().resolve()
    context = ai_dlc_context(current)
    if context.get("control_plane_scope") != "user_local":
        return {
            "status": "skipped",
            "reason": "not using Codex user-local fallback state",
            "mode": context.get("mode", "unknown"),
            "root": context.get("root", ""),
        }

    target = Path(context["root"]).expanduser()
    base = Path.home() / ".codex" / "ai-dlc" / "user-workspaces"
    try:
        target.resolve().relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"refusing to remove context outside user-workspaces: {target}") from exc

    if not target.exists():
        return {"status": "absent", "root": str(target)}

    shutil.rmtree(target)
    return {"status": "deleted", "root": str(target)}


def ai_dlc_context(start: Path, *, ensure_user_local: bool = False) -> dict:
    current = start.expanduser().resolve()
    workspace_root = _ancestor_with(current, "workspace.yaml")
    if workspace_root is not None:
        return {
            "mode": "task_workspace",
            "control_plane_scope": "project",
            "root": str(workspace_root),
            "user_local_root": "",
            "recommendation": "Use the existing AI-DLC task workspace.",
        }

    project_root = _ancestor_with(current, "ai-dlc/project-metadata.yaml")
    if project_root is None:
        project_root = _ancestor_with(current, "sango.yaml")
    if project_root is not None:
        return {
            "mode": "project_root",
            "control_plane_scope": "project",
            "root": str(project_root),
            "user_local_root": "",
            "recommendation": "Use the existing project-local AI-DLC control-plane.",
        }

    user_root = codex_user_workspace_root(current)
    if ensure_user_local:
        for name in [
            "plans",
            "decisions",
            "docs",
            "evidence",
            "handoff",
            "quality",
            "logs",
            "assignments",
            "leases",
            "locks",
            "reports",
        ]:
            ensure_dir(user_root / name)
        context_path = user_root / "context.yaml"
        if not context_path.exists():
            write_data(
                context_path,
                {
                    "schema": "ai-dlc.user_context.v1",
                    "project_id": stable_project_id(current),
                    "source_path": str(current),
                    "control_plane_scope": "user_local",
                    "created_at": now_iso(),
                        "recommendation": (
                            "Project-local AI-DLC is recommended for durable team workflows; "
                            "plan-driven repos should add .codex/config.toml with hooks enabled "
                            "and guardrails.subagent_required=true before source edits. "
                            "This user-local context is Codex-owned fallback state."
                        ),
                },
            )

    exists = user_root.exists()
    return {
        "mode": "user_local_available" if exists else "none",
        "control_plane_scope": "user_local" if exists else "none",
        "root": str(user_root) if exists else "",
        "user_local_root": str(user_root),
        "recommendation": (
            "Project-local AI-DLC is recommended. For plan-driven work, add `.codex/config.toml` with "
            "`hooks = true` and `guardrails.subagent_required = true`; use `ai-dlc ensure-context` "
            "only as Codex user-local fallback state."
            if not exists
            else "Using Codex user-local AI-DLC fallback. Add project-local `.codex/config.toml` with "
            "`hooks = true` and `guardrails.subagent_required = true` before source edits, or consider `ai-dlc init-project` "
            "when this should become project-local."
        ),
    }


def _repo_metadata(
    repos: dict[str, str],
    branch: str,
    repo_urls: dict[str, str] | None,
    repo_base_refs: dict[str, str] | None,
) -> dict[str, dict]:
    repo_urls = repo_urls or {}
    repo_base_refs = repo_base_refs or {}
    metadata: dict[str, dict] = {}
    for name, path in repos.items():
        metadata[name] = {
            "path": name,
            "role": name,
            "canonical_repo_path": _abs(path),
            "canonical_repo_url": repo_urls.get(name) or _repo_url(Path(path)),
            "default_branch": "main",
            "issue_branch": branch,
            "base_ref": repo_base_refs.get(name, "origin/main"),
            "base_sha": _git_ref(Path(path), repo_base_refs.get(name, "origin/main")),
            "head_sha": _git_ref(Path(path), "HEAD"),
            "overlay": {
                "embedded": True,
                "parent_tracked": True,
                "git_controller": f"../.local/gitdirs/{name}.git",
                "tracked_output_prefixes": [f"{name}/src/**", f"{name}/tests/**"],
            },
        }
    return metadata


def _run_git(repo: Path, args: list[str]) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _repo_url(repo: Path) -> str:
    try:
        url = _run_git(repo, ["remote", "get-url", "origin"])
    except Exception as exc:
        raise ValueError(f"canonical repo URL is required for {repo}") from exc
    if not url:
        raise ValueError(f"canonical repo URL is required for {repo}")
    return url


def _git_ref(repo: Path, ref: str) -> str:
    candidates = [ref]
    if ref.startswith("origin/"):
        candidates.append(ref.split("/", 1)[1])
    candidates.append("HEAD")
    for candidate in candidates:
        result = subprocess.run(["git", "rev-parse", "--verify", candidate], cwd=repo, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    raise ValueError(f"unable to resolve git ref {ref} for {repo}")


def project_agents_md() -> str:
    return """# root-system AGENTS.md

This repository is an AI-DLC control-plane workspace.

Facts are declared in `workspace.yaml`.
Plans are stored in `ai-dlc/plans`.
Machine-readable work items are stored in `ai-dlc/work-items`.
Verification evidence is stored in `ai-dlc/evidence`.
Runtime leases, locks, logs, and reports live under `../.local`.

The root-system session is controller-only.
Substantive work must be delegated to AI-DLC subagents.
"""


def controller_only_agents_md() -> str:
    return """# controller-only AGENTS.md

This repository is not an AI-DLC workspace.

The local Codex session is controller-only.
Direct edits are blocked.
Use delegation or approved bootstrap commands only.
"""


def project_codex_config() -> str:
    return """# root-system project config
sandbox_mode = "workspace-write"
approval_policy = "on-request"

[features]
hooks = true
shell_snapshot = true

[sandbox_workspace_write]
writable_roots = ["../.local"]
network_access = false

[guardrails]
subagent_required = true
"""


def controller_only_project_codex_config() -> str:
    return """# controller-only project config
sandbox_mode = "workspace-write"
approval_policy = "on-request"

[features]
hooks = true
shell_snapshot = true

[guardrails]
subagent_required = true
"""


def project_gitignore() -> str:
    return """ai-dlc/executions/
ai-dlc/scratch/
.local/
logs/
tmp/
*.log
.env
.env.*
!.env.example
"""


def _write_text_if_missing(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    if path.exists():
        return
    path.write_text(text, encoding="utf-8")


def _git_ok(repo: Path, args: list[str]) -> bool:
    return subprocess.run(["git", *args], cwd=repo, check=False, capture_output=True, text=True).returncode == 0


def _has_remote_url(repo: Path, remote: str = "origin") -> bool:
    result = subprocess.run(["git", "remote", "get-url", remote], cwd=repo, check=False, capture_output=True, text=True)
    return result.returncode == 0 and bool(result.stdout.strip())


def init_workspace_prerequisite_errors(
    root: Path,
    repos: dict[str, str],
    *,
    root_canonical_path: str | None = None,
    root_canonical_url: str = "",
    repo_urls: dict[str, str] | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    next_actions: list[str] = []
    repo_urls = repo_urls or {}
    root_repo = Path(root_canonical_path or root).expanduser().resolve()

    if not _git_ok(root_repo, ["rev-parse", "--show-toplevel"]):
        errors.append(f"root-system repo is not a git repository: {root_repo}")
        next_actions.append(f"`git -C {root_repo} init -b main` などで root-system repo を初期化する")
    else:
        if not _git_ok(root_repo, ["rev-parse", "--verify", "HEAD"]):
            errors.append(f"root-system repo does not have an initial commit yet: {root_repo}")
            next_actions.append(f"`git -C {root_repo} add . && git -C {root_repo} commit -m init` で初回 commit を作る")
        if not root_canonical_url and not _has_remote_url(root_repo):
            errors.append(f"root-system canonical repo URL is unavailable for {root_repo}")
            next_actions.append("root-system に `origin` remote を追加するか、`ai-dlc init-workspace --root-canonical-url ...` を指定する")

    for name, raw_path in repos.items():
        repo = Path(raw_path).expanduser().resolve()
        if not repo.exists():
            errors.append(f"repo path is missing for {name}: {repo}")
            next_actions.append(f"`--repo {name}=...` に実在する path を指定する")
            continue
        if not _git_ok(repo, ["rev-parse", "--show-toplevel"]):
            errors.append(f"child repo is not a git repository for {name}: {repo}")
            next_actions.append(f"`git -C {repo} init -b main` などで {name} repo を初期化する")
            continue
        if not _git_ok(repo, ["rev-parse", "--verify", "HEAD"]):
            errors.append(f"child repo does not have an initial commit for {name}: {repo}")
            next_actions.append(f"`git -C {repo} add . && git -C {repo} commit -m init` で {name} の初回 commit を作る")
        if not repo_urls.get(name) and not _has_remote_url(repo):
            errors.append(f"canonical repo URL is unavailable for {name}: {repo}")
            next_actions.append(f"{name} に `origin` remote を追加するか、`ai-dlc init-workspace --repo-url {name}=...` を指定する")

    return errors, list(dict.fromkeys(next_actions))


def default_plan_body(
    workspace_id: str,
    issue_title: str,
    issue_url: str,
    repo_names: list[str],
    root_export_target: str,
    workspace_root: str,
    root_system_path: str,
    base_ref: str,
) -> str:
    repos = ", ".join(repo_names)
    return f"""# {workspace_id}: {issue_title}

## Goal

- Linear: {issue_url}
- Repositories: {repos}
- Workspace root: {workspace_root}
- root-system path: {root_system_path}
- Base ref: {base_ref}

## Sprint contract

### Scope

- Fill active work items before implementation.

### Exclusions

- No out-of-scope repo edits.

## Acceptance criteria

- Work items define repo ownership, writable scopes, verifier gate, and evaluator gate.
- Evidence links back to a verified branch and HEAD.
- Root export target is `{root_export_target}`.
- Output ownership:
  - plan/decisions: dlc_plan_writer
  - work-items: dlc_scope_manager
  - evidence: dlc_verifier / dlc_evaluator
  - handoff: dlc_handoff_writer

## Cross-repo contract

- root-system is controller-only.
- Child repo edits require assignments and leases.
- verifier evidence must precede evaluator verdict.
- finish-stage Git operations require `dlc_git_operator`.
- Workflow type is `plan_implementation` unless the plan frontmatter explicitly states otherwise.
- Controller remains orchestrator-only; phase work is delegated to the phase owner subagent.

## Work items

See `ai-dlc/work-items/{workspace_id}.yaml`.

## Verification evidence

See `ai-dlc/evidence/{workspace_id}.yaml`.

## Decisions

See `ai-dlc/decisions/{workspace_id}.md`.

## Current risks

- Overlay and hardening must remain valid.
"""


def default_handoff_body(
    workspace_id: str,
    issue_url: str,
    branch: str,
    repo_names: list[str],
    root_export_target: str,
    workspace_root: str,
) -> str:
    repo_sections = "\n\n".join(
        f"### {repo_name}\n\n- branch: {branch}\n- dirty: unrecorded\n- do-not-touch: follow assignment writable contract" for repo_name in repo_names
    )
    return f"""# {workspace_id} Handoff

## Issue

- url: {issue_url}
- issue branch: {branch}
- root export target: {root_export_target}
- workspace root: {workspace_root}

## Current status

- plan status: planning
- active item: none
- active assignments: none
- assignment detail: see `../.local/ai-dlc/assignments`
- overlay mode: literal_worktree_overlay

## Branch map

- root-system: {branch}
{chr(10).join(f"- {repo_name}: {branch}" for repo_name in repo_names)}

## Lease sessions

- none
- lease detail: see `../.local/ai-dlc/leases`

## Pending obligations

- verifier: confirm active repo HEAD and clean tree
- evaluator: record quality verdict after verifier evidence
- handoff_writer: refresh assignment and branch state before finish
- root-export: confirm branch `{root_export_target}` is root-only before push

## Verified state

- verifier evidence: pending
- evaluator verdict: pending
- root-export status: pending

## Changes this session

{repo_sections}

## Root-system

- tracked outputs only

## Blockers

- none recorded

## Next best action

- next_agent: dlc_plan_writer
- next_action: complete the workflow plan, checkpoints, and approval gates

## Do not touch

- embedded repos from root commit path

## Commands

- ai-dlc validate-overlay
- ai-dlc validate
"""


def default_handoff_meta(workspace_id: str, issue_url: str, branch: str, root_export_target: str, repo_names: list[str]) -> dict[str, object]:
    return {
        "schema": "ai-dlc.handoff.v1",
        "workspace_id": workspace_id,
        "issue_url": issue_url,
        "issue_branch": branch,
        "root_export_target": root_export_target,
        "active_assignments": [],
        "lease_sessions": [],
        "branch_map": {"root-system": branch, **{name: branch for name in repo_names}},
        "pending_obligations": ["verifier", "evaluator", "handoff_writer"],
    }


def default_decisions_body(workspace_id: str, issue_url: str) -> str:
    return f"""# {workspace_id} Decisions

- workspace_id: {workspace_id}
- issue: {issue_url}
- timestamp: unrecorded
- actor_role: unrecorded
- affected_stage: unrecorded
- rationale: record deviations from the default orchestration here.
- approval_boundary: unrecorded
- allow-next-agent: none
"""


def default_decisions_meta(workspace_id: str, issue_url: str) -> dict[str, object]:
    return {
        "schema": "ai-dlc.decisions.v1",
        "workspace_id": workspace_id,
        "issue_url": issue_url,
        "timestamp": "unrecorded",
        "actor_role": "unrecorded",
        "affected_stage": "unrecorded",
        "approval_boundary": "unrecorded",
        "allow_next_agent": [],
    }


def default_quality_body(workspace_id: str, issue_url: str) -> str:
    return f"""# {workspace_id} Quality

- issue: {issue_url}
- evaluator verdict: pending
- evidence coverage: pending
- residual risks: none recorded
- finish recommendation: pending
"""


def init_project(
    root_system: Path,
    repo_paths: dict[str, str] | None = None,
    repo_urls: dict[str, str] | None = None,
    *,
    project_kind: str = "root-system",
) -> None:
    ensure_dir(root_system / ".codex")
    if project_kind == "controller-only":
        write_text(root_system / "AGENTS.md", controller_only_agents_md())
        _write_text_if_missing(root_system / ".codex" / "config.toml", controller_only_project_codex_config())
        return

    ensure_dir(root_system / "ai-dlc")
    write_text(root_system / "AGENTS.md", project_agents_md())
    _write_text_if_missing(root_system / ".codex" / "config.toml", project_codex_config())
    write_text(root_system / ".gitignore", project_gitignore())
    write_text(root_system / "ai-dlc" / ".gitkeep", "")
    if repo_paths or repo_urls:
        metadata = {
            "schema": "ai-dlc.project-init.v1",
            "root_system_path": _abs(root_system),
            "repos": {name: {"path": _abs(path), "url": (repo_urls or {}).get(name, "")} for name, path in (repo_paths or {}).items()},
        }
        write_data(root_system / "ai-dlc" / "project-metadata.yaml", metadata)


def scaffold_workspace(
    root: Path,
    issue: str,
    branch: str,
    repos: dict[str, str],
    mode: str,
    *,
    issue_url: str = "",
    issue_title: str | None = None,
    base_ref: str = "origin/main",
    root_export_target: str = "main",
    root_export_remote: str = "origin",
    workspace_root: str | None = None,
    root_canonical_path: str | None = None,
    root_canonical_url: str = "",
    repo_urls: dict[str, str] | None = None,
    repo_base_refs: dict[str, str] | None = None,
) -> None:
    repo_names = list(repos.keys())
    workspace_root = _abs(workspace_root or root.parent)
    root_system_path = _abs(root)
    root_canonical_path = _abs(root_canonical_path or root)
    local_root = root.parent / ".local"
    local_root_abs = _abs(local_root)
    repo_urls = repo_urls or {}
    repo_base_refs = repo_base_refs or {}
    root_canonical_url = root_canonical_url or repo_urls.get("root-system") or _repo_url(Path(root_canonical_path))
    issue_title = issue_title or issue
    paths = {
        "overlay": f"ai-dlc/overlay/{issue}.yaml",
        "bootstrap": f"ai-dlc/bootstrap/{issue}.yaml",
        "plan": f"ai-dlc/plans/{issue}.md",
        "work_items": f"ai-dlc/work-items/{issue}.yaml",
        "decisions": f"ai-dlc/decisions/{issue}.md",
        "evidence": f"ai-dlc/evidence/{issue}.yaml",
        "handoff": f"ai-dlc/handoff/{issue}.md",
        "quality": f"ai-dlc/quality/{issue}.md",
    }
    repo_entries = _repo_metadata(repos, branch, repo_urls, repo_base_refs)
    workspace = {
        "schema": "ai-dlc.workspace.v1",
        "id": issue,
        "title": issue_title,
        "issue": {"tracker": "linear", "id": issue, "url": issue_url},
        "workspace": {
            "root": workspace_root,
            "root_system_path": root_system_path,
            "root_canonical_path": root_canonical_path,
            "local_path": local_root_abs,
        },
        "branch": {
            "issue": branch,
            "base_ref": base_ref,
            "by_repo": {
                "root-system": repo_base_refs.get("root-system", base_ref),
                **{name: repo_base_refs.get(name, base_ref) for name in repo_names},
            },
            "root_export": {
                "target_repo": "root-system",
                "target_remote": root_export_remote,
                "target_ref": root_export_target,
                "export_mode": "root_only",
            },
        },
        "layout": {"mode": mode, "root_diff_hack": True},
        "repos": {
            "root-system": {
                "path": ".",
                "role": "control-plane",
                "canonical_repo_path": root_canonical_path,
                "canonical_repo_url": root_canonical_url,
                "default_branch": "main",
                "issue_branch": branch,
                "base_ref": repo_base_refs.get("root-system", base_ref),
                "base_sha": _git_ref(Path(root_canonical_path), repo_base_refs.get("root-system", base_ref)),
                "head_sha": _git_ref(Path(root_canonical_path), "HEAD"),
            },
            **repo_entries,
        },
        "paths": {"local": "../.local", **paths},
        "controller": {"no_direct_edits": True, "substantive_work_requires_subagent": True},
        "workflow": {"wip_limit": 1, "subagent_required": True},
        "hardening": {
            "destructive_git_guard": {
                "required": True,
                "mode": "git_shim",
                "path": "../.local/bin/ai-dlc-git-shim/git",
            }
        },
    }
    write_data(root / "workspace.yaml", workspace)

    overlay = {
        "schema": "ai-dlc.overlay.v1",
        "workspace_id": issue,
        "issue": {"id": issue, "url": issue_url},
        "mode": mode,
        "baseline": {
            "status": "pending",
            "root_commit": None,
            "created_at": now_iso(),
            "local_only": True,
            "must_not_push": True,
            "must_not_merge_to_main": True,
        },
        "embedded_repos": [
            {
                "name": name,
                "path": name,
                "branch": branch,
                "base_ref": repo_base_refs.get(name, base_ref),
                "base_sha": repo_entries[name]["base_sha"],
                "head_sha": repo_entries[name]["head_sha"],
                "controller": f"../.local/gitdirs/{name}.git",
                "tracked_files_ref": f"../.local/overlay/{name}.tracked.z",
                "baseline_tree_recorded_by_root": False,
                "baseline_tracked_file_count": 0,
                "gitfile_restored": False,
                "recovery": {
                    "gitfile_backup": f"../.local/overlay/gitfiles/{name}.gitfile",
                    "restore_required": False,
                    "last_attempt_at": now_iso(),
                },
            }
            for name in repo_names
        ],
        "root_commit_policy": {
            "embedded_paths": repo_names,
            "allow_embedded_paths_only_for_baseline": True,
            "forbid_root_push": True,
            "forbid_root_merge_directly": True,
        },
        "finish_policy": {
            "child_repos_commit_normally": True,
            "root_system_export_root_only": True,
            "excluded_from_root_export": repo_names,
        },
    }
    bootstrap = {
        "schema": "ai-dlc.bootstrap.v1",
        "workspace_id": issue,
        "issue": {"tracker": "linear", "id": issue, "url": issue_url},
        "workspace_ref": "workspace.yaml",
        "status": "pending",
        "readiness": {
            "can_start": "pending",
            "can_test": "pending",
            "can_see_progress": "pending",
            "can_pick_next_step": "pending",
        },
        "root_export": workspace["branch"]["root_export"],
        "overlay": {"status": "pending", "validate_command": "ai-dlc validate-overlay"},
        "hooks": {"status": "pending", "destructive_git_guard": "pending"},
        "repos": {
            name: {
                "path": name,
                "branch": branch,
                "base_ref": repo_base_refs.get(name, base_ref),
                "base_sha": repo_entries[name]["base_sha"],
                "head_sha": repo_entries[name]["head_sha"],
                "baseline": {
                    "install": {"command": "pnpm install", "status": "pending", "evidence_ref": None},
                    "test": {"command": "pnpm test", "status": "pending", "evidence_ref": None},
                },
            }
            for name in repo_names
        },
        "blockers": [],
        "next_agent": "dlc_initializer",
        "next_action": "Validate overlay, hooks, hardening, and child repo readiness.",
    }
    work_items = {
        "schema": "ai-dlc.work_items.v1",
        "workspace_id": issue,
        "issue": {"tracker": "linear", "id": issue, "url": issue_url},
        "plan_ref": paths["plan"],
        "wip_limit": 1,
        "active_item": None,
        "items": [],
        "item_template": {
            "id": "WI-001",
            "title": "Describe the concrete implementation slice",
            "status": "not_started",
            "repo": repo_names[0] if repo_names else "root-system",
            "source_ref": paths["plan"],
            "writable": ["<repo>/**"],
            "deliverables": ["worker_report", "verifier_evidence", "evaluator_verdict"],
            "blocked_by": [],
            "verifier_gate": {"phase": "verifying", "assignment_role": "dlc_verifier"},
            "evaluator_gate": {"phase": "evaluating", "assignment_role": "dlc_evaluator"},
        },
    }
    evidence = {
        "schema": "ai-dlc.evidence.v1",
        "workspace_id": issue,
        "items": {},
        "diff_inspection": {
            "status": "pending",
            "method": "root_system_overlay_diff",
            "repos": repo_names,
            "notes": "Subrepo diffs are expected to appear as normal root-system file diffs through literal_worktree_overlay.",
        },
        "clean_state": {
            "build": {"status": "pending", "evidence_ref": None},
            "tests": {"status": "pending", "evidence_ref": None},
            "progress": {"status": "pending", "files": [paths["work_items"], paths["handoff"], paths["quality"]]},
            "artifacts": {
                "status": "pending",
                "checks": ["no_debug_files", "no_untracked_temp_files", "root_embedded_paths_not_staged"],
            },
            "startup": {"status": "pending", "evidence_ref": None},
        },
        "verifier_log": [],
        "evaluator_log": [],
        "entry_template": {
            "repo": repo_names[0] if repo_names else "root-system",
            "issue_branch": branch,
            "head_sha": "<verified head sha>",
            "tree_clean": True,
            "recorded_by": "dlc_verifier",
            "work_item": "WI-001",
            "command": "<verification command>",
            "expected_outcome": "<expected result>",
            "actual_result": "<actual result>",
            "log_ref": "../.local/ai-dlc/logs/<log file>",
            "verdict": "pending",
            "artifact_refs": [],
        },
    }
    plan_meta = {
        "schema": "ai-dlc.plan.v2",
        "id": issue,
        "title": issue_title,
        "status": "planning",
        "issue": {"tracker": "linear", "id": issue, "url": issue_url},
        "workspace_ref": "workspace.yaml",
        "overlay_ref": paths["overlay"],
        "bootstrap_ref": paths["bootstrap"],
        "work_items_ref": paths["work_items"],
        "evidence_ref": paths["evidence"],
        "handoff_ref": paths["handoff"],
        "root_export": workspace["branch"]["root_export"],
        "target_repos": repo_names,
        "controller": {"no_direct_edits": True, "substantive_work_requires_subagent": True},
        "paths": {
            "plan": paths["plan"],
            "decisions": paths["decisions"],
            "work_items": paths["work_items"],
            "evidence": paths["evidence"],
            "handoff": paths["handoff"],
            "quality": paths["quality"],
        },
        "targets": {
            "repos": repo_names,
            "worktrees": [workspace_root],
            "writable": ["ai-dlc/plans/**", "ai-dlc/work-items/**", "ai-dlc/evidence/**", "ai-dlc/handoff/**", "ai-dlc/quality/**", *[f"{name}/**" for name in repo_names]],
            "forbidden": ["workspace.yaml", ".codex/**"],
        },
        "phases": [
            {
                "name": "planning",
                "owner": "dlc_plan_writer",
                "checkpoints": ["goal/scope/out-of-scope recorded", "workflow axes recorded", "approval boundary recorded"],
                "outputs": [paths["plan"], paths["decisions"]],
                "verification": ["ai-dlc validate"],
            },
            {
                "name": "plan_ready",
                "owner": "dlc_scope_manager",
                "checkpoints": ["work items map to plan", "WIP limit remains 1"],
                "outputs": [paths["work_items"]],
                "verification": ["ai-dlc validate"],
            },
            {
                "name": "assigning",
                "owner": "dlc_scope_manager",
                "checkpoints": ["active item selected", "assignment writable/forbidden scopes recorded"],
                "outputs": [paths["work_items"], "../.local/ai-dlc/assignments"],
                "verification": ["ai-dlc validate"],
            },
            {
                "name": "executing",
                "owner": "dlc_repo_worker",
                "checkpoints": ["repo worker assignment claimed", "worker report recorded"],
                "outputs": ["../.local/ai-dlc/reports"],
                "verification": ["active work item verifier gate"],
            },
            {
                "name": "verifying",
                "owner": "dlc_verifier",
                "checkpoints": ["required commands run", "evidence_ref recorded"],
                "outputs": [paths["evidence"], "../.local/ai-dlc/logs"],
                "verification": ["ai-dlc validate"],
            },
            {
                "name": "evaluating",
                "owner": "dlc_evaluator",
                "checkpoints": ["independent review recorded", "residual risk listed"],
                "outputs": [paths["evidence"], paths["quality"]],
                "verification": ["ai-dlc validate"],
            },
            {
                "name": "handoff_ready",
                "owner": "dlc_handoff_writer",
                "checkpoints": ["handoff refreshed", "pending obligations listed"],
                "outputs": [paths["handoff"]],
                "verification": ["ai-dlc validate"],
            },
            {
                "name": "ready_to_finish",
                "owner": "dlc_git_operator",
                "checkpoints": ["user approval exists for git boundary", "commit/export/push boundary recorded"],
                "outputs": [paths["handoff"], paths["evidence"]],
                "verification": ["ai-dlc validate", "ai-dlc clean-state-check"],
            },
        ],
        "approval_boundary": {
            "allowed_without_user": ["read-only inspection", "plan/work-item/evidence validation", "assigned lease-scoped edits"],
            "requires_user_approval": ["dependency download", "git commit", "git push", "PR create", "root-export", "overlay-cleanup", "destructive cleanup"],
        },
        "rollback": {
            "commands_or_steps": [
                "stop and record blocker in decisions",
                "release owned assignment leases",
                "do not discard local changes without explicit user approval",
            ]
        },
        "workflow": {
            "origin_mode": "new_workspace_from_plan",
            "execution_intent": "docs_then_impl",
            "safety_domain": "source_change",
            "workflow_type": "plan_implementation",
            "config_edit_stage": None,
        },
        "orchestration": {
            "controller_mode": "orchestrate_only",
            "controller_allowed_actions": ["inspect", "classify", "assign", "spawn", "integrate", "transition", "report"],
            "controller_forbidden_actions": ["source_edit", "evidence_substitution", "evaluator_substitution", "git_finish"],
            "phase_ownership": {
                "planning": "dlc_plan_writer",
                "plan_ready": "dlc_scope_manager",
                "assigning": "dlc_scope_manager",
                "executing": "dlc_repo_worker",
                "verifying": "dlc_verifier",
                "evaluating": "dlc_evaluator",
                "handoff_ready": "dlc_handoff_writer",
                "ready_to_finish": "dlc_git_operator",
            },
        },
        "hook_contract": {
            "PreToolUse": "enforce lease, writable scope, workflow type, and break-glass scope",
            "PermissionRequest": "gate escalation against approval boundary",
            "PostToolUse": "record drift and evidence obligations",
            "Stop": "block missing phase deliverables without creating deadlocks",
        },
        "evidence_contract": {
            "requires_phase_owner_report": True,
            "requires_verifier_before_evaluator": True,
            "requires_handoff_before_finish": True,
        },
        "current": {
            "active_item": None,
            "phase": "planning",
            "next_action_type": "delegate",
            "next_agent": "dlc_plan_writer",
            "next_action": "Complete initial plan, workflow classification, checkpoints, and approval gates.",
            "stop_condition": "dlc_plan_writer report for planning is recorded.",
        },
        "deadlock_policy": {
            "max_same_failure_attempts": 2,
            "max_repair_attempts": 1,
            "stop_hook_max_continuations_per_turn": 1,
        },
    }

    write_data(root / paths["overlay"], overlay)
    write_data(root / paths["bootstrap"], bootstrap)
    write_data(root / paths["work_items"], work_items)
    write_data(root / paths["evidence"], evidence)
    write_frontmatter(
        root / paths["plan"],
        plan_meta,
        default_plan_body(issue, issue_title, issue_url, repo_names, root_export_target, workspace_root, root_system_path, base_ref),
    )
    write_frontmatter(root / paths["decisions"], default_decisions_meta(issue, issue_url), default_decisions_body(issue, issue_url))
    write_frontmatter(
        root / paths["handoff"],
        default_handoff_meta(issue, issue_url, branch, root_export_target, repo_names),
        default_handoff_body(issue, issue_url, branch, repo_names, root_export_target, workspace_root),
    )
    write_text(root / paths["quality"], default_quality_body(issue, issue_url))

    for relative in [
        "gitdirs",
        "overlay/gitfiles",
        "overlay",
        "bin/ai-dlc-git-shim",
        "ai-dlc/assignments",
        "ai-dlc/leases",
        "ai-dlc/locks",
        "ai-dlc/reports",
        "ai-dlc/logs",
        "ai-dlc/traces",
        "env",
        "tmp",
    ]:
        ensure_dir(local_root / relative)

    install_project_hooks(root)
