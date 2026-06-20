# dotfiles

macOS/Linux 環境の dotfiles 管理リポジトリ。

## Packages

- `codex`: `~/.codex` を配備する Codex 設定
- `codex-careflow`: `~/.codex-careflow` を配備する Careflow 補助ツール
- `agents`: `~/.agents/skills` を配備する agent skills
- そのほか shell / git / nvim などの通常 dotfiles package

## Install

通常 package は GNU Stow で `$HOME` に展開します。`codex` だけは安全のため `.codex` 全体を stow せず、portable files の symlink と local `config.toml` の managed block を生成します。

前提として `agent-careflow` CLI を先にインストールし、`command -v agent-careflow` が成功する状態にしてください。旧 `careflow` / `aidlc` / `ai-dlc` CLI は Codex hooks から参照しません。`codex-careflow` package は dotfiles 側の補助 doctor と docs の配布であり、Careflow 本体のインストーラではありません。

```bash
./install.sh codex codex-careflow agents
```

- `packages/codex/.codex/AGENTS.md`、`hooks.json`、`rules/` が `~/.codex` へ配備される portable source
- `packages/codex/.codex/config.toml.template` は local `~/.codex/config.toml` の managed block 生成元
- `packages/codex-careflow/.codex-careflow/` が `~/.codex-careflow` の正本
- `packages/agents/.agents/skills/` が `~/.agents/skills` の正本
- repo 直下 `.codex/` はこの dotfiles 自身の project-local 設定と作業記録用

既存 `~/.codex/config.toml` は保持され、managed block だけが追加・更新されます。trusted project path などの PC 固有設定は managed block の外に置いてください。
user-level install の dry-run は実 HOME に依存させず、fixture HOME を渡して検証します。

```bash
DOTFILES_TARGET_HOME=/tmp/dotfiles-home ./install.sh -n codex
```

任意 repo へ Careflow / Sango 前提の project-local 設定を配布する場合:

```bash
./install.sh workspace-careflow /path/to/workspace
./install.sh codex-project /path/to/repo
./install.sh claude-project /path/to/repo
./install.sh sango-project /path/to/repo
```

既存の polyrepo workspace には `workspace-careflow` を使います。これは
既存の `workspace.yaml` / `.aidlc/workspace.yaml` / `sango.yaml` を置き換えず、
共有 `.careflow` store、`.worktrees` 配下の symlink、project-local Claude
Careflow rule を配備します。

`codex-project` / `claude-project` / `sango-project` の引数は、単一 repo root
でも workspace-henry のような polyrepo workspace root でも構いません。
bootstrap は共有 `.careflow` store を用意し、ancestor に既存 store があれば
target root の `.careflow` をそこへ symlink します。case/order/result/evidence
は共有し、active case/order は worktree/session scope で扱う前提です。

project-local bootstrap は unmanaged file を上書きしません。dotfiles-managed marker 付きでも内容がローカル変更されている場合は `--force` なしでは拒否します。
既存 `.careflow` runtime store は削除しません。`.worktrees` 配下に孤立した
`.careflow` directory がある場合、通常は警告して残します。`--force` 指定時
のみ共有 store の `migrated/` へ退避して symlink に置き換えます。

shell package には `sango worktree create` 成功後に
`./install.sh workspace-careflow "$(sango root)"` を再実行する薄い wrapper も
含めています。手動で同期したい場合は `careflow_sync_workspace /path/to/workspace`
を使います。

## Codex / Careflow

Portable Codex / Careflow / Sango のテンプレートと検証方針は `codex-plan.md` を正本にします。
tracked config には個人の home directory、machine-local worktree、project trust path を置きません。
project trust は各マシンの local config で追加してください。

Careflow doctor と portability scan は read-only です。`FORBIDDEN_WORDS` は CI secret または local env から渡し、repo には書きません。

```bash
FORBIDDEN_WORDS="$FORBIDDEN_WORDS" scripts/check-portability.sh
python3 packages/codex-careflow/.codex-careflow/bin/doctor.py --repo .
python3 packages/codex-careflow/.codex-careflow/bin/doctor.py --repo . --project-repo /path/to/repo
```

## GitHub Rulesets

新規リポジトリ向けの repository ruleset テンプレートは `.github/rulesets/` に置いています。
管理者以外の push / branch 更新を止め、Issues は通常どおり許可する用途では `admin-only-branches.json` を使います。
