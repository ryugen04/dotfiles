# Codex Careflow Project Instructions

<!-- dotfiles-managed: codex-careflow-project-v1 -->

## Workflow

- Use Codex Careflow for non-trivial work.
- Inspect context, plan, create assignment, activate lease, implement, verify, evaluate, and discharge.
- Do not mutate repository content without an approved plan, an assignment, an active lease, and a Careflow-managed worktree.
- Controllers inspect, plan, assign, verify, and integrate. Workers implement only inside their writable scope.
- Subagents must receive an explicit role, assignment id, writable scope, forbidden scope, expected report, and verification criteria.
- Do not revert unrelated user or agent edits.
- Record blockers, near misses, and incidents as Careflow artifacts.
- For dual-agent work in kitty, run `careflow-kitty-start` from the existing controller pane to bind the case/order. It must not create a replacement controller tab.
- Use `careflow-kitty-go` only after PLAN/ORDER approval and explicit go. It resolves the right worker pane, starts the worker in an idle right shell or new right split when needed, and refuses unsafe existing panes.
- Workers must send blockers with `careflow-escalate-left`; this records an agmsg under `.careflow/cases/<case_id>/messages/` and notifies the controller pane when available.
- Keep the ORDER as the worker subplan. Do not replace the fixed handoff with an informal chat summary.
- Do not use cmux for Careflow agent handoff; this repository expects the kitty/agmsg lane.

## Sango Evidence

- When `sango.yaml` exists, use Sango for repository, worktree, service, log, doctor, troubleshoot, and runbook evidence.
- Prefer `sango doctor --json`, `sango status --json`, `sango worktree status --json`, and `sango worktree verify` during verification.
- Sango proves operational health; Careflow decides whether work is authorized.

## Verification

- Report changed paths, commands run, skipped checks, blockers, and residual risks.
- Commit, push, and PR creation require discharge-ready Careflow state and a git-operator responsibility.
