---
name: codex-agents-md-authoring
description: Author or audit Codex AGENTS.md files, including user-level and project-level instruction scope, plan persistence, large-plan splitting, hierarchy, context budget, and what belongs in skills, rules, hooks, or subagents instead.
---

# codex-agents-md-authoring

Use before editing `AGENTS.md` files or rules that change how Codex reads standing instructions.

## Procedure

1. Read `references/agents-md-scope.md` before changing instruction scope.
2. Read `references/plan-splitting.md` when a task has multiple workflow types, subsystems, or phase contracts.
3. Keep `AGENTS.md` short, stable, and cross-project safe.
4. Move repeatable procedures to skills, command policy to `.codex/rules`, and hard enforcement to hooks.
5. Do not store volatile task state in `AGENTS.md`; put it in timestamped plans or workspace artifacts.
6. For large plans, require a parent plan that lists child plan paths.

