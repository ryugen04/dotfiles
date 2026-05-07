from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .git_hooks import install_project_hooks
from .hooks import diagnose_block, dispatch
from .overlay import overlay_cleanup, overlay_init, overlay_repair, overlay_status, root_export, validate_overlay
from .state import (
    agent_claim,
    agent_release,
    agent_report,
    assignment_create,
    assignment_list,
    assignment_update_status,
    block_record,
    bootstrap,
    clean_state_check,
    deadlock_check,
    evidence_record,
    finish,
    invalidate,
    lock_list,
    lock_release,
    transition,
    validate,
    verify_gate,
    work_item_activate,
    work_item_block,
    work_item_cancel,
    workspace_status,
)
from .validators import assert_overlay, assert_workspace
from .workspace import ai_dlc_context, cleanup_user_context, init_project, init_workspace_prerequisite_errors, parse_keyed_args, parse_repo_args, scaffold_workspace


def find_workspace_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "workspace.yaml").exists():
            return candidate
    raise FileNotFoundError("workspace.yaml not found")


def find_assignment_context_root(start: Path) -> Path:
    try:
        return find_workspace_root(start)
    except FileNotFoundError:
        return start


def cmd_install(_: argparse.Namespace) -> int:
    home = Path.home()
    status = {
        "~/.codex": (home / ".codex").exists(),
        "~/.agents/skills": (home / ".agents" / "skills").exists(),
        "~/.codex/ai-dlc/bin": (home / ".codex" / "ai-dlc" / "bin").exists(),
        "codex_hooks": True,
    }
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    home = Path.home()
    checks = {
        "codex_config": (home / ".codex" / "config.toml").exists(),
        "codex_hooks": (home / ".codex" / "hooks.json").exists(),
        "ai_dlc_bin": (home / ".codex" / "ai-dlc" / "bin" / "ai-dlc").exists(),
        "skills_dir": (home / ".agents" / "skills").exists(),
        "python_yaml": True,
    }
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    return 0 if all(checks.values()) else 1


def cmd_init_project(args: argparse.Namespace) -> int:
    repo_paths = parse_repo_args(args.repo) if args.repo else {}
    repo_urls = parse_keyed_args(args.repo_url) if args.repo_url else {}
    init_project(
        Path(args.root_system).resolve(),
        repo_paths=repo_paths,
        repo_urls=repo_urls,
        project_kind=args.project_kind,
    )
    return 0


def cmd_init_workspace(args: argparse.Namespace) -> int:
    root = Path.cwd()
    repos = parse_repo_args(args.repo)
    repo_urls = parse_keyed_args(args.repo_url) if args.repo_url else {}
    repo_base_refs = parse_keyed_args(args.repo_base_ref) if args.repo_base_ref else {}
    errors, next_actions = init_workspace_prerequisite_errors(
        root,
        repos,
        root_canonical_path=args.root_canonical_path,
        root_canonical_url=args.root_canonical_url,
        repo_urls=repo_urls,
    )
    if errors:
        lines = ["init-workspace prerequisites are not met:"]
        lines.extend(f"- {error}" for error in errors)
        if next_actions:
            lines.append("")
            lines.append("Next actions:")
            lines.extend(f"- {action}" for action in next_actions)
        raise ValueError("\n".join(lines))
    scaffold_workspace(
        root,
        args.issue,
        args.branch,
        repos,
        args.mode,
        issue_url=args.issue_url,
        issue_title=args.issue_title,
        base_ref=args.base_ref,
        root_export_target=args.root_export_target,
        root_export_remote=args.root_export_remote,
        workspace_root=args.workspace_root,
        root_canonical_path=args.root_canonical_path,
        root_canonical_url=args.root_canonical_url,
        repo_urls=repo_urls,
        repo_base_refs=repo_base_refs,
    )
    overlay_init(root, args.issue, args.branch, repos)
    install_project_hooks(root, [root / name for name in repos])
    assert_overlay(root)
    if validate(root):
        raise ValueError("\n".join(validate(root)))
    return 0


