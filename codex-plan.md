# Portable Codex Careflow And Sango Dotfiles Plan

## Goal

Establish dotfiles that can configure Codex Careflow on another machine and bootstrap another repository without committing local paths, user secrets, runtime state, or machine-specific project trust.

## Architecture

- Codex Careflow is the workflow authority: case, plan, assignment, lease, managed worktree, hook policy, verification, and discharge.
- Sango is the operational evidence layer for repositories that define `sango.yaml`: worktree status, service status, logs, doctor, troubleshoot, runbook, and audit inventory.
- dotfiles is the portable distribution layer: templates, safe installer commands, doctor, scanner, and documentation.

## Implementation Scope

- Safe user-level Codex install through `install.sh codex`.
- Project bootstrap through `install.sh codex-project <repo>`.
- Optional Sango bootstrap through `install.sh sango-project <repo>`.
- Portable `AGENTS.md`, hooks, rules, config template, Careflow workspace template, Sango template, doctor, and portability scan.
- CI gate that runs the same portability scan on push and pull request.

## Non-Negotiable Constraints

- Do not track user-specific `packages/codex/.codex/config.toml`.
- Do not track local absolute home paths, project trust paths, auth files, histories, sqlite databases, caches, Careflow state, or Sango runtime outputs.
- Do not write forbidden local identifiers into the repository. They must come from local env or CI secret as `FORBIDDEN_WORDS`.
- Existing user or project files are not overwritten unless they contain a dotfiles managed marker or `--force` is explicitly used for user-level symlinks.
- Existing project files with a dotfiles managed marker are not overwritten when they diverged from the current template unless `--force` is explicitly used.
- The `careflow` CLI is an explicit prerequisite for enabling Codex hooks. The `codex-careflow` dotfiles package distributes local helper files; it does not install the Careflow runtime.

## Workflow Enforcement Target

- User-level and project-level Codex hooks delegate lifecycle events to `careflow codex-hook <event>`.
- Careflow denies unsafe mutation when plan, assignment, active lease, managed worktree, or writable scope evidence is missing.
- Controller work plans, assigns, verifies, and integrates. Worker assignments perform implementation inside explicit scope.
- Sango checks are evidence, not authorization. Careflow remains the authorization gate.

## Verification Gate

Run all applicable checks before commit, push, or PR:

1. `git status --short --branch --untracked-files=all`
2. `FORBIDDEN_WORDS=... scripts/check-portability.sh`
3. `DOTFILES_TARGET_HOME=<fixture-home> ./install.sh -n codex`
4. `./install.sh -n codex-project <fixture-repo>`
5. `./install.sh -n sango-project <fixture-repo>`
6. `python3 packages/codex-careflow/.codex-careflow/bin/doctor.py --repo .`
7. `careflow doctor`
8. Sango checks for repos that provide `sango.yaml`
9. Codex CLI read-only critical review

If any gate fails, is skipped, or cannot run because of environment constraints, PR creation is blocked.
