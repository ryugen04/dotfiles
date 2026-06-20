#!/usr/bin/env python3
"""Read-only doctor for portable Codex and Careflow dotfiles."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


REQUIRED_FILES = (
    "packages/codex/.codex/config.toml.template",
    "packages/codex/.codex/AGENTS.md",
    "packages/codex/.codex/templates/project-AGENTS.md",
    "packages/codex/.codex/templates/careflow/workspace.yaml",
    "packages/codex/.codex/templates/careflow/case.md",
    "packages/codex/.codex/templates/careflow/assignment.md",
    "packages/codex/.codex/templates/sango/sango.yaml",
    "packages/codex/.codex/templates/sango/AGENTS.md",
    "packages/codex-careflow/.codex-careflow/README.md",
    "packages/codex-careflow/.codex-careflow/bin/doctor.py",
)

PATH_MARKERS = tuple(
    "".join(parts)
    for parts in (
        ("/", "home", "/"),
        ("/", "Users", "/"),
        ("dev", "/", "projects", "/"),
    )
)
LEGACY_HOOK_COMMAND = "careflow " + "codex-hook"


def repository_files(repo: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--cached", "--others", "--exclude-standard"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return [child for child in repo.rglob("*") if child.is_file() and ".git" not in child.parts]
    return [repo / relative for relative in result.stdout.splitlines()]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_files(repo: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (repo / relative).is_file():
            errors.append(f"missing required file: {relative}")
    return errors


def check_config(repo: Path) -> list[str]:
    errors: list[str] = []
    tracked_config = repo / "packages/codex/.codex/config.toml"
    if tracked_config.exists():
        errors.append("portable dotfiles must not track packages/codex/.codex/config.toml")

    config = repo / "packages/codex/.codex/config.toml.template"
    if not config.is_file():
        return errors + ["missing Codex config template"]

    text = read_text(config)
    if "[projects." in text:
        errors.append("portable config template must not track project trust paths")
    if "on-failure" in text:
        errors.append("deprecated approval policy found: on-failure")
    return errors


def check_cli() -> list[str]:
    errors: list[str] = []
    found = shutil.which("agent-careflow")
    if found is None:
        errors.append("agent-careflow is not on PATH")
    else:
        checks = (
            [found, "--help"],
            [found, "hook", "codex", "session-start", "--help"],
            [found, "hook", "codex", "pre-tool-use", "--help"],
        )
        for command in checks:
            result = subprocess.run(
                command,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode != 0:
                errors.append(f"{' '.join(command)} failed: {result.stderr.strip()}")

    for command in ("careflow", "aidlc", "ai-dlc"):
        legacy = shutil.which(command)
        if legacy is not None:
            errors.append(f"legacy Careflow CLI remains on PATH: {command} -> {legacy}")
    return errors


def check_legacy_hooks(repo: Path) -> list[str]:
    errors: list[str] = []
    for relative in (
        "packages/codex/.codex/hooks.json",
        "packages/codex/.codex/templates/project-AGENTS.md",
        "packages/codex/.codex/rules/careflow.rules",
    ):
        path = repo / relative
        if not path.is_file():
            continue
        if LEGACY_HOOK_COMMAND in read_text(path):
            errors.append(f"legacy hook command found in {relative}")
    return errors


def check_path_markers(repo: Path) -> list[str]:
    errors: list[str] = []
    for path in repository_files(repo):
        if not path.is_file():
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(repo)
        for marker in PATH_MARKERS:
            if marker in text:
                errors.append(f"path marker {marker!r} found in {relative}")
    return errors


def has_marker(path: Path, marker: str) -> bool:
    try:
        return marker in read_text(path)
    except (FileNotFoundError, UnicodeDecodeError):
        return False


def has_any_marker(path: Path, markers: tuple[str, ...]) -> bool:
    try:
        text = read_text(path)
    except (FileNotFoundError, UnicodeDecodeError):
        return False
    return any(marker in text for marker in markers)


def has_path_segment(path: Path, segment: str) -> bool:
    return segment in path.parts


def resolve_symlink(path: Path) -> Path:
    target = path.readlink()
    if target.is_absolute():
        return target
    return (path.parent / target).resolve(strict=False)


def check_careflow_topology(project: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    careflow = project / ".careflow"
    store: Path | None = None

    if careflow.is_symlink():
        store = resolve_symlink(careflow)
        if not store.exists():
            errors.append(f".careflow symlink target is missing: {careflow} -> {store}")
            return errors, warnings
        if not store.is_dir():
            errors.append(f".careflow symlink target is not a directory: {careflow} -> {store}")
            return errors, warnings
    elif careflow.exists():
        if not careflow.is_dir():
            errors.append(f".careflow is not a directory or symlink: {careflow}")
            return errors, warnings
        store = careflow
        if has_path_segment(project, ".worktrees"):
            errors.append(
                "worktree-local .careflow directory found; worktree roots should symlink to the shared workspace store"
            )
    else:
        errors.append("missing project .careflow store or symlink")
        return errors, warnings

    required_dirs = (
        "cases",
        "active/worktrees",
        "active/sessions",
        "leases",
        "repos",
    )
    for relative in required_dirs:
        path = store / relative
        if not path.is_dir():
            errors.append(f"missing Careflow store directory: {path}")

    workspace_metadata = store / "workspace.yaml"
    if not workspace_metadata.is_file():
        warnings.append("Careflow store metadata is missing: .careflow/workspace.yaml")
    elif not has_marker(workspace_metadata, "dotfiles-managed: codex-careflow-runtime-workspace-v1"):
        warnings.append("Careflow workspace metadata exists but is not dotfiles-managed")

    legacy_state = store / "state.json"
    if legacy_state.exists():
        warnings.append(
            "legacy global .careflow/state.json exists; scoped active state under active/worktrees should be preferred"
        )

    return errors, warnings


def check_project_repo(project: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not project.exists():
        return [f"project repo does not exist: {project}"], warnings

    git_result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if git_result.returncode != 0:
        warnings.append(f"project path is not a git repository; treating as workspace root: {project}")

    codex_files = (
        (".codex/AGENTS.md", ("dotfiles-managed: codex-careflow-project-v1",)),
        (".codex/hooks.json", ("agent-careflow hook codex",)),
        (".codex/rules/careflow.rules", ("Codex Careflow",)),
    )
    for relative, markers in codex_files:
        path = project / relative
        if not path.exists():
            warnings.append(f"missing optional Codex project file: {relative}")
        elif not path.is_file():
            errors.append(f"project path is not a file: {relative}")
        elif not has_any_marker(path, markers):
            errors.append(f"project file is not dotfiles-managed: {relative}")

    workspace_file = project / ".aidlc/workspace.yaml"
    workspace_markers = (
        "dotfiles-managed: codex-careflow-workspace-v1",
        "dotfiles careflow workspace managed",
    )
    if not workspace_file.is_file():
        warnings.append("missing optional Careflow workspace file: .aidlc/workspace.yaml")
    elif not has_any_marker(workspace_file, workspace_markers):
        warnings.append("Careflow workspace file exists but has no dotfiles-managed Careflow block")

    claude_files = (
        (".claude/CLAUDE.md", ("dotfiles-managed: claude-careflow-project-v1",)),
        (".claude/rules/careflow-workspace.md", ("Careflow Workspace Rule",)),
    )
    for relative, markers in claude_files:
        path = project / relative
        if not path.exists():
            warnings.append(f"missing optional Claude Careflow file: {relative}")
        elif not path.is_file():
            errors.append(f"Claude project path is not a file: {relative}")
        elif not has_any_marker(path, markers):
            warnings.append(f"Claude Careflow file is not dotfiles-managed: {relative}")

    sango_config = project / "sango.yaml"
    if sango_config.exists() and not has_marker(sango_config, "dotfiles-managed: sango-project-v1"):
        warnings.append("sango.yaml exists but is not dotfiles-managed")
    if sango_config.exists() and shutil.which("sango") is None:
        warnings.append("sango.yaml exists but sango is not on PATH")

    careflow_errors, careflow_warnings = check_careflow_topology(project)
    errors.extend(careflow_errors)
    warnings.extend(careflow_warnings)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="dotfiles repository root")
    parser.add_argument("--project-repo", default=None, help="optional bootstrapped project repo")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    errors.extend(check_required_files(repo))
    errors.extend(check_config(repo))
    errors.extend(check_cli())
    errors.extend(check_legacy_hooks(repo))
    errors.extend(check_path_markers(repo))

    if args.project_repo:
        project_errors, project_warnings = check_project_repo(Path(args.project_repo).resolve())
        errors.extend(project_errors)
        warnings.extend(project_warnings)

    failed = bool(errors or (args.strict and warnings))
    payload = {
        "status": "FAIL" if failed else "OK",
        "repo": str(repo),
        "checked_files": len(repository_files(repo)),
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if failed else 0

    if failed:
        print("codex-careflow doctor: FAIL")
        for error in errors:
            print(f"- {error}")
        for warning in warnings:
            print(f"- warning: {warning}")
        return 1

    print("codex-careflow doctor: OK")
    print(f"- repo: {repo}")
    print(f"- checked files: {len(repository_files(repo))}")
    for warning in warnings:
        print(f"- warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