def cmd_overlay_init(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    repos = parse_repo_args(args.repo) if args.repo else None
    overlay_init(root, args.issue, args.branch, repos)
    print(overlay_status(root))
    return 0


def cmd_validate_overlay(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    errors = validate_overlay(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("overlay valid")
    return 0


def cmd_overlay_status(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(overlay_status(root))
    return 0


def cmd_root_export(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    target_branch = args.target_branch
    target_remote = args.target_remote
    target_repo = args.target_repo
    if not target_branch:
        from .io import read_data

        workspace = read_data(root / "workspace.yaml")
        export_meta = workspace["branch"]["root_export"]
        target_branch = export_meta["target_ref"]
        target_remote = target_remote or export_meta.get("target_remote")
        target_repo = target_repo or export_meta.get("target_repo")
    print(json.dumps({
        "export_dir": root_export(root, target_branch, commit=args.commit),
        "target_branch": target_branch,
        "target_remote": target_remote,
        "target_repo": target_repo,
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_overlay_cleanup(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(overlay_cleanup(root))
    return 0


def cmd_overlay_repair(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(overlay_repair(root), indent=2, ensure_ascii=False))
    return 0


def cmd_inspect(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    assert_workspace(root)
    print("workspace valid")
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    errors = validate(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("workspace valid")
    return 0


def cmd_transition(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    target = args.to or args.status
    if not target:
        raise ValueError("transition target is required")
    meta = transition(root, target)
    print(meta["status"])
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(bootstrap(root, args.status), indent=2, ensure_ascii=False))
    return 0


def cmd_work_item_activate(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(work_item_activate(root, args.item_id), indent=2, ensure_ascii=False))
    return 0


def cmd_work_item_block(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(work_item_block(root, args.item_id, args.reason), indent=2, ensure_ascii=False))
    return 0


def cmd_work_item_cancel(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(work_item_cancel(root, args.item_id, args.reason), indent=2, ensure_ascii=False))
    return 0


def cmd_verify_gate(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(verify_gate(root, args.item_id, args.summary), indent=2, ensure_ascii=False))
    return 0


def cmd_invalidate(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    invalidate(root, args.item_id)
    return 0


def cmd_assignment_create(args: argparse.Namespace) -> int:
    root = find_assignment_context_root(Path.cwd())
    payload = assignment_create(root, args.role, args.repo, args.writable, args.work_item)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_assignment_list(_: argparse.Namespace) -> int:
    root = find_assignment_context_root(Path.cwd())
    print(json.dumps(assignment_list(root), indent=2, ensure_ascii=False))
    return 0


def cmd_assignment_status(args: argparse.Namespace) -> int:
    root = find_assignment_context_root(Path.cwd())
    print(json.dumps(assignment_update_status(root, args.assignment, args.status), indent=2, ensure_ascii=False))
    return 0


def cmd_agent_claim(args: argparse.Namespace) -> int:
    root = find_assignment_context_root(Path.cwd())
    print(json.dumps(agent_claim(root, args.assignment, args.session_id), indent=2, ensure_ascii=False))
    return 0


def cmd_agent_report(args: argparse.Namespace) -> int:
    root = find_assignment_context_root(Path.cwd())
    print(json.dumps(agent_report(root, args.assignment, args.status, args.report), indent=2, ensure_ascii=False))
    return 0


def cmd_agent_release(args: argparse.Namespace) -> int:
    root = find_assignment_context_root(Path.cwd())
    agent_release(root, args.assignment, args.session_id)
    return 0


def cmd_evidence_record(args: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(evidence_record(root, args.key, args.status, args.note), indent=2, ensure_ascii=False))
    return 0


def cmd_clean_state_check(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(clean_state_check(root), indent=2, ensure_ascii=False))
    return 0


def cmd_deadlock_check(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(deadlock_check(root), indent=2, ensure_ascii=False))
    return 0


def cmd_lock_list(_: argparse.Namespace) -> int:
    root = find_assignment_context_root(Path.cwd())
    print(json.dumps(lock_list(root), indent=2, ensure_ascii=False))
    return 0


def cmd_lock_release(args: argparse.Namespace) -> int:
    root = find_assignment_context_root(Path.cwd())
    lock_release(root, args.lock_name, args.session_id)
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(workspace_status(root), indent=2, ensure_ascii=False))
    return 0


def cmd_finish(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    print(json.dumps(finish(root), indent=2, ensure_ascii=False))
    return 0


def cmd_install_project_hooks(_: argparse.Namespace) -> int:
    root = find_workspace_root(Path.cwd())
    repos = []
    workspace = json.loads(json.dumps({}))
    workspace = None
    try:
        from .io import read_data

        workspace = read_data(root / "workspace.yaml")
        repos = [root / meta["path"] for name, meta in workspace["repos"].items() if name != "root-system" and (root / meta["path"]).exists()]
    except Exception:
        repos = []
    install_project_hooks(root, repos)
    return 0


def cmd_git_shim_install(args: argparse.Namespace) -> int:
    destination = Path(args.destination).expanduser()
    destination.mkdir(parents=True, exist_ok=True)
    shim = destination / "git"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "cmd=\"$*\"\n"
        "if [[ \"$cmd\" == *\"restore\"* ]] || [[ \"$cmd\" == *\"checkout -- web\"* ]] || [[ \"$cmd\" == *\"checkout -- backend\"* ]] || [[ \"$cmd\" == *\"clean\"* ]]; then\n"
        "  if [[ -f workspace.yaml ]]; then\n"
        "    echo \"AI-DLC: root-system discard/restore is blocked. Use child repo commands instead.\" >&2\n"
        "    exit 1\n"
        "  fi\n"
        "fi\n"
        "exec /usr/bin/git \"$@\"\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    print(str(shim))
    return 0


def cmd_hook_dispatch(_: argparse.Namespace) -> int:
    result = dispatch(Path.cwd())
    print(json.dumps(result, ensure_ascii=False))
    return 0


def cmd_block_diagnose(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else Path.cwd()
    result = diagnose_block(cwd, args.event, args.tool, args.command, args.message)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_block_record(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else Path.cwd()
    root = find_assignment_context_root(cwd)
    diagnosis = diagnose_block(cwd, args.event, args.tool, args.command, args.message)
    result = block_record(
        root,
        cwd=cwd,
        block_type=str(diagnosis.get("block_type") or "unknown"),
        route=str(diagnosis.get("suggested_route") or "inspect_block"),
        tool=args.tool,
        command=args.command,
        message=args.message,
        suggested_agent=str(diagnosis.get("suggested_agent") or ""),
        allowed_next_actions=[str(item) for item in diagnosis.get("allowed_next_actions") or []],
        recoverable=bool(diagnosis.get("recoverable", True)),
        requires_user_approval=bool(diagnosis.get("requires_user_approval", False)),
    )
    if diagnosis.get("suggested_commands"):
        result["suggested_commands"] = [str(item) for item in diagnosis["suggested_commands"]]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else Path.cwd()
    print(json.dumps(ai_dlc_context(cwd), indent=2, ensure_ascii=False))
    return 0


def cmd_ensure_context(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else Path.cwd()
    print(json.dumps(ai_dlc_context(cwd, ensure_user_local=True), indent=2, ensure_ascii=False))
    return 0


def cmd_close_context(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else Path.cwd()
    print(json.dumps(cleanup_user_context(cwd), indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-dlc")
    parser.set_defaults(func=lambda _: parser.print_help() or 0)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers()

    install = sub.add_parser("install")
    install.set_defaults(func=cmd_install)

    doctor = sub.add_parser("doctor")
    doctor.set_defaults(func=cmd_doctor)

    init_project_parser = sub.add_parser("init-project")
    init_project_parser.add_argument("--root-system", default=".")
    init_project_parser.add_argument("--repo", action="append", default=[])
    init_project_parser.add_argument("--repo-url", action="append", default=[])
    init_project_parser.add_argument("--project-kind", choices=["root-system", "controller-only"], default="root-system")
    init_project_parser.set_defaults(func=cmd_init_project)

    init_workspace_parser = sub.add_parser("init-workspace")
    init_workspace_parser.add_argument("--issue", required=True)
    init_workspace_parser.add_argument("--issue-url", required=True)
    init_workspace_parser.add_argument("--issue-title", required=True)
    init_workspace_parser.add_argument("--branch", required=True)
    init_workspace_parser.add_argument("--repo", action="append", default=[])
    init_workspace_parser.add_argument("--repo-url", action="append", default=[])
    init_workspace_parser.add_argument("--repo-base-ref", action="append", default=[])
    init_workspace_parser.add_argument("--base-ref", default="origin/main")
    init_workspace_parser.add_argument("--root-export-target", default="main")
    init_workspace_parser.add_argument("--root-export-remote", default="origin")
    init_workspace_parser.add_argument("--workspace-root", default="")
    init_workspace_parser.add_argument("--root-canonical-path", default="")
    init_workspace_parser.add_argument("--root-canonical-url", default="")
    init_workspace_parser.add_argument("--mode", default="literal_worktree_overlay")
    init_workspace_parser.set_defaults(func=cmd_init_workspace)

    overlay_init_parser = sub.add_parser("overlay-init")
    overlay_init_parser.add_argument("--issue")
    overlay_init_parser.add_argument("--branch")
    overlay_init_parser.add_argument("--repo", action="append", default=[])
    overlay_init_parser.set_defaults(func=cmd_overlay_init)

    validate_overlay_parser = sub.add_parser("validate-overlay")
    validate_overlay_parser.set_defaults(func=cmd_validate_overlay)

    overlay_status_parser = sub.add_parser("overlay-status")
    overlay_status_parser.set_defaults(func=cmd_overlay_status)

    root_export_parser = sub.add_parser("root-export")
    root_export_parser.add_argument("--target-branch")
    root_export_parser.add_argument("--target-remote")
    root_export_parser.add_argument("--target-repo")
    root_export_parser.add_argument("--commit", action="store_true")
    root_export_parser.set_defaults(func=cmd_root_export)

    overlay_cleanup_parser = sub.add_parser("overlay-cleanup")
    overlay_cleanup_parser.set_defaults(func=cmd_overlay_cleanup)

    overlay_repair_parser = sub.add_parser("overlay-repair")
    overlay_repair_parser.set_defaults(func=cmd_overlay_repair)

    inspect_parser = sub.add_parser("inspect")
    inspect_parser.set_defaults(func=cmd_inspect)

    validate_parser = sub.add_parser("validate")
    validate_parser.set_defaults(func=cmd_validate)

    transition_parser = sub.add_parser("transition")
    transition_parser.add_argument("status", nargs="?")
    transition_parser.add_argument("--to")
    transition_parser.set_defaults(func=cmd_transition)

    bootstrap_parser = sub.add_parser("bootstrap")
    bootstrap_parser.add_argument("--status")
    bootstrap_parser.set_defaults(func=cmd_bootstrap)

    work_item_parser = sub.add_parser("work-item")
    work_item_sub = work_item_parser.add_subparsers()
    activate_parser = work_item_sub.add_parser("activate")
    activate_parser.add_argument("item_id")
    activate_parser.set_defaults(func=cmd_work_item_activate)
    block_parser = work_item_sub.add_parser("block")
    block_parser.add_argument("item_id")
    block_parser.add_argument("--reason", required=True)
    block_parser.set_defaults(func=cmd_work_item_block)
    cancel_parser = work_item_sub.add_parser("cancel")
    cancel_parser.add_argument("item_id")
    cancel_parser.add_argument("--reason", required=True)
    cancel_parser.set_defaults(func=cmd_work_item_cancel)

    verify_parser = sub.add_parser("verify-gate")
    verify_parser.add_argument("item_id")
    verify_parser.add_argument("--summary", required=True)
    verify_parser.set_defaults(func=cmd_verify_gate)

    invalidate_parser = sub.add_parser("invalidate")
    invalidate_parser.add_argument("item_id")
    invalidate_parser.set_defaults(func=cmd_invalidate)

    assignment_parser = sub.add_parser("assignment")
    assignment_sub = assignment_parser.add_subparsers()
    assignment_create_parser = assignment_sub.add_parser("create")
    assignment_create_parser.add_argument("--role", required=True)
    assignment_create_parser.add_argument("--repo")
    assignment_create_parser.add_argument("--work-item")
    assignment_create_parser.add_argument("--writable", action="append", default=[])
    assignment_create_parser.set_defaults(func=cmd_assignment_create)
    assignment_list_parser = assignment_sub.add_parser("list")
    assignment_list_parser.set_defaults(func=cmd_assignment_list)
    for status_name in ["accept", "reject"]:
        status_parser = assignment_sub.add_parser(status_name)
        status_parser.add_argument("--assignment", required=True)
        status_parser.set_defaults(func=cmd_assignment_status, status=f"{status_name}ed")

    claim_parser = sub.add_parser("agent-claim")
    claim_parser.add_argument("--assignment", required=True)
    claim_parser.add_argument("--session-id")
    claim_parser.set_defaults(func=cmd_agent_claim)

    report_parser = sub.add_parser("agent-report")
    report_parser.add_argument("--assignment", required=True)
    report_parser.add_argument("--status", required=True)
    report_parser.add_argument("--report")
    report_parser.set_defaults(func=cmd_agent_report)

    release_parser = sub.add_parser("agent-release")
    release_parser.add_argument("--assignment", required=True)
    release_parser.add_argument("--session-id")
    release_parser.set_defaults(func=cmd_agent_release)

    evidence_parser = sub.add_parser("evidence")
    evidence_sub = evidence_parser.add_subparsers()
    evidence_record_parser = evidence_sub.add_parser("record")
    evidence_record_parser.add_argument("--key", required=True)
    evidence_record_parser.add_argument("--status", required=True)
    evidence_record_parser.add_argument("--note", required=True)
    evidence_record_parser.set_defaults(func=cmd_evidence_record)

    clean_parser = sub.add_parser("clean-state-check")
    clean_parser.set_defaults(func=cmd_clean_state_check)

    deadlock_parser = sub.add_parser("deadlock-check")
    deadlock_parser.set_defaults(func=cmd_deadlock_check)

    lock_parser = sub.add_parser("lock")
    lock_sub = lock_parser.add_subparsers()
    lock_list_parser = lock_sub.add_parser("list")
    lock_list_parser.set_defaults(func=cmd_lock_list)
    lock_release_parser = lock_sub.add_parser("release")
    lock_release_parser.add_argument("lock_name")
    lock_release_parser.add_argument("--session-id")
    lock_release_parser.set_defaults(func=cmd_lock_release)

    status_parser = sub.add_parser("status")
    status_parser.set_defaults(func=cmd_status)

    finish_parser = sub.add_parser("finish")
    finish_parser.set_defaults(func=cmd_finish)

    install_hooks_parser = sub.add_parser("install-project-hooks")
    install_hooks_parser.set_defaults(func=cmd_install_project_hooks)

    git_shim = sub.add_parser("git-shim")
    git_shim_sub = git_shim.add_subparsers()
    git_shim_install = git_shim_sub.add_parser("install")
    git_shim_install.add_argument("--destination", default="~/.local/bin/ai-dlc-git-shim")
    git_shim_install.set_defaults(func=cmd_git_shim_install)

    hook_dispatch = sub.add_parser("hook-dispatch")
    hook_dispatch.set_defaults(func=cmd_hook_dispatch)

    block_diagnose = sub.add_parser("block-diagnose")
    block_diagnose.add_argument("--cwd", default="")
    block_diagnose.add_argument("--event", default="")
    block_diagnose.add_argument("--tool", default="")
    block_diagnose.add_argument("--command", default="")
    block_diagnose.add_argument("--message", default="")
    block_diagnose.set_defaults(func=cmd_block_diagnose)

    block_record_parser = sub.add_parser("block-record")
    block_record_parser.add_argument("--cwd", default="")
    block_record_parser.add_argument("--event", default="")
    block_record_parser.add_argument("--tool", default="")
    block_record_parser.add_argument("--command", default="")
    block_record_parser.add_argument("--message", default="")
    block_record_parser.set_defaults(func=cmd_block_record)

    context_parser = sub.add_parser("context")
    context_parser.add_argument("--cwd", default="")
    context_parser.set_defaults(func=cmd_context)

    ensure_context = sub.add_parser("ensure-context")
    ensure_context.add_argument("--cwd", default="")
    ensure_context.set_defaults(func=cmd_ensure_context)

    close_context = sub.add_parser("close-context")
    close_context.add_argument("--cwd", default="")
    close_context.set_defaults(func=cmd_close_context)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return int(args.func(args))
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
