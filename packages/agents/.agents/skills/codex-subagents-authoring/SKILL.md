---
name: codex-subagents-authoring
description: Author or audit Codex subagent TOML definitions, including role scope, phase ownership, write boundaries, forbidden actions, assignment/report contracts, and controller-to-subagent orchestration rules.
---

# codex-subagents-authoring

Use before editing `packages/codex/.codex/agents/*.toml` or changing phase ownership.

## Procedure

1. Read `references/subagent-role-contract.md`.
2. Give each subagent one clear role and write scope.
3. State what the subagent may read, write, run, and must not do.
4. Include required report fields.
5. Keep controller responsibilities separate from worker responsibilities.
6. For AI-DLC, connect every phase owner to an assignment, report, and transition unblock condition.

