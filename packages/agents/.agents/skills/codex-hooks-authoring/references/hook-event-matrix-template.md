# Hook Event Matrix Template

Fill this table before designing or changing hooks.

| Event | Official trigger | Matcher target | Input keys | Valid stdout | Blocks/continues | Fail-open/closed | AI-DLC use | Must hit | Must not hit | Probe required |
|---|---|---|---|---|---|---|---|---|---|---|
| SessionStart | Session startup, resume, or clear | `source` | common fields + `source` | JSON `additionalContext` or plain context | Continues only | Context mistakes fail open into bad guidance | Context injection only | session startup/resume | permission/path enforcement | Yes |
| UserPromptSubmit | Before user prompt is sent | matcher ignored | common fields + `turn_id` + `prompt` | JSON `additionalContext` or block, plain context | Can block prompt | Wrong block fails closed | Detect `AI_DLC_SAFETY_DOMAIN=codex_config_edit`, persist initial user instruction, classify workflow | first prompt and subsequent prompt deltas | tool permission decisions | Yes |
| PreToolUse | Before supported tool execution | `tool_name` and aliases | common fields + `turn_id` + `tool_name` + `tool_use_id` + `tool_input` | JSON deny/block or exit 2 stderr | Can block before execution | Unsupported allow/update paths fail open | Block destructive or lease-violating tool calls before execution | Bash/apply_patch/Edit/Write/MCP before execution | approval escalation decisions that belong to PermissionRequest | Yes |
| PermissionRequest | When Codex is already requesting approval | `tool_name` and aliases | common fields + `turn_id` + `tool_name` + `tool_input` | JSON `decision.behavior` allow/deny | Can short-circuit approval prompt | Reserved fields fail closed | Approval prompt short-circuit only when Codex is already requesting approval | sandbox/network/escalation approval request | normal non-approval commands | Yes |
| PostToolUse | After supported tool output | `tool_name` and aliases | common fields + `turn_id` + `tool_name` + `tool_use_id` + `tool_input` + `tool_response` | JSON `additionalContext`/block or exit 2 stderr | Continues after completed tool | Cannot undo side effects | Side-effect inspection, evidence/context updates | after relevant tools | pre-execution blocking or undo assumptions | Yes |
| Stop | Assistant turn end | matcher ignored | common fields + `turn_id` + `stop_hook_active` + `last_assistant_message` | JSON only on exit 0 | Block continues the turn | Plain stdout invalid | Final checkpoint/handoff/lease continuation | assistant turn end | plain stdout output or ordinary command gating | Yes |

Official sources:

- https://developers.openai.com/codex/hooks
- https://github.com/openai/codex/blob/main/codex-rs/hooks/src/schema.rs
