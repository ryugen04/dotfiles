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
   - Claude available: use Claude as planner/replanner and agmsg for path-based handoff.
   - Claude unavailable: run two Codex sessions in kitty, left as controller and right as worker.
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
7. Escalate back to Claude when the worker finds a plan defect, missing scope, repeated verification failure, or unclear product decision.
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

## Claude And Agmsg Lane

1. Claude drafts or repairs `PLAN_FILE`.
2. Controller locks the plan and issues `ORDER_FILE`.
3. Claude sends an agmsg message containing the fixed handoff header and file paths only.
4. Codex reads the files, executes, and writes `EXPECTED_RESULT_PATH`.
5. If blocked, Codex writes an incident or blocker note and sends agmsg back to Claude with the exact decision needed.

## Dual Codex Kitty Lane

1. Left pane: controller/planner. Owns PLAN, ORDER, scope, evidence policy, escalation, and close validation.
2. Right pane: worker. Reads the handoff header and ORDER, performs implementation or patch proposal, writes RESULT.
3. Left pane verifies RESULT/Evidence and either closes the case or revises PLAN/ORDER.

## References

- `references/fast-lane-protocol.md`
- `references/templates.md`
