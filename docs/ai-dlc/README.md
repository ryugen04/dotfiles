# AI-DLC

AI-DLC は `root-system` を control-plane にし、child repo の実ファイル差分を root diff に見せる運用基盤です。

## Repo Bootstrap

1. `./install.sh codex agents`
2. `ai-dlc install`
3. `ai-dlc doctor`
4. root-system repo で `ai-dlc init-project`

詳細は `project-setup.md` を参照。

## Workspace Bootstrap

1. root-system worktree を作る
2. worktree 内で `ai-dlc init-workspace`
3. `ai-dlc validate-overlay`
4. `ai-dlc bootstrap`

詳細は `workspace-setup.md` を参照。

## Controller-Only Project Template

AI-DLC workspace ではない repo でも controller-only 制約だけを有効化したい場合は、対象 repo で次を実行する。

`ai-dlc init-project --project-kind controller-only`

補足:

- user-level hooks の正本は `~/.codex/hooks.json`
- hook 本体は `~/.codex/ai-dlc/hooks/dispatcher.py`
- project 側 `.codex/` には workspace 固有の境界設定だけを置く
- controller-only project の正式テンプレートは `controller-only-project.md` を参照
