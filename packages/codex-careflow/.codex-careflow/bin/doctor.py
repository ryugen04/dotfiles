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
    "packages/codex/.codex/templates/careflow/case.md",
    "packages/codex/.codex/templates/careflow/assignment.md",
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
        errors.append(f"project repo is not a git repository: {project}")

    required = (
        (".codex/AGENTS.md", "dotfiles-managed: codex-careflow-project-v1"),
        (".codex/hooks.json", "agent-careflow hook codex"),
        (".codex/rules/careflow.rules", "Codex Careflow"),
        (".aidlc/workspace.yaml", "dotfiles-managed: codex-careflow-workspace-v1"),
    )
    for relative, marker in required:
        path = project / relative
        if not path.is_file():
            errors.append(f"missing project file: {relative}")
        elif not has_marker(path, marker):
            errors.append(f"project file is not dotfiles-managed: {relative}")

    sango_config = project / "sango.yaml"
    if sango_config.exists() and not has_marker(sango_config, "dotfiles-managed: sango-project-v1"):
        warnings.append("sango.yaml exists but is not dotfiles-managed")
    if sango_config.exists() and shutil.which("sango") is None:
        warnings.append("sango.yaml exists but sango is not on PATH")

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
