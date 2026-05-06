---
name: codex-rules-authoring
description: Author or audit Codex .rules files for sandbox escalation command policy, including prefix_rule patterns, allow/prompt/forbidden decisions, match/not_match examples, execpolicy checks, and separation from hooks or AGENTS prose.
---

# codex-rules-authoring

Use before editing `.codex/rules/*.rules`.

## Procedure

1. Read `references/rules-policy.md`.
2. Use rules only for sandbox escalation command policy.
3. Keep allow rules narrow and justified.
4. Put dangerous commands in `prompt` or `forbidden`.
5. Include `match` and `not_match` examples for every rule.
6. Validate with `codex execpolicy check --pretty --rules <file> -- <command>`.

