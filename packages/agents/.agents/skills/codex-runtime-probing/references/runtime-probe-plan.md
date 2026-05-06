# Runtime Probe Plan

Use focused probes and record results as `codex.runtime_probe.v1` JSONL.

Official sources:

- https://developers.openai.com/codex/hooks
- https://developers.openai.com/codex/config-reference
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/subagents
- https://github.com/openai/codex/blob/main/codex-rs/hooks/src/schema.rs

## Required Probes

- `codex --version`
- `codex --profile codex-config-edit --help`
- config layer read path
- `hooks.json` + inline `[hooks]` merge
- SessionStart payload
- UserPromptSubmit payload
- PreToolUse payload and deny output
- PermissionRequest payload and allow/deny output
- PostToolUse payload
- Stop JSON vs plain stdout behavior

## Notes

- Keep output under a planned path such as `.codex/probes/<issue>/runtime-probe.jsonl`.
- Do not store probe logs in arbitrary scratch when they are evidence for a change.
- For each event, record command, cwd, stdin payload, stdout, stderr, exit code, verdict, and notes.
- If docs/source and runtime disagree, preserve both facts and mark the runtime result as `runtime-observed`.
