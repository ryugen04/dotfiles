from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

from .io import ensure_dir

ROOT_PRE_COMMIT = """#!/usr/bin/env bash
set -euo pipefail

if [ "${AI_DLC_ALLOW_OVERLAY_BASELINE:-}" = "1" ]; then
  exit 0
fi

bad_paths="$(python3 - <<'PY'
from pathlib import Path
import subprocess

try:
    import yaml
except Exception:
    yaml = None

workspace = Path("workspace.yaml")
if not workspace.exists():
    raise SystemExit(0)
text = workspace.read_text(encoding="utf-8")
data = yaml.safe_load(text) if yaml is not None else {}
embedded = [meta.get("path", name) for name, meta in (data.get("repos") or {}).items() if name != "root-system"]
if not embedded:
    raise SystemExit(0)
result = subprocess.run(["git", "diff", "--cached", "--name-only", "--", *embedded], check=False, capture_output=True, text=True)
print(result.stdout.strip())
PY
)"
if [ -n "$bad_paths" ]; then
  echo "AI-DLC: root-system must not commit embedded subrepo paths after overlay baseline."
  echo "$bad_paths"
  exit 1
fi

forbidden="$(git diff --cached --name-only -- ai-dlc/executions ai-dlc/scratch || true)"
if [ -n "$forbidden" ]; then
  echo "AI-DLC: executions/scratch must not be committed."
  echo "$forbidden"
  exit 1
fi

if git diff --cached --name-only | grep -E '(^|/)\\.env(\\.|$)|secret|credential' >/dev/null; then
  echo "AI-DLC: possible secret/env file staged."
  exit 1
fi
"""

ROOT_PRE_PUSH = """#!/usr/bin/env bash
set -euo pipefail

current_branch="$(git rev-parse --abbrev-ref HEAD)"
expected_branch="$(python3 - <<'PY'
from pathlib import Path
try:
    import yaml
except Exception:
    yaml = None

workspace = Path("workspace.yaml")
if not workspace.exists():
    raise SystemExit(0)
text = workspace.read_text(encoding="utf-8")
data = yaml.safe_load(text) if yaml is not None else {}
print(((data.get("branch") or {}).get("root_export") or {}).get("target_ref", ""))
PY
)"

if [ -z "$expected_branch" ] || [ "$current_branch" != "$expected_branch" ]; then
  echo "AI-DLC: root-system overlay branch must not be pushed."
  echo "Use ai-dlc root-export for root-system state, and push only the configured root-export branch."
  exit 1
fi

if python3 - <<'PY'
from pathlib import Path
import subprocess

try:
    import yaml
except Exception:
    yaml = None

workspace = Path("workspace.yaml")
if not workspace.exists():
    raise SystemExit(1)
text = workspace.read_text(encoding="utf-8")
data = yaml.safe_load(text) if yaml is not None else {}
embedded = [meta.get("path", name) for name, meta in (data.get("repos") or {}).items() if name != "root-system"]
if not embedded:
    raise SystemExit(1)
result = subprocess.run(["git", "ls-files", "--", *embedded], check=False, capture_output=True, text=True)
raise SystemExit(0 if result.stdout.strip() else 1)
PY
then
  echo "AI-DLC: root-system tracks embedded repo paths. Push is forbidden."
  exit 1
fi
"""

