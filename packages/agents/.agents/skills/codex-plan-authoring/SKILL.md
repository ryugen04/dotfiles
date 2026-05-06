---
name: codex-plan-authoring
description: Author or audit Codex plan files, including timestamped .codex/plans naming, parent/child split plans, phase dashboards, workflow axes, acceptance criteria, approval boundaries, rollback, and local-vs-durable plan state.
---

# codex-plan-authoring

Use before creating or revising `.codex/plans/*.md` or project plan templates.

## Procedure

1. Read `references/plan-file-contract.md`.
2. Use `.codex/plans/YYYYMMDDHH-{planname}.md`.
3. Keep `.codex/plans/**` as local working state unless the project explicitly tracks it.
4. Split large plans into a parent plan and child plans.
5. Record workflow axes, target root, allowed/forbidden paths, phases, outputs, tests, approval gates, and rollback.
6. For Codex config/hooks/skills/subagents work, include hook matrix, validation plan, and rollback plan.

