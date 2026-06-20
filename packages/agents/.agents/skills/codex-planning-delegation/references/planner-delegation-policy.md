# Planner Delegation Policy

This policy keeps Codex from wasting user time with repeated "subagent or
direct edit?" prompts. The controller makes the routing decision when the task
classification is clear.

## Direct Edit Threshold

Use direct edit only when all are true:

- The change is small and local after read-only inspection.
- The affected surface is single-module or single-document.
- The expected behavior is clear.
- No external research is needed.
- Failure impact is low and rollback is obvious.
- The narrow verification command is known.

If any condition fails, create or update a plan and consider delegation.

## Planner Path

| Situation | Planner path | Notes |
|---|---|---|
| Trivial local edit | Main Codex thread | Still inspect before edit. |
| Non-trivial but low-risk | Codex planner workflow | Use this skill plus plan artifact. |
| Specification-sensitive, multi-surface, migration, or regression-prone | `decision-complete-planning` plus planner role | Define expected and forbidden outputs before implementation. |
| Research-heavy plan and Claude Code is available/allowed | Claude planner/subagent handoff may draft the plan | Preserve careflow handoff headers when applicable. |
| Claude unavailable, unapproved, or unsuitable | Codex planner fallback | Do not block progress merely because Claude is absent. |

Do not hard-code a model name such as `claude-4.6-opus` or any local alias until
runtime support is verified. Treat model selection as an environment capability,
not a portable repo rule.

## Delegation Defaults

| Task signal | Default route | Do not ask the user unless |
|---|---|---|
| Broad codebase discovery, many files, unknown architecture | Researcher/explorer subagent | Extra permissions or network are required. |
| Plan drafting for non-trivial work | Planner role | Cross-tool invocation changes cost/privacy. |
| Security, data migration, auth, permissions, filesystem deletion, CI/CD | Reviewer/verifier role after planning | Ownership or approval boundaries are unclear. |
| Many independent review dimensions | Parallel reviewers | Token/cost budget is material. |
| Quantitative collection target | Goal ledger plus verifier | External paid tools are needed. |
| Small clear local patch | Direct edit | Any risk signal appears during inspection. |

When using Codex subagents, current public docs say Codex spawns subagents only
when explicitly asked. Therefore the main controller should explicitly request
the needed subagent work instead of asking the user to choose the mechanism.

## Grill/Critique Gate

Run this gate before implementation when the task is ambiguous, high-risk,
multi-surface, or has unclear acceptance criteria.

Ask the critique role to identify:

- Missing acceptance criteria.
- Hidden coupling or ownership boundaries.
- Wrong or weak expected values.
- Tests that would freeze the wrong premise.
- Broad edits that could be split.
- Rollback gaps.
- Unsupported config, hook, rule, or model assumptions.
- Completion claims that cannot be verified.

Implementation starts only after the plan answers the critique or records an
explicit accepted risk.

## Goal Ledger

For long-running or quantitative tasks, maintain a ledger:

| Field | Meaning |
|---|---|
| requested | Target count or completion condition. |
| accepted | Items that meet the condition. |
| rejected | Items inspected but not accepted. |
| duplicates | Items already counted elsewhere. |
| blockers | Conditions that prevent completion. |
| evidence | Commands, URLs, logs, or review notes proving progress. |

Do not claim completion from memory. Count the ledger and record the check.

## Durable Surface Rules

- Use a skill when the workflow is reusable and decision-like.
- Use a skill reference for tables, source inventories, and long examples.
- Use a subagent definition only for a stable role with read/write/command/report
  boundaries.
- Use hooks only for deterministic lifecycle enforcement after payload/runtime
  probing.
- Use `.codex/rules` only for sandbox escalation command policy.
- Keep `AGENTS.md` short; it should point to durable workflow surfaces rather
  than duplicating them.

## Minimum Plan Shape

A non-trivial plan should record:

- Objective and fixed input.
- Allowed and forbidden paths.
- Expected output by surface.
- Forbidden outputs/regression guards.
- Planner path and delegation decision.
- Critique/grill findings or reason skipped.
- Implementation phases.
- Verification commands.
- Rollback path.
- Evidence requirements.
