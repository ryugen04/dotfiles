# AGENTS.md Scope

Official and practice references:

- https://developers.openai.com/codex/guides/agents-md
- https://agents.md/
- https://openai.com/index/unrolling-the-codex-agent-loop/

## Policy

- User-level `~/.codex/AGENTS.md` is a stable base policy.
- Project-level `AGENTS.md` adds repo-specific build, test, safety, and layout rules.
- Keep always-loaded guidance concise. Long tables and procedures belong in skills or references.
- Do not mix command approval policy into prose when `.codex/rules` or hooks can enforce it.
- Do not put temporary task status in `AGENTS.md`.

## Move Out Of AGENTS.md

- Multi-step workflows -> skills.
- Shell escalation policy -> `.codex/rules/*.rules`.
- Hook wire format and event matrices -> hook authoring references.
- Subagent role details -> `agents/*.toml` and subagent authoring skill.
- Large task plans -> `.codex/plans/YYYYMMDDHH-{planname}.md`.

