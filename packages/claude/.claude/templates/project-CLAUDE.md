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

## Kitty / agmsg Lane

When Claude is the left/current controller pane:

```bash
careflow-kitty-start --case <case_id> --order <order_id> --controller claude --worker codex
```

This binds the current Claude pane as controller. It must not open a replacement
controller tab and it must not start the worker before PLAN/ORDER approval.

After explicit go:

```bash
careflow-kitty-go --case <case_id> --order <order_id>
```

`careflow-kitty-go` resolves the right worker pane: reuse a marked worker, start
Codex in an idle right shell, or open a right split when missing. Unsafe existing
panes are refused. cmux is not a Careflow handoff path.

Workers escalate with:

```bash
careflow-escalate-left --case <case_id> --order <order_id> --blocker "<one sentence>" --decision-needed "<one sentence>"
```

Escalations are recorded under `.careflow/cases/<case_id>/messages/` by agmsg.
