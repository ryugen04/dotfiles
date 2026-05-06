---
name: codex-runtime-probing
description: Verify local Codex runtime behavior for config, hooks, profiles, hook payloads, hook stdout parsing, schema compatibility, and codex_config_edit safety-domain changes.
---

# codex-runtime-probing

Use when docs/source are insufficient or implementation edits hook/config behavior.

## Procedure

1. Read `references/runtime-probe-plan.md` and choose the smallest probe set that answers the question.
2. Store logs in a planned output path, not arbitrary scratch.
3. Use `scripts/probe_hook_payload.py` as a hook command when capturing hook stdin payloads.
4. Validate JSONL logs with `scripts/validate_probe_log.py`.
5. Label conclusions from local commands as `runtime-observed`.

Probe before broad changes. Do not generalize from one event to another without an event-specific probe.
