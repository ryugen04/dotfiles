# Codex Careflow Package

This package installs portable Careflow support files under `~/.codex-careflow`.

## Contents

- `bin/doctor.py`: read-only checks for the dotfiles Codex and Careflow packages.

## Doctor

Run from the dotfiles repository root:

```bash
python3 packages/codex-careflow/.codex-careflow/bin/doctor.py --repo .
```

The doctor checks that:

- the portable Codex config exists,
- user-specific project trust paths are not tracked,
- Careflow and Sango templates are present,
- tracked owned files do not contain common home-directory or machine-specific path markers.
- optional project/worktree roots have a `.careflow` store or symlink,
- worktree-local `.careflow` directories are reported instead of silently
  accepted, because worktrees should point at the shared workspace store.

For existing polyrepo workspaces, use:

```bash
./install.sh workspace-careflow /path/to/workspace
```

Use `--force` only when you intentionally want isolated `.worktrees/**/.careflow`
directories archived under the shared store's `migrated/` directory and replaced
with symlinks.

The script does not modify files.

## Fast-Lane Execution Rule

Fast careflow execution should reduce repeated ceremony, not remove durable records.

Minimum durable chain:

- Case
- Plan
- Order
- Result
- Evidence
- Incident or Review when escalation is needed
- Close validation

When the normal edit path is unavailable, do not require host-level namespace or sandbox repair for ordinary work. Use a patch-gated path instead: Codex proposes a unified diff, the controller verifies it with `git apply --check`, then applies it with `git apply` and records Evidence.
