---
name: codex-planning-delegation
description: Use before non-trivial Codex work when deciding planner quality, Claude-vs-Codex planner fallback, subagent delegation, direct edit thresholds, grill/critique review, goal persistence, or durable workflow knowledge updates.
---

# codex-planning-delegation

Use this before mutating files for non-trivial tasks where planning quality,
role delegation, or completion persistence matters.

## Procedure

1. Read `references/planner-delegation-policy.md`.
2. Classify the request:
   - trivial direct edit
   - bounded implementation
   - research-heavy planning
   - specification-sensitive or high-risk implementation
   - verification/review
   - long-running or quantitative goal
3. For non-trivial implementation, write or update a plan before mutation. Pair
   with `decision-complete-planning` when the work is high-risk,
   specification-sensitive, multi-surface, or regression-prone.
4. Choose the planner path:
   - Prefer a specialized planner role for non-trivial plans.
   - Use Claude Code as planner only when it is installed, allowed by the user or
     workflow, and the handoff/cost/privacy boundary is acceptable.
   - Fall back to the Codex planner workflow when Claude is unavailable or not
     approved.
   - Do not hard-code model slugs without runtime verification.
5. Decide delegation without asking the user when the policy has a clear answer.
   Ask only when the choice changes permissions, cost, privacy, ownership, or
   external-tool boundaries.
6. Run a grill/critique gate before mutation when the plan is ambiguous,
   high-risk, broad, or likely to hide missing tests.
7. For quantitative or long-running tasks, maintain a visible goal ledger with
   requested count, accepted count, rejected count, duplicates, blockers, and
   verification evidence.
8. Put durable behavior in the smallest correct surface:
   - `AGENTS.md` for concise repo conventions.
   - Skills for reusable workflows.
   - Subagent definitions for stable role contracts.
   - Hooks for deterministic enforcement after runtime probing.
   - Rules only for command approval policy.
9. Record the planner path, delegation decision, critique findings, and
   verification evidence in the task result or final report.

## References

- `references/planner-delegation-policy.md`
- `references/research-digest-2026-06.md`
