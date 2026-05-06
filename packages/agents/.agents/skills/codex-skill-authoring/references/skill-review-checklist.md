# Skill Review Checklist

Accept the skill only when:

- Trigger description is clear.
- `SKILL.md` body is procedural.
- References are one level deep.
- Scripts are deterministic and syntax-valid.
- No redundant docs were created.
- Japanese body is allowed, keys/identifiers remain English.

Reject or revise when:

- The `description` omits the real trigger words.
- `SKILL.md` duplicates large reference content.
- A README, CHANGELOG, INSTALL, or similar auxiliary doc was added without explicit need.
- A script mutates files without explicit output arguments or documented scope.
- Two skills use the same `name`.
- A broad domain mega-skill hides reusable Codex feature knowledge that should be split into feature-specific skills.

Prefer feature-specific Codex skills for reusable platform behavior:

- AGENTS.md instruction scope -> `codex-agents-md-authoring`
- `.codex/rules` command policy -> `codex-rules-authoring`
- subagent TOML and role ownership -> `codex-subagents-authoring`
- timestamped plans and split plans -> `codex-plan-authoring`

Official sources:

- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/subagents
