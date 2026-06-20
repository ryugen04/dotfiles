# Fast Lane Templates

## Agmsg Handoff Message

```text
PLAN_FILE: .careflow/cases/<case_id>/PLAN.md
ORDER_FILE: .careflow/cases/<case_id>/orders/<order_id>.order.md
SUBPLAN_FILE: .careflow/cases/<case_id>/orders/<order_id>.order.md
EXPECTED_RESULT_PATH: .careflow/cases/<case_id>/results/<order_id>.result.md
CASE_ID: <case_id>
ORDER_ID: <order_id>
ASSIGNED_ROLE: <researcher|implementer|verifier|reviewer|incident-commander>
TARGET_TOOL: <codex|claude|cursor>

OBJECTIVE: <one sentence>
PATCH_PATH: .careflow/cases/<case_id>/patches/<order_id>-<slug>.patch or none
EVIDENCE_DIR: .careflow/cases/<case_id>/evidence/
ESCALATE_IF: plan/order mismatch, forbidden path, repeated verification failure, missing decision
```

## Codex-To-Claude Escalation

```text
CASE_ID: <case_id>
ORDER_ID: <order_id>
BLOCKER: <one sentence>
DECISION_NEEDED: <one sentence>
PLAN_FILE: .careflow/cases/<case_id>/PLAN.md
ORDER_FILE: .careflow/cases/<case_id>/orders/<order_id>.order.md
RESULT_FILE: .careflow/cases/<case_id>/results/<order_id>.result.md
EVIDENCE: .careflow/cases/<case_id>/evidence/<file>
PATCH_PATH: .careflow/cases/<case_id>/patches/<order_id>-<slug>.patch or none
```

## Dual Codex Kitty Setup

```text
left pane: controller/planner
right pane: worker/executor

left responsibilities:
- create or select case
- maintain PLAN
- issue ORDER
- own escalation decisions
- verify RESULT and Evidence
- close case

right responsibilities:
- read handoff header
- follow ORDER as subplan
- implement or propose patch
- write RESULT
- stop on scope mismatch
```

## Patch Gate Commands

```bash
git apply --check .careflow/cases/<case_id>/patches/<order_id>-<slug>.patch
git apply .careflow/cases/<case_id>/patches/<order_id>-<slug>.patch
agent-careflow evidence collect --case <case_id> --kind git-status
```

## Minimal RESULT Shape

```markdown
# RESULT: <order_id>

order_id: <order_id>
case_id: <case_id>
status: complete|blocked
plan_path: .careflow/cases/<case_id>/PLAN.md
order_path: .careflow/cases/<case_id>/orders/<order_id>.order.md
expected_result_path: .careflow/cases/<case_id>/results/<order_id>.result.md

## Summary

- <what changed or what blocked>

## Changes

- <files changed, patch proposed, or no source files changed>

## Evidence

- <commands and evidence paths>

## Escalations

- <agmsg destination and decision request, or none>

## Blockers

- <remaining blocker, or none>
```
