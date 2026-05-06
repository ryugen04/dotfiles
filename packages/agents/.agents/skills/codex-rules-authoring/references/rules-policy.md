# Codex Rules Policy

References:

- https://developers.openai.com/codex/rules
- Runtime command: `codex execpolicy check --pretty --rules <file> -- <command>`

## Decisions

- `allow`: safe, narrow, read-oriented, repeatable.
- `prompt`: mutating or publishing actions that may be valid with approval.
- `forbidden`: broadly destructive actions such as generic `rm -rf`.

## Boundaries

Rules do not replace hooks, sandboxing, or plan validation. They only affect command approval behavior outside the sandbox.

## Required Shape

Every rule should include:

- `pattern`
- `decision`
- `justification`
- `match`
- `not_match`

