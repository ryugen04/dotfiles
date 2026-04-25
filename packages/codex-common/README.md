# codex-common

`codex-common` は project 非依存の Codex 共通層を `~/.config/codex-common` へ配備する stow package。

## Contents

- `hooks/`: 共通 hook 実装（`pre_tool_use`, `stop`, `session_start`, `user_prompt_submit`）
- `templates/ai-dlc/`: plan/review/execution/learnings の共通テンプレート
- `rules/base.rules`: 共通 rules の正本

## Rollout Steps

1. Step A: dotfiles に `packages/codex-common` を追加
2. Step B: project `.codex/hooks/*.py` を薄いラッパーへ切替
3. Step C: project `default.rules` を `base.rules + project.rules` 生成方式へ切替
4. Step D: 動作確認後に旧ロジックを削除
5. Step E: 横展開時は `./install.sh -n codex-common` -> `./install.sh codex-common` で適用

## Notes

- `~/.codex` は実行時データを保持し、`codex-common` と分離する。
- project 固有データ（plans/artifacts）は project repo に残す。
