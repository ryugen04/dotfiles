# Project Setup

1. dotfiles を反映する: `./install.sh codex agents`
   既存の `~/.codex/AGENTS.md` / `config.toml` / `hooks.json` が実体ファイルなら先に退避する。
2. user-level 配置を確認する: `ai-dlc install && ai-dlc doctor`
3. root-system repo で `ai-dlc init-project --repo web=... --repo backend=...`
4. 生成された `AGENTS.md`、`.codex/config.toml`、`.gitignore`、`ai-dlc/.gitkeep` を確認する。
5. project main には汎用 hooks や user-level 設定を混ぜない。
6. project 側 `.codex/` は workspace 固有の実行境界だけを持たせる。
