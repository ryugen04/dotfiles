# Sango Project Instructions

Use this template as a project-level `AGENTS.md` for Sango repositories.

## Careflow

- Use Codex Careflow for non-trivial work.
- Plan before mutation.
- Do not mutate repository content without an approved assignment and active lease.
- Use AI-DLC-managed worktrees for implementation.
- Controller work should inspect, plan, assign, verify, and integrate rather than directly implement.
- Record blockers, near misses, and incidents.
- Prefer system-level corrective action over blaming individual agents.

## Worker Rules

- Work only in the assigned managed worktree.
- Keep strictly to assigned ownership paths.
- Do not edit forbidden paths unless the controller issues a new assignment.
- Do not revert edits made by other workers.
- Use `apply_patch` for manual file edits.
- Run relevant read-only checks before final handoff.

## Handoff

Final responses should include changed paths, verification results, skipped checks, and blockers.