CHILD_PRE_COMMIT = """#!/usr/bin/env bash
set -euo pipefail

workspace_root="$(pwd)"
while [ "$workspace_root" != "/" ] && [ ! -f "$workspace_root/workspace.yaml" ]; do
  workspace_root="$(dirname "$workspace_root")"
done

if [ -f "$workspace_root/workspace.yaml" ]; then
  expected_branch="$(python3 - <<'PY' "$workspace_root/workspace.yaml" "$(pwd)"
from pathlib import Path
import sys
try:
    import yaml
except Exception:
    yaml = None
path = Path(sys.argv[1])
repo_dir = Path(sys.argv[2]).resolve()
text = path.read_text(encoding="utf-8")
if yaml is not None:
    data = yaml.safe_load(text) or {}
else:
    data = {}
workspace_root = path.parent.resolve()
repo_name = None
for name, meta in (data.get("repos") or {}).items():
    repo_path = (workspace_root / meta.get("path", name)).resolve()
    if repo_path == repo_dir:
        repo_name = name
        break
if repo_name is None:
    print("")
else:
    repo_meta = (data.get("repos") or {}).get(repo_name, {})
    print(repo_meta.get("issue_branch") or (data.get("branch") or {}).get("issue", ""))
PY
)"
  current_branch="$(git rev-parse --abbrev-ref HEAD)"
  if [ -n "$expected_branch" ] && [ "$current_branch" != "$expected_branch" ]; then
    echo "AI-DLC: child repo branch must match workspace branch."
    echo "expected: $expected_branch"
    echo "current:  $current_branch"
    exit 1
  fi
fi

if git diff --cached --name-only | grep -E '(^|/)\\.env(\\.|$)|secret|credential' >/dev/null; then
  echo "AI-DLC: possible secret/env file staged."
  exit 1
fi
"""

CHILD_PRE_PUSH = """#!/usr/bin/env bash
set -euo pipefail

workspace_root="$(pwd)"
while [ "$workspace_root" != "/" ] && [ ! -f "$workspace_root/workspace.yaml" ]; do
  workspace_root="$(dirname "$workspace_root")"
done

[ -f "$workspace_root/workspace.yaml" ] || exit 0

python3 - <<'PY' "$workspace_root" "$(pwd)"
from pathlib import Path
import subprocess
import sys

try:
    import yaml
except Exception:
    yaml = None

workspace_root = Path(sys.argv[1]).resolve()
repo_dir = Path(sys.argv[2]).resolve()
text = (workspace_root / "workspace.yaml").read_text(encoding="utf-8")
data = yaml.safe_load(text) if yaml is not None else {}
repo_name = None
for name, meta in (data.get("repos") or {}).items():
    repo_path = (workspace_root / meta.get("path", name)).resolve()
    if repo_path == repo_dir:
        repo_name = name
        break
if repo_name is None:
    raise SystemExit(0)
evidence_path = workspace_root / (data.get("paths") or {}).get("evidence", "")
if not evidence_path.exists():
    raise SystemExit("AI-DLC: evidence file is missing.")
evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8")) if yaml is not None else {}
items = evidence.get("items") or {}
matching = []
for item in items.values():
    if (
        item.get("repo") == repo_name
        and item.get("status") == "passing"
        and item.get("recorded_by") == "dlc_verifier"
        and item.get("workspace_id") == data.get("id")
        and item.get("issue_branch") == (data.get("branch") or {}).get("issue")
    ):
        matching.append(item)
if not matching:
    raise SystemExit(f"AI-DLC: no passing verifier evidence recorded for repo {repo_name}.")
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, check=True, capture_output=True, text=True).stdout.strip()
if not any(item.get("head_sha") == head and item.get("tree_clean") is True for item in matching):
    raise SystemExit(f"AI-DLC: HEAD {head} for repo {repo_name} is not covered by passing verifier evidence.")
PY
"""


def write_executable(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _resolve_git_hooks_dir(repo: Path) -> Path:
    git_path = repo / ".git"
    if git_path.is_file():
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--git-dir"],
            check=True,
            capture_output=True,
            text=True,
        )
        resolved = result.stdout.strip()
        if os.path.isabs(resolved):
            return Path(resolved) / "hooks"
        return (repo / resolved).resolve() / "hooks"
    return git_path / "hooks"


def install_project_hooks(root: Path, child_repos: list[Path] | None = None) -> None:
    hooks_dir = ensure_dir(_resolve_git_hooks_dir(root))
    write_executable(hooks_dir / "pre-commit", ROOT_PRE_COMMIT)
    write_executable(hooks_dir / "pre-push", ROOT_PRE_PUSH)
    for repo in child_repos or []:
        git_dir = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--git-dir"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        child_hooks = ensure_dir((repo / git_dir).resolve() / "hooks" if not os.path.isabs(git_dir) else Path(git_dir) / "hooks")
        write_executable(child_hooks / "pre-commit", CHILD_PRE_COMMIT)
        write_executable(child_hooks / "pre-push", CHILD_PRE_PUSH)
