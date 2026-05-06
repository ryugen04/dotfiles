# Project Setup

このページは repo bootstrap だけを扱う。workspace 作成は `workspace-setup.md` を参照。

1. dotfiles を反映する: `./install.sh codex agents`
   既存の `~/.codex/AGENTS.md` / `config.toml` / `hooks.json` が実体ファイルなら先に退避する。
2. user-level 配置を確認する: `ai-dlc install && ai-dlc doctor`
3. root-system repo で `ai-dlc init-project --repo web=... --repo backend=...`
4. 生成された `AGENTS.md`、`.codex/config.toml`、`.gitignore`、`ai-dlc/.gitkeep` を確認する。
5. project main には汎用 hooks や user-level 設定を混ぜない。
6. project 側 `.codex/` は workspace 固有の実行境界だけを持たせる。
7. `.codex/hooks.json` や `.codex/hooks/*.py` を置くのは project 固有の挙動が本当に必要な場合だけにする。generic な plan gate、learning gate、Git finish gate は dotfiles 管理の user-level hooks に寄せる。

補足:

- 既存の `.codex/config.toml` がある場合、`init-project` はそれを上書きしない。
- AI-DLC workspace を作らず controller-only 制約だけ入れたい repo では `ai-dlc init-project --project-kind controller-only` を使う。
- 既存 repo に generic な `.codex/hooks.json` や `.codex/hooks/*.py` が残っている場合は、project 固有の理由が無ければ削除する。
