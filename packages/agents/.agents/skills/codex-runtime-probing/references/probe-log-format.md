# Probe Log Format

Each line is one JSON object:

```json
{
  "schema": "codex.runtime_probe.v1",
  "recorded_at": "ISO-8601",
  "codex_version": "string",
  "probe": "string",
  "event": "SessionStart|UserPromptSubmit|PreToolUse|PermissionRequest|PostToolUse|Stop|config",
  "command": ["codex", "..."],
  "cwd": "string",
  "input_payload": {},
  "stdout": "string",
  "stderr": "string",
  "exit_code": 0,
  "verdict": "pass|fail|inconclusive",
  "notes": "string"
}
```

Rules:

- Use `schema = "codex.runtime_probe.v1"` exactly.
- Use ISO-8601 timestamps.
- Use only allowed events.
- Keep `command` as an argv array, not a shell string.
- Preserve stdout/stderr text without post-hoc cleanup.
- Use `inconclusive` when the probe ran but did not answer the question.
