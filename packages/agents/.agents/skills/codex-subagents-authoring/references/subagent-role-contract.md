# Subagent Role Contract

References:

- https://developers.openai.com/codex/subagents
- Local role examples: `packages/codex/.codex/agents/dlc-*.toml`

## Required Role Fields

- purpose
- write scope
- allowed commands
- forbidden actions
- required input context
- report fields
- phase ownership, when used by a workflow

## AI-DLC Phase Ownership

Controller remains orchestrator-only. Phase work belongs to subagents:

- planning -> `dlc_plan_writer`
- scoping -> `dlc_scope_manager`
- implementation -> `dlc_repo_worker`
- verification -> `dlc_verifier`
- evaluation -> `dlc_evaluator`
- handoff -> `dlc_handoff_writer`
- finish -> `dlc_git_operator`

