from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from .block_ledger import open_blocker_errors
from .io import now_iso, read_data, write_data


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, env=env, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def git(cmd: list[str], cwd: Path) -> str:
    return run(["git", *cmd], cwd=cwd)


def detect_default_branch(repo_path: Path) -> str:
    return git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)


def resolve_start_point(controller: Path, default_branch: str, base_ref: str | None = None) -> str:
    candidates = []
    if base_ref:
        if base_ref.startswith("refs/"):
            candidates.append(base_ref)
        else:
            candidates.append(f"refs/remotes/{base_ref}")
            candidates.append(f"refs/heads/{base_ref}")
    candidates.extend([f"refs/remotes/origin/{default_branch}", f"refs/heads/{default_branch}"])
    for candidate in candidates:
        result = subprocess.run(
            ["git", "--git-dir", str(controller), "show-ref", "--verify", candidate],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate.removeprefix("refs/")
    return base_ref or default_branch


def resolve_repo_ref(repo_path: Path, default_branch: str, base_ref: str | None = None) -> str:
    candidates = []
    if base_ref:
        candidates.append(base_ref)
        if base_ref.startswith("origin/"):
            candidates.append(base_ref.split("/", 1)[1])
    candidates.extend([f"origin/{default_branch}", default_branch, "HEAD"])
    for candidate in candidates:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            cwd=repo_path,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate
    return "HEAD"


def _local_root(root: Path, workspace: dict) -> Path:
    return (root / workspace["paths"]["local"]).resolve()


def _stash_root(root: Path, workspace: dict) -> Path:
    stash = _local_root(root, workspace) / "overlay" / "gitfiles"
    stash.mkdir(parents=True, exist_ok=True)
    return stash


def _tracked_manifest(root: Path, repo_name: str, repo_path: Path, overlay_repo: dict) -> list[str]:
    tracked = git(["ls-files"], repo_path).splitlines()
    manifest_path = (_local_root(root, read_data(root / "workspace.yaml")) / "overlay" / f"{repo_name}.tracked.z")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(b"\0".join(path.encode() for path in tracked) + (b"\0" if tracked else b""))
    overlay_repo["tracked_files_ref"] = str(manifest_path.relative_to(_local_root(root, read_data(root / "workspace.yaml"))))
    overlay_repo["baseline_tracked_file_count"] = len(tracked)
    return tracked


def _write_workspace_git_shim(root: Path, workspace: dict) -> Path:
    shim_dir = _local_root(root, workspace) / "bin" / "ai-dlc-git-shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    shim = shim_dir / "git"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "cmd=\"$*\"\n"
        "if [[ -f workspace.yaml ]] && ([[ \"$cmd\" == *\"restore\"* ]] || [[ \"$cmd\" == *\"checkout --\"* ]] || [[ \"$cmd\" == *\"clean\"* ]] || [[ \"$cmd\" == *\"reset --hard\"* ]]); then\n"
        "  echo \"AI-DLC: root-system discard/restore/reset/clean is blocked. Use child repo commands instead.\" >&2\n"
        "  exit 1\n"
        "fi\n"
        "exec /usr/bin/git \"$@\"\n",
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return shim


def _restore_gitfiles(root: Path, overlay: dict, stash_root: Path) -> None:
    for repo in overlay["embedded_repos"]:
        worktree_path = root / repo["path"]
        backup = stash_root / f"{repo['name']}.gitfile"
        if backup.exists():
            backup.rename(worktree_path / ".git")
            repo["gitfile_restored"] = True
            repo["recovery"]["restore_required"] = False


def overlay_init(root: Path, issue: str | None = None, branch: str | None = None, repos: dict[str, str] | None = None) -> dict:
    workspace = read_data(root / "workspace.yaml")
    issue = issue or workspace["id"]
    branch = branch or workspace["branch"]["issue"]
    repos = repos or {
        name: meta["canonical_repo_path"]
        for name, meta in workspace["repos"].items()
        if name != "root-system"
    }
    local_root = _local_root(root, workspace)
    gitdirs = local_root / "gitdirs"
    gitdirs.mkdir(parents=True, exist_ok=True)
    stash_root = _stash_root(root, workspace)
    overlay_path = root / workspace["paths"]["overlay"]
    overlay = read_data(overlay_path)
    moved_gitfiles: list[str] = []

    try:
        for repo in overlay["embedded_repos"]:
            repo_name = repo["name"]
            source = Path(repos[repo_name]).expanduser().resolve()
            controller = gitdirs / f"{repo_name}.git"
            if not controller.exists():
                run(["git", "clone", "--bare", str(source), str(controller)])
            else:
                run(["git", "--git-dir", str(controller), "fetch", "--all", "--prune"])

            repo_meta = workspace["repos"][repo_name]
            worktree_path = root / repo_name
            default_branch = detect_default_branch(source)
            resolved_base_ref = resolve_repo_ref(source, default_branch, repo_meta.get("base_ref"))
            repo["base_sha"] = git(["rev-parse", resolved_base_ref], source)
            repo["head_sha"] = git(["rev-parse", "HEAD"], source)
            start_point = resolve_start_point(controller, default_branch, repo_meta.get("base_ref"))
            if not (worktree_path.exists() and (worktree_path / ".git").exists()):
                if worktree_path.exists():
                    shutil.rmtree(worktree_path)
                run(
                    [
                        "git",
                        "--git-dir",
                        str(controller),
                        "worktree",
                        "add",
                        "-B",
                        branch,
                        str(worktree_path),
                        start_point,
                    ]
                )

            _tracked_manifest(root, repo_name, worktree_path, repo)
            gitfile = worktree_path / ".git"
            backup = stash_root / f"{repo_name}.gitfile"
            if gitfile.exists():
                if backup.exists():
                    backup.unlink()
                gitfile.rename(backup)
                repo["recovery"]["restore_required"] = True
                repo["recovery"]["last_attempt_at"] = now_iso()
                moved_gitfiles.append(repo_name)

        git(["add", "--all", "--", *repos.keys()], root)
        commit_env = os.environ.copy()
        commit_env["AI_DLC_ALLOW_OVERLAY_BASELINE"] = "1"
        try:
            run(["git", "commit", "-m", f"AI-DLC overlay baseline: {issue}"], cwd=root, env=commit_env)
        except subprocess.CalledProcessError as exc:
            if "nothing to commit" not in (exc.stdout + exc.stderr):
                raise
        root_commit = git(["rev-parse", "HEAD"], root)
        overlay["baseline"]["status"] = "created"
        overlay["baseline"]["root_commit"] = root_commit
        overlay["baseline"]["created_at"] = now_iso()
        overlay["baseline"]["hardening"] = {"mode": "git_shim", "path": str(_write_workspace_git_shim(root, workspace))}
        for repo in overlay["embedded_repos"]:
            repo["baseline_tree_recorded_by_root"] = True
        return overlay
    finally:
        _restore_gitfiles(root, overlay, stash_root)
        write_data(overlay_path, overlay)


def overlay_repair(root: Path) -> dict:
    workspace = read_data(root / "workspace.yaml")
    overlay_path = root / workspace["paths"]["overlay"]
    overlay = read_data(overlay_path)
    stash_root = _stash_root(root, workspace)
    restored: list[str] = []
    for repo in overlay["embedded_repos"]:
        worktree_path = root / repo["path"]
        backup = stash_root / f"{repo['name']}.gitfile"
        if not (worktree_path / ".git").exists() and backup.exists():
            backup.rename(worktree_path / ".git")
            repo["gitfile_restored"] = True
            repo["recovery"]["restore_required"] = False
            repo["recovery"]["last_attempt_at"] = now_iso()
            restored.append(repo["name"])
    overlay["baseline"].setdefault("hardening", {"mode": "git_shim", "path": str(_write_workspace_git_shim(root, workspace))})
    write_data(overlay_path, overlay)
    return {"restored": restored, "shim": str(_write_workspace_git_shim(root, workspace))}


def validate_overlay(root: Path) -> list[str]:
    workspace = read_data(root / "workspace.yaml")
    overlay = read_data(root / workspace["paths"]["overlay"])
    errors: list[str] = []
    if workspace["layout"]["mode"] != "literal_worktree_overlay":
        errors.append("workspace layout.mode must be literal_worktree_overlay")
    if not overlay["baseline"].get("root_commit"):
        errors.append("overlay baseline root_commit is missing")
    hardening = workspace.get("hardening", {}).get("destructive_git_guard", {})
    if hardening.get("required"):
        shim_path = (root / hardening.get("path", "")).resolve() if hardening.get("path") else None
        if not shim_path or not shim_path.exists():
            errors.append("destructive-operation hardening is not active")
    for repo in overlay["embedded_repos"]:
        repo_path = root / repo["path"]
        if not repo_path.exists():
            errors.append(f"{repo['name']}: repo path missing")
            continue
        if not (repo_path / ".git").exists():
            errors.append(f"{repo['name']}: .git missing")
            continue
        try:
            value = git(["rev-parse", "--is-inside-work-tree"], repo_path)
            if value != "true":
                errors.append(f"{repo['name']}: git worktree check failed")
        except subprocess.CalledProcessError:
            errors.append(f"{repo['name']}: git rev-parse failed")
        index_rows = git(["ls-files", "-s", "--", repo["path"]], root).splitlines()
        if any(row.startswith("160000 ") and row.rsplit("\t", 1)[-1] == repo["path"] for row in index_rows):
            errors.append(f"{repo['name']}: tracked as gitlink 160000")
        if repo.get("recovery", {}).get("restore_required"):
            errors.append(f"{repo['name']}: recovery requires gitfile restore")
    from .git_hooks import _resolve_git_hooks_dir
    root_hooks = _resolve_git_hooks_dir(root)
    if not (root_hooks / "pre-commit").exists():
        errors.append("root pre-commit hook missing")
    if not (root_hooks / "pre-push").exists():
        errors.append("root pre-push hook missing")
    return errors


def overlay_status(root: Path) -> str:
    workspace = read_data(root / "workspace.yaml")
    overlay = read_data(root / workspace["paths"]["overlay"])
    lines = [
        f"root branch: {git(['rev-parse', '--abbrev-ref', 'HEAD'], root)}",
        f"overlay baseline: {overlay['baseline'].get('root_commit')}",
    ]
    for repo in overlay["embedded_repos"]:
        repo_path = root / repo["path"]
        lines.append(f"{repo['name']} branch: {git(['rev-parse', '--abbrev-ref', 'HEAD'], repo_path)}")
        lines.append(f"{repo['name']} status: {git(['status', '--short'], repo_path) or 'clean'}")
    lines.append(f"root view: {git(['status', '--short'], root) or 'clean'}")
    return "\n".join(lines)


ALLOWED_EXPORT_PREFIXES = [
    "workspace.yaml",
    "ai-dlc/overlay/",
    "ai-dlc/bootstrap/",
    "ai-dlc/plans/",
    "ai-dlc/work-items/",
    "ai-dlc/decisions/",
    "ai-dlc/evidence/",
    "ai-dlc/handoff/",
    "ai-dlc/quality/",
    "docs/",
    ".codex/",
    "AGENTS.md",
]

EXCLUDED_EXPORT_PREFIXES = ["web/", "backend/", "ai-dlc/executions/", "ai-dlc/scratch/", ".env", "logs/", "tmp/"]


def root_export(root: Path, target_branch: str, commit: bool = False) -> str:
    errors = validate_overlay(root)
    errors.extend(open_blocker_errors(root, "root-export"))
    if errors:
        raise ValueError("\n".join(errors))
    temp_parent = (_local_root(root, read_data(root / "workspace.yaml")) / "tmp")
    temp_parent.mkdir(parents=True, exist_ok=True)
    export_dir = Path(tempfile.mkdtemp(prefix="root-export-", dir=temp_parent))
    run(["git", "worktree", "add", str(export_dir), target_branch], cwd=root)
    changed: list[str] = []
    try:
        removed: list[str] = []
        for prefix in EXCLUDED_EXPORT_PREFIXES:
            target = prefix.rstrip("/")
            tracked = run(["git", "ls-files", "--", target], cwd=export_dir)
            if tracked:
                run(["git", "rm", "-r", "--ignore-unmatch", "--cached", "--", target], cwd=export_dir)
                if (export_dir / target).exists():
                    shutil.rmtree(export_dir / target, ignore_errors=True)
                removed.append(target)
        for relative in git(["ls-files"], root).splitlines():
            if any(relative.startswith(prefix) for prefix in EXCLUDED_EXPORT_PREFIXES):
                continue
            if relative not in ALLOWED_EXPORT_PREFIXES and not any(relative.startswith(prefix) for prefix in ALLOWED_EXPORT_PREFIXES):
                continue
            src = root / relative
            dst = export_dir / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_file():
                shutil.copy2(src, dst)
                changed.append(relative)
        if changed:
            run(["git", "add", "--", *changed], cwd=export_dir)
        if removed:
            changed.extend(removed)
        if commit:
            run(["git", "commit", "-m", "AI-DLC root export"], cwd=export_dir)
        return str(export_dir)
    except Exception:
        run(["git", "worktree", "remove", "--force", str(export_dir)], cwd=root)
        raise


def overlay_cleanup(root: Path) -> str:
    blocker_errors = open_blocker_errors(root, "overlay-cleanup")
    if blocker_errors:
        raise ValueError("\n".join(blocker_errors))
    workspace = read_data(root / "workspace.yaml")
    local_root = _local_root(root, workspace)
    lines = [f"root status: {git(['status', '--short'], root) or 'clean'}"]
    for name, repo in workspace["repos"].items():
        if name == "root-system":
            continue
        lines.append(f"{name} status: {git(['status', '--short'], root / repo['path']) or 'clean'}")
    lines.append(f"local gitdirs: {local_root / 'gitdirs'}")
    lines.append("destructive cleanup is not performed automatically")
    return "\n".join(lines)
