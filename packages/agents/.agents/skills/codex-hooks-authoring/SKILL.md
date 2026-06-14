---
name: codex-hooks-authoring
description: Design, review, or repair Codex hooks. Use for hooks.json, inline [hooks], dispatcher scripts, hook output schemas, PreToolUse, PermissionRequest, PostToolUse, UserPromptSubmit, Stop, SessionStart, hooks feature flag, and high-risk Codex hook behavior.
---

# codex-hooks-authoring

Use this skill before changing Codex hook configuration, dispatcher scripts, or hook wire-format behavior.

## Procedure

1. Read `references/hook-event-matrix-template.md` and create a filled hook event matrix before design or implementation.
2. Read `references/hooks-wire-format.md` for event inputs, outputs, matcher behavior, merge behavior, trust, and timeout rules.
3. Read `references/hook-design-review-checklist.md` before accepting a hook design or diff.
4. For high-risk behavior, verify against official docs, openai/codex source schema, and a local runtime probe.
5. Label any claim from local commands as `runtime-observed`.

## Hard Rules

- Do not design hooks without first creating a hook event matrix.
- Do not rely on unsupported allow paths in PreToolUse.
- Do not use old PermissionRequest output format; use `hookSpecificOutput.decision.behavior`.
- Do not treat PostToolUse as undo.
- Do not emit plain stdout from Stop.
- Always check docs, source schema, and runtime probe when behavior is high risk.
