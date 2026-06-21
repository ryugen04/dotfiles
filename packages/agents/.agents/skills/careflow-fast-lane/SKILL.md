---
name: careflow-fast-lane
description: Use when running a fast but durable careflow workflow with Plan, Order, Result, Evidence, agmsg handoff to Claude, Codex-to-Claude escalation, patch-gated edits, or dual Codex sessions in kitty.
---

# careflow-fast-lane

Use this when a task should move quickly but still preserve session-external records and escalation paths.

## Procedure

1. Establish context before implementation or completion claims:
   - `PLAN_FILE`
   - `ORDER_FILE`
   - `SUBPLAN_FILE`
   - `EXPECTED_RESULT_PATH`
   - `CASE_ID`
   - `ORDER_ID`
   - `ASSIGNED_ROLE`
   - `TARGET_TOOL`
2. Read the assigned PLAN and ORDER. Treat the ORDER as the worker subplan.
3. Choose the lane:
   - Kitty lane: the current pane is controller/planner; the right pane is worker/executor after explicit go.
   - Fallback lane: if kitty remote control is unavailable, use the same handoff text and agmsg files manually.
4. Preserve durable records:
   - PLAN stores objective, scope, acceptance criteria, escalation triggers, verification, and rollback.
   - ORDER stores the assigned role, scope, and expected result path.
   - RESULT records outcome before completion is claimed.
   - Evidence records checks, failed attempts, and external decisions.
   - Incidents record plan defects, blocked execution, or escalation events.
5. Use path references in agmsg. Send case/order/result/patch paths instead of copying long plans.
6. If direct edits are unavailable, switch to patch-proposer mode:
   - Produce a unified diff as a careflow patch artifact or in RESULT.
   - Require controller `git apply --check` before `git apply`.
   - Do not require OS namespace, setuid, AppArmor, or bubblewrap repair for normal work.
7. Escalate back to the controller when the worker finds a plan defect, missing scope, repeated verification failure, or unclear product decision.
8. Do not mark an order complete from file existence alone. Inspect RESULT content and required Evidence.

## Required Handoff Header

Every cross-session or cross-tool handoff starts with these exact labels, in this order:

```text
PLAN_FILE: .careflow/cases/<case_id>/PLAN.md
ORDER_FILE: .careflow/cases/<case_id>/orders/<order_id>.order.md
SUBPLAN_FILE: .careflow/cases/<case_id>/orders/<order_id>.order.md
EXPECTED_RESULT_PATH: .careflow/cases/<case_id>/results/<order_id>.result.md
CASE_ID: <case_id>
ORDER_ID: <order_id>
ASSIGNED_ROLE: <researcher|implementer|verifier|reviewer|incident-commander>
TARGET_TOOL: <codex|claude|cursor>
```

## Kitty Controller/Worker Lane

This is the preferred lane. It does not use cmux.

1. From the current controller pane, bind the case/order:
   - `careflow-kitty-start --case <case_id> --order <order_id> --worker codex`
   - This records the current pane as controller and does not open a replacement controller tab.
2. Current-pane controller writes or revises `PLAN_FILE`, validates it, and issues `ORDER_FILE`.
3. When the user says go, the controller resolves and dispatches to the worker:
   - `careflow-kitty-go --case <case_id> --order <order_id>`
   - If a marked right worker pane exists for the same case/order, it is reused.
   - If the right pane is an idle shell, the worker agent starts there.
   - If no right pane exists, a right split is opened and the worker agent starts there.
   - Unsafe existing panes are refused instead of receiving the handoff.
4. New worker agents run through the user's interactive shell so `.bashrc`/`.zshrc`-style setup is loaded.
5. Right pane worker reads PLAN and ORDER, executes only the assigned scope, and writes `EXPECTED_RESULT_PATH`.
6. If blocked, the worker escalates left through agmsg and kitty:
   - `careflow-escalate-left --case <case_id> --order <order_id> --blocker "<one sentence>" --decision-needed "<one sentence>"`
7. Current-pane controller reads the agmsg file, decides, updates PLAN/ORDER if needed, and sends a revised handoff.
8. Current-pane controller verifies RESULT/Evidence and either closes the case or revises PLAN/ORDER.

## File-Backed Agmsg

- `agmsg send` records messages under `.careflow/cases/<case_id>/messages/` when the case exists.
- `agmsg list --case <case_id> --to controller` shows worker escalations.
- `agmsg read --case <case_id>` reads the latest message.
- agmsg stores paths and decisions; it does not replace PLAN, ORDER, RESULT, Evidence, or Incident artifacts.

## References

- `references/fast-lane-protocol.md`
- `references/templates.md`
