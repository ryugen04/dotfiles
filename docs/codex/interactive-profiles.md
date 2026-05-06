# 対話セッションと profile

Codex 設定や hooks を編集する対話セッションでは、`codex-config-edit` profile を使う。

```bash
cd /home/glaucus03/dev/projects/dotfiles
codex --profile codex-config-edit
```

この profile は user-level config の `packages/codex/.codex/config.toml` にある。

```toml
[profiles.codex-config-edit]
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

## 使い分け

- `codex-config-edit`: Codex config、hooks、skills、subagents、schema、approval / sandbox 境界の編集。
- `review`: 読み取り中心の確認。
- `implement`: 通常実装を subagent などへ委譲する時の自動実行寄り profile。
- `fast`: 軽い確認や小さな実装。

## 起動後に確認すること

1. `~/.codex/config.toml` が dotfiles の `packages/codex/.codex/config.toml` を指しているか。
2. `~/.codex/hooks.json` が dotfiles の `packages/codex/.codex/hooks.json` を指しているか。
3. `codex_hooks` が有効か。
4. project-local `.codex/config.toml` の `[guardrails]` が意図通りか。

## 注意

`-c` は Codex runtime override であり、AI-DLC の workflow mode ではない。Codex config / hooks / skills / subagents を扱う時は、workflow の `safety_domain` を `codex_config_edit` として分類する。
