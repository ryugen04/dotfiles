# Codex Config Reference

Validate current behavior against official docs before changing keys.

Official sources:

- https://developers.openai.com/codex/config-reference
- https://developers.openai.com/codex/hooks
- https://developers.openai.com/codex/subagents
- https://developers.openai.com/codex/skills

## Approval Policy

Allowed `approval_policy` values:

- `untrusted`
- `on-request`
- `never`
- granular object:

```toml
approval_policy = { granular = { sandbox_approval = true, rules = true, mcp_elicitations = true, request_permissions = true, skill_approval = true } }
```

`on-failure` is deprecated. Use `on-request` for interactive runs and `never` only for non-interactive runs where approvals must not surface.

`approvals_reviewer` allowed values:

- `user`
- `auto_review`

## Hooks

Enable hooks with:

```toml
[features]
hooks = true
```

Hook sources can be:

- `hooks.json`
- inline `[hooks]` tables in `config.toml`

When more than one hook source exists, Codex loads all matching hooks. If one layer contains both `hooks.json` and inline `[hooks]`, Codex merges them and warns at startup. Prefer one representation per layer.

## Permissions

`default_permissions` builtins:

- `:read-only`
- `:workspace`
- `:danger-no-sandbox`

When editing permissions, confirm whether the active profile uses builtins or a named `[permissions.<name>]` profile.

## Profiles

Profiles are configured under `[profiles.<name>]` and used with `--profile <name>`. Profile-scoped values override top-level values for that session.

Required `codex-config-edit` profile:

```toml
[profiles.codex-config-edit]
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

Do not add `model = "gpt-5.5"` to this profile unless official config validation and local runtime support are confirmed.

## Command-Line Overrides

The CLI supports `--config, -c key=value` for per-invocation config overrides. Values parse as JSON when possible.

AI-DLC rule: `-c` is not a workflow or safety-domain source. Use the prompt marker `AI_DLC_SAFETY_DOMAIN=codex_config_edit` for the v1 classifier input.

## Project Trust

`[projects."<path>"] trust_level = "trusted"` enables project-scoped `.codex/` layers for that path. Untrusted projects skip project-scoped config, hooks, and rules.

## Unknown Keys

Do not add unknown AI-DLC-only keys to Codex config unless:

- local hook/tooling source explicitly reads them from the file,
- the key is documented where it is consumed,
- the config audit records the reader implementation and schema expectation.
