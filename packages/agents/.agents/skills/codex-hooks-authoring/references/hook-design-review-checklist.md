# Hook Design Review Checklist

Reject the design or diff when any item applies:

- Missing event matrix.
- `timeout` treated as milliseconds.
- `PermissionRequest` using `permissionDecision`.
- Hook gates that can deadlock without an explicit user-instructed break-glass decision marker.
- Project-local hook designs that duplicate generic user-level guardrails or block plan/learnings self-repair paths.
- `Stop` hooks that continue forever instead of naming the exact missing decision or evidence.
- `PreToolUse` design depending on allow.
- `Stop` plain stdout.
- `PostToolUse` described as undo.
- No runtime probe for high-risk hook output.

Required review checks:

- Confirm event trigger and matcher target.
- Confirm exact input keys used by the script.
- Confirm stdout JSON shape and event-specific output keys.
- Confirm fail-open/fail-closed behavior.
- Confirm project trust if hook is project-local.
- Confirm `hooks.json` and inline `[hooks]` merge behavior if both may exist.
- Confirm source schema and official docs agree, or label differences as `runtime-observed`.

Official sources:

- https://developers.openai.com/codex/hooks
- https://github.com/openai/codex/blob/main/codex-rs/hooks/src/schema.rs
