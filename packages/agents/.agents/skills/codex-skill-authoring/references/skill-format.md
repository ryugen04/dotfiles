# Skill Format

Official source:

- https://developers.openai.com/codex/skills

Related official sources:

- https://developers.openai.com/codex/subagents
- https://developers.openai.com/codex/config-reference

## Required Files

Every skill is a directory containing:

- `SKILL.md`

`SKILL.md` must include YAML frontmatter and body instructions.

Required frontmatter keys:

- `name`
- `description`

Optional directories:

- `scripts/`
- `references/`
- `assets/`
- `agents/openai.yaml`

Do not create README, CHANGELOG, INSTALL, or extra docs unless explicitly requested and justified.

## Discovery

Repo skill scan behavior:

- Codex scans `.agents/skills` from the current working directory upward to the repo root.
- Duplicate skill names do not merge; avoid duplicate names across scanned skill roots.

When changing discovery-sensitive behavior, verify with runtime probing and label results `runtime-observed`.

## Authoring Guidance

- Put trigger scope in `description`, because Codex uses it for implicit skill activation.
- Keep `SKILL.md` procedural.
- Put detailed tables and schema notes in `references/`.
- Use scripts only for deterministic work that should not be rewritten each time.
- Keep keys and identifiers in English. Japanese body text is allowed.
