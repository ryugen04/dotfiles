# Config Audit Checklist

Run this checklist before and after config edits.

- Check active config layer.
- Check project trust.
- Check deprecated keys.
- Check unknown keys.
- Check approval/sandbox interaction.
- Check hooks enabled.
- Check hooks source merge.
- Check profile used by CLI convention.

Suggested evidence commands:

```bash
rg -n "approval_policy|approvals_reviewer|sandbox_mode|codex_hooks|profiles\\.|projects\\." .codex packages/codex/.codex
rg -n "on-failure|AI_DLC|safety_domain" .codex packages/codex/.codex
```

Audit matrix:

| Area | Expected | Evidence |
|---|---|---|
| active config layer | user/project layer understood | runtime probe or config path note |
| project trust | trusted path for project-local config/hooks | `[projects."<path>"] trust_level` |
| deprecated keys | no `on-failure` | `rg on-failure` |
| unknown keys | no unsupported Codex keys | config reference comparison |
| approval/sandbox | `codex-config-edit` uses `on-request` + `workspace-write` | profile stanza |
| hooks enabled | `[features] codex_hooks = true` when hooks are needed | config stanza |
| hooks source merge | no accidental double registration | hooks source inventory |
| CLI profile | `--profile codex-config-edit` used | command log |

Official sources:

- https://developers.openai.com/codex/config-reference
- https://developers.openai.com/codex/hooks
