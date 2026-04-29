# Controller-Only Project

AI-DLC workspace を作らず、repo を controller-only 運用にしたい場合の正式テンプレート。

## 作成

対象 repo で次を実行する。

`ai-dlc init-project --project-kind controller-only`

生成物:

- `AGENTS.md`
- `.codex/config.toml`

`init-project` は既存の `.codex/config.toml` がある場合、それを上書きしない。

## テンプレート内容

`.codex/config.toml` には少なくとも次が入る。

```toml
sandbox_mode = "workspace-write"
approval_policy = "on-request"

[features]
codex_hooks = true
shell_snapshot = true

[guardrails]
subagent_required = true
```

必要なら project 側で `bootstrap_extra_commands` などを追加して、許可する bootstrap コマンドを絞る。
