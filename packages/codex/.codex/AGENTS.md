# Codex User Guidance

This is the portable user-level Codex baseline installed by the dotfiles `codex` package.

- Keep repository-specific build, test, and safety rules in that repository's `AGENTS.md`.
- Keep temporary plans, case status, and assignment notes out of this file.
- Use project-local `.codex/` configuration only for settings that are safe to carry with that repository.
- Do not commit machine-specific trust paths, home directories, local worktree paths, API keys, tokens, or host names.
- For non-trivial implementation work, write or update a plan before mutating files.
- For high-risk or specification-sensitive implementation work, use the `decision-complete-planning` skill before mutating files.
- When multiple agents are active, keep edits inside the assigned ownership boundary and do not revert changes made by others.
- Prefer read-only inspection before mutation, then run the narrowest relevant verification after changes.
- For dual-agent careflow work in kitty, use the `careflow-fast-lane` skill and the kitty-only lane: the current pane is controller/planner, and the right pane becomes worker/executor after explicit go.
- Bind the current controller pane with `careflow-kitty-start --case <case_id> --order <order_id> --worker <codex|claude>`; do not open a replacement controller tab.
- After PLAN/ORDER approval and an explicit go, send work with `careflow-kitty-go --case <case_id> --order <order_id>` rather than pasting ad hoc instructions.
- `careflow-kitty-go` is responsible for resolving the right worker pane: reuse a marked worker, start the agent in an idle right shell, or open a right split when missing.
- Workers must escalate blockers with `careflow-escalate-left --case <case_id> --order <order_id> --blocker "..." --decision-needed "..."` so the message is recorded under `.careflow/cases/<case_id>/messages/`.
- Do not use cmux for careflow agent handoff; cmux integrations are separate UI helpers only.
