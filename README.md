# dotfiles

macOS/Linux 環境の dotfiles 管理リポジトリ。

## Packages

- `codex`: `~/.codex` を配備する Codex 設定
- `agents`: `~/.agents/skills` を配備する agent skills
- そのほか shell / git / nvim などの通常 dotfiles package

## Install

GNU Stow で package を `$HOME` に展開します。

```bash
./install.sh codex agents
```

- `packages/codex/.codex/` が `~/.codex` の正本
- `packages/agents/.agents/skills/` が `~/.agents/skills` の正本
- repo 直下 `.codex/` はこの dotfiles 自身の project-local 設定と作業記録用

## AI-DLC Redesign

AI-DLC Clinical OS の再設計計画は `codex-plan.md` を正本にします。
旧 dotfiles 内実装は source of truth ではありません。

既存の `~/.codex/config.toml` が実体ファイルの場合、`codex` package の Stow 配置と衝突します。
先に退避してから `./install.sh codex agents` を実行してください。

## GitHub Rulesets

新規リポジトリ向けの repository ruleset テンプレートは `.github/rulesets/` に置いています。
管理者以外の push / branch 更新を止め、Issues は通常どおり許可する用途では `admin-only-branches.json` を使います。
