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

## Kitty Lane

Use this as the default fast lane. It is kitty-only and does not use cmux.

1. Controller creates or selects a case and order.
2. Controller starts a kitty careflow tab:
   - `careflow-kitty-start --case <case_id> --order <order_id> --controller claude --worker codex`
   - Use `--controller codex` for a Codex-led plan lane.
3. Left pane controller writes or repairs `PLAN_FILE`, validates it, and issues `ORDER_FILE`.
4. When the user says go, controller sends the fixed handoff to the right pane:
   - `careflow-kitty-go --case <case_id> --order <order_id>`
5. Right pane worker executes from ORDER and writes RESULT.
6. Worker escalates blockers left through agmsg:
   - `careflow-escalate-left --case <case_id> --order <order_id> --blocker "<one sentence>" --decision-needed "<one sentence>"`
7. Controller reads the agmsg, decides, updates PLAN/ORDER, and re-runs `careflow-kitty-go` when work can continue.
8. Controller validates RESULT/Evidence and closes, or escalates.

## Kitty Command Contract

The kitty lane relies on saved window ids, not pane-title guessing:

```text
.careflow/cases/<case_id>/kitty/session.env
```

Required commands:

- `agmsg`: file-backed message store.
- `careflow-handoff`: prints the fixed handoff header.
- `careflow-kitty-start`: opens controller/worker kitty panes and records ids.
- `careflow-kitty-go`: sends the handoff to the worker pane and records an agmsg.
- `careflow-escalate-left`: records an escalation agmsg and sends a notification to the controller pane.

If kitty remote control is unavailable, use `careflow-handoff` and `agmsg` manually, then record the blocker in RESULT or Incident.

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
