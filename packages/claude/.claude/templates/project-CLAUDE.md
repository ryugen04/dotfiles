# dotfiles-managed: claude-careflow-project-v1
# Project Claude Careflow Baseline

For non-trivial implementation, review, investigation, configuration changes,
or cross-agent handoff, use `.careflow` as the project coordination source of
truth.

Before mutating files or claiming completion, know the active:

- Case: `.careflow/cases/<case_id>/CASE.yaml`
- Plan: `.careflow/cases/<case_id>/PLAN.md`
- Order: `.careflow/cases/<case_id>/orders/<order_id>.order.md`
- Result: `.careflow/cases/<case_id>/results/<order_id>.result.md`
- Evidence: `.careflow/cases/<case_id>/evidence/`

Read `.claude/rules/careflow-workspace.md` before delegating to Codex, Claude
subagents, Cursor, or another external agent. Do not use `.claude/plans` or
`.claude/work` as the durable completion record.

Every handoff must start with these exact labels in this order:

```text
PLAN_FILE: <.careflow/cases/<case_id>/PLAN.md>
ORDER_FILE: <.careflow/cases/<case_id>/orders/<order_id>.order.md>
SUBPLAN_FILE: <same path as ORDER_FILE unless a child order exists>
EXPECTED_RESULT_PATH: <.careflow/cases/<case_id>/results/<order_id>.result.md>
CASE_ID: <case_id>
ORDER_ID: <order_id>
ASSIGNED_ROLE: <researcher|implementer|verifier|reviewer|incident-commander>
TARGET_TOOL: <codex|claude|cursor>
```
