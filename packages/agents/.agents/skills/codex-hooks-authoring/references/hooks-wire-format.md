# Hooks Wire Format

Use this as a checklist; confirm current behavior against official docs and source schema before high-risk edits.

Official sources:

- https://developers.openai.com/codex/hooks
- https://developers.openai.com/codex/config-reference
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/subagents
- https://github.com/openai/codex/blob/main/codex-rs/hooks/src/schema.rs

## Config Shape

Hooks are nested as:

```text
event -> matcher group -> hooks
```

JSON shape:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^Bash$",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/hook.py",
            "timeout": 30,
            "statusMessage": "Checking Bash command"
          }
        ]
      }
    ]
  }
}
```

Inline TOML shape:

```toml
[features]
hooks = true

[[hooks.PreToolUse]]
matcher = "^Bash$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "python3 /path/to/hook.py"
timeout = 30
statusMessage = "Checking Bash command"
```

`timeout` is seconds. If omitted, Codex defaults to `600` seconds.

## Source Loading And Trust

- Hook sources can be `hooks.json` next to an active config layer or inline `[hooks]` tables inside `config.toml`.
- Matching hooks from multiple files all run.
- Higher-precedence config layers do not replace lower-precedence hooks.
- If a single layer contains both `hooks.json` and inline `[hooks]`, Codex merges them and warns at startup.
- Project-local hooks require the project `.codex/` layer to be trusted.

## Matcher Targets

- `SessionStart`: matcher applies to `source` (`startup`, `resume`, `clear`).
- `UserPromptSubmit`: matcher is ignored.
- `PreToolUse`: matcher applies to `tool_name` and aliases; `apply_patch` can match `apply_patch`, `Edit`, or `Write`.
- `PermissionRequest`: matcher applies to `tool_name` and aliases.
- `PostToolUse`: matcher applies to `tool_name` and aliases.
- `Stop`: matcher is ignored.

## Common Input Fields

Every command hook receives JSON on stdin:

- `session_id`
- `transcript_path`
- `cwd`
- `hook_event_name`
- `model`
- `permission_mode`

Turn-scoped hooks also include `turn_id` according to the source schema.

## Per-Event Input And Output

### SessionStart

- Input adds `source`.
- Plain stdout is added as context.
- JSON stdout can include `hookSpecificOutput.hookEventName = "SessionStart"` and `additionalContext`.

### UserPromptSubmit

- Input adds `turn_id` and `prompt`.
- Plain stdout is added as context.
- JSON stdout can add context or block the prompt with `decision = "block"` and `reason`.

### PreToolUse

- Input adds `turn_id`, `tool_name`, `tool_use_id`, and `tool_input`.
- Plain stdout is ignored.
- Supported blocking output is `hookSpecificOutput.hookEventName = "PreToolUse"` with `permissionDecision = "deny"` and `permissionDecisionReason`.
- Exit code `2` with stderr can block.
- Do not depend on `permissionDecision = "allow"` or `"ask"`; unsupported allow/update paths fail open.

### PermissionRequest

- Runs only when Codex is about to ask for approval.
- Input adds `turn_id`, `tool_name`, and `tool_input`; `tool_input.description` may contain a human-readable reason.
- Plain stdout is ignored.
- Approve or deny with:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow"
    }
  }
}
```

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "message": "Blocked by repository policy."
    }
  }
}
```

- Do not return `updatedInput`, `updatedPermissions`, or `interrupt`; these reserved fields fail closed today.

### PostToolUse

- Runs after supported Bash, `apply_patch`, and MCP tool calls produce output.
- Input adds `turn_id`, `tool_name`, `tool_use_id`, `tool_input`, and `tool_response`.
- Plain stdout is ignored.
- JSON stdout can add context and can block normal processing of the original tool result.
- It cannot undo side effects from the completed tool.

### Stop

- Input adds `turn_id`, `stop_hook_active`, and `last_assistant_message`.
- `Stop` expects JSON on stdout when exiting `0`; plain stdout is invalid.
- Returning `decision = "block"` with `reason` continues Codex with another prompt.

## Fail-Open / Fail-Closed Risks

- PreToolUse unsupported allow/update fields fail open; do not build policy on them.
- PermissionRequest reserved fields fail closed; keep output minimal.
- PostToolUse cannot undo side effects; use it for evidence/context, not enforcement.
- Stop plain stdout is invalid and can break finalization.
