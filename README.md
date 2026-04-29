# dotfiles

dotfiles と AI-DLC 配布リポジトリ。

## Packages

- `codex`: `~/.codex` を配備する AI-DLC / Codex 基盤
- `agents`: `~/.agents/skills` を配備する AI-DLC workflow skills
- そのほか shell / git / nvim などの通常 dotfiles package

## AI-DLC

最短導入:

```bash
./install.sh codex agents
ai-dlc install
ai-dlc doctor
```

- `packages/codex/.codex/` が `~/.codex` の正本
- `packages/agents/.agents/skills/` が `~/.agents/skills` の正本
- repo 直下 `.codex/` はこの dotfiles 自身の project-local 設定と作業記録用

詳細は `docs/ai-dlc/` を参照。

既存の `~/.codex/AGENTS.md` や `~/.codex/config.toml` が実体ファイルの場合、`codex` package の Stow 配置と衝突する。先に退避してから `./install.sh codex agents` を実行する。
