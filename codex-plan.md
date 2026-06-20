# Portable Codex Careflow And Sango Dotfiles Plan

## Goal

Establish dotfiles that can configure Codex Careflow on another machine and bootstrap another repository without committing local paths, user secrets, runtime state, or machine-specific project trust.

## Architecture

- Codex Careflow is the workflow authority: case, plan, assignment, lease, managed worktree, hook policy, verification, and discharge.
- Sango is the operational evidence layer for repositories that define `sango.yaml`: worktree status, service status, logs, doctor, troubleshoot, runbook, and audit inventory.
- dotfiles is the portable distribution layer: templates, safe installer commands, doctor, scanner, and documentation.
- Careflow case data is a workspace-shared store. Do not copy `.careflow/cases` into every worktree. Repo and worktree roots should point `.careflow` at the shared workspace store.
- Careflow active state is scoped. `active_case`, `active_order`, lease, and current phase must be resolved by worktree/session context instead of one global `.careflow/state.json` pointer.

Recommended runtime layout:

```text
<workspace-root>/.careflow/
  workspace.yaml
  cases/<case_id>/
  active/worktrees/<worktree_id>.json
  active/sessions/<session_id>.json
  leases/<lease_id>.yaml
  repos/<repo_id>.yaml

<repo-or-worktree-root>/.careflow -> <workspace-root>/.careflow
```

## Implementation Scope

- Safe user-level Codex install through `install.sh codex`.
- Project bootstrap through `install.sh codex-project <repo>`.
- Existing workspace bootstrap through `install.sh workspace-careflow <repo>`.
- Claude project bootstrap through `install.sh claude-project <repo>`.
- Optional Sango bootstrap through `install.sh sango-project <repo>`.
- Portable `AGENTS.md`, hooks, rules, config template, Careflow workspace template, Sango template, doctor, and portability scan.
- CI gate that runs the same portability scan on push and pull request.
- Workspace bootstrap may target either a git repo root or a polyrepo workspace root. Existing polyrepo roots should use `workspace-careflow`, which preserves existing workspace files, adds a managed Careflow block, installs project-local Claude Careflow rules, and links `.worktrees` roots to the shared store.
- Shell integration wraps successful `sango worktree create` calls and re-runs `workspace-careflow` so newly created roots get `.careflow` links and local Git excludes.

## Non-Negotiable Constraints

- Do not track user-specific `packages/codex/.codex/config.toml`.
- Do not track local absolute home paths, project trust paths, auth files, histories, sqlite databases, caches, Careflow state, or Sango runtime outputs.
- Do not write forbidden local identifiers into the repository. They must come from local env or CI secret as `FORBIDDEN_WORDS`.
- Do not track runtime `.careflow`, `.worktrees`, `.sango`, or scoped active state files.
- Do not copy `.careflow` case stores into worktrees; use a symlink to the workspace store.
- Existing user or project files are not overwritten unless they contain a dotfiles managed marker or `--force` is explicitly used for user-level symlinks.
- Existing project files with a dotfiles managed marker are not overwritten when they diverged from the current template unless `--force` is explicitly used.
- The `agent-careflow` CLI is an explicit prerequisite for enabling Codex hooks. The `codex-careflow` dotfiles package distributes local helper files; it does not install the Careflow runtime.

## Workflow Enforcement Target

- User-level and project-level Codex hooks delegate lifecycle events to `agent-careflow hook codex <event>`.
- Careflow denies unsafe mutation when plan, assignment, active lease, managed worktree, or writable scope evidence is missing.
- `agent-careflow` should resolve the workspace store from cwd by following `.careflow` symlinks or workspace templates, then resolve active state by worktree/session scope.
- `sango worktree create` should create or verify `.careflow -> <workspace-root>/.careflow` for each repo worktree it creates.
- Until Sango exposes a native post-create hook, the shell wrapper performs this verification by re-running `install.sh workspace-careflow "$(sango root)"`.
- Controller work plans, assigns, verifies, and integrates. Worker assignments perform implementation inside explicit scope.
- Sango checks are evidence, not authorization. Careflow remains the authorization gate.

## Verification Gate

Run all applicable checks before commit, push, or PR:

1. `git status --short --branch --untracked-files=all`
2. `FORBIDDEN_WORDS=... scripts/check-portability.sh`
3. `DOTFILES_TARGET_HOME=<fixture-home> ./install.sh -n codex`
4. `./install.sh -n codex-project <fixture-repo>`
5. `./install.sh -n workspace-careflow <fixture-workspace>`
6. `./install.sh -n claude-project <fixture-repo>`
7. `./install.sh -n sango-project <fixture-repo>`
8. `python3 packages/codex-careflow/.codex-careflow/bin/doctor.py --repo .`
9. `python3 packages/codex-careflow/.codex-careflow/bin/doctor.py --repo . --project-repo <fixture-repo>`
10. `agent-careflow doctor`
11. Sango checks for repos that provide `sango.yaml`
12. Codex CLI read-only critical review

If any gate fails, is skipped, or cannot run because of environment constraints, PR creation is blocked.
