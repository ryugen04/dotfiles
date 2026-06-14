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
