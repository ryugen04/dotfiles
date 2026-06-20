# Fast Lane Protocol

## Invariants

- Plan, Order, Result, Evidence, Incident, Review, and Close remain careflow artifacts.
- Handoffs use paths and ids, not pasted plan bodies.
- The worker does not redefine scope after dispatch.
- The controller does not close from memory.
- A skeleton result is not completion evidence.

## Naming And Traceability

Use one canonical slug across the case, branch, and PR, then derive each surface from it.

```text
slug: <short-kebab-case-objective>
CASE_ID: ACF-<slug>
branch: codex/<slug>
PR title: [codex] <human-readable title>
```

Rules:

- Keep the slug short enough to scan in paths, branch lists, and PR heads.
- Prefer the work objective over process words: use `local-careflow-fast-lane`, not `configure-local-codex-environment-and-pr`.
- Keep `ACF-` on `CASE_ID` for careflow artifact namespacing and current CLI compatibility.
- Do not put `ACF-` in git branch names or PR titles; those surfaces already have their own namespace.
- Record `slug`, `branch`, and `pr` in `CASE.yaml` or `PLAN.md` once they exist.
- If one case needs multiple PRs, keep the case slug stable and suffix the branch slug with the delivery slice, such as `codex/<slug>-docs`.

## Lane A: Claude Available

Use this when Claude can act as external planner or replanner.

1. Controller creates or selects a case.
2. Claude drafts or repairs `PLAN_FILE`.
3. Controller validates and locks the plan.
4. Controller issues one or more orders.
5. Claude sends agmsg to Codex with:
   - fixed handoff header
   - one-line objective
   - paths for PLAN, ORDER, RESULT, Evidence, and optional patch artifact
   - escalation trigger
6. Codex executes from ORDER.
7. Codex writes RESULT and Evidence.
8. Controller validates and closes, or escalates.

## Lane B: Claude Unavailable

Use this when Claude is absent or should not be used.

1. Split kitty into left and right panes.
2. Left pane is controller/planner:
   - owns case intake
   - writes or revises PLAN
   - issues ORDER
   - validates RESULT and Evidence
   - sends escalation decisions
3. Right pane is worker:
   - receives the fixed handoff header
   - reads PLAN and ORDER
   - edits directly only when the normal edit path is available
   - otherwise proposes a patch
   - writes RESULT
4. Left pane applies patches, verifies, and closes.

## Patch-Proposer Mode

Use this when direct editing is unavailable, blocked, unsafe, or outside the worker scope.

Required behavior:

1. Worker creates a unified diff as a careflow patch artifact when possible.
2. If artifact writing is unavailable, worker embeds the diff in RESULT.
3. Controller runs `git apply --check <patch>`.
4. Controller runs `git apply <patch>` only after the check passes.
5. Controller records check/apply output as Evidence.

Patch artifact location:

```text
.careflow/cases/<case_id>/patches/<order_id>-<slug>.patch
```

Patch summary location:

```text
.careflow/cases/<case_id>/results/<order_id>.result.md
```

## Escalation Triggers

Escalate to Claude or the left-pane controller when any of these occurs:

- PLAN and ORDER disagree.
- Required scope is missing from the ORDER.
- Verification fails twice for the same reason.
- The worker needs a product or architecture decision.
- The patch would touch forbidden paths.
- The worker has evidence that the plan assumption is false.

Escalation message must include:

```text
CASE_ID: <case_id>
ORDER_ID: <order_id>
BLOCKER: <one sentence>
DECISION_NEEDED: <one sentence>
FILES: <paths>
EVIDENCE: <paths>
```

## Close Gate

The controller may close only after inspecting:

- PLAN acceptance criteria
- ORDER completion criteria
- RESULT content
- Evidence files
- git status
- validation command output
