---
name: codex-config-authoring
description: Author or audit Codex config.toml, project trust, profiles, sandbox, approval policy, hooks source configuration, managed requirements, and Codex profile/policy keys. Use before editing .codex/config.toml or packages/codex/.codex/config.toml.
---

# codex-config-authoring

Use this before editing `.codex/config.toml`, `packages/codex/.codex/config.toml`, or Codex profile/policy keys.

## Procedure

1. Read `references/config-reference.md` for supported keys and official links.
2. Read `references/config-audit-checklist.md` and audit the active config layer, project trust, approval/sandbox posture, hooks enablement, and unknown keys.
3. Validate each key/value against the official config reference.
4. Do not introduce unknown config keys unless intentionally consumed by project-local tooling and documented.
5. Do not use `approval_policy = "never"` for `codex-config-edit`; use `on-request`.
6. Treat `-c` as a Codex override only, not as an AI-DLC mode source.

For high-risk behavior, pair this skill with `codex-runtime-probing`.
