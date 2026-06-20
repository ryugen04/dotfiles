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
