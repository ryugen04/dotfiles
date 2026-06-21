---
name: careflow-kitty-agmsg
description: Use when Claude is coordinating Careflow work in kitty with the current pane as controller, right pane as worker, explicit go, agmsg escalation, and no cmux handoff.
when_to_use: |
  triggered by "careflow", "kitty lane", "agmsg", "explicit go", "worker escalation", "Codex worker", "Claude controller", "current pane controller"
---

# careflow-kitty-agmsg

Use this when Claude is the controller/planner for a Careflow case and work is handed to Codex or Claude in a right kitty pane.

## Contract

- Current pane is the controller. Do not open a replacement controller tab.
- Right pane becomes the worker only after PLAN/ORDER approval and explicit go.
- `.careflow` is the durable source of truth for Case, Plan, Order, Result, Evidence, Incident, and messages.
- agmsg records go/escalation messages under `.careflow/cases/<case_id>/messages/`.
- cmux is not a Careflow handoff path.

## Controller Start

From the existing Claude controller pane:

```bash
careflow-kitty-start --case <case_id> --order <order_id> --controller claude --worker codex
```

This records the current pane as controller and leaves worker unresolved.

Before go, verify:

```bash
agent-careflow order status --case <case_id> --order <order_id>
```

## Explicit Go

After PLAN/ORDER approval and user go:

```bash
careflow-kitty-go --case <case_id> --order <order_id>
```

Expected behavior:

- Reuse a marked right worker for the same case/order.
- Start the worker agent in an idle right shell.
- Open a right split if no right pane exists.
- Refuse unknown, busy, or different-case panes.
- Start new worker agents through the user's interactive shell so shell rc PATH/env loads.

## Worker Escalation

Workers escalate with:

```bash
careflow-escalate-left \
  --case <case_id> \
  --order <order_id> \
  --blocker "<one sentence>" \
  --decision-needed "<one sentence>" \
  --files "<paths>" \
  --evidence "<paths>"
```

Controller response:

1. Read the agmsg file.
2. Inspect PLAN, ORDER, RESULT, and Evidence.
3. Repair CASE/PLAN/ORDER if the escalation is valid.
4. Re-run `agent-careflow order status` when schema validity is involved.
5. Send revised go to the same worker pane.

## Stop Conditions

Stop instead of sending work when:

- PLAN is draft or contradicts ORDER.
- ORDER lacks schema fields required by `agent-careflow order status`.
- Expected result path is missing or outside scope.
- Right pane is unmarked, busy, or belongs to another case/order.
- The operation would require cmux as the handoff path.
