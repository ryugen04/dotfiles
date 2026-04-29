# AI-DLC

AI-DLC は `root-system` を control-plane にし、child repo の実ファイル差分を root diff に見せる運用基盤です。

最短手順:

1. `./install.sh codex agents`
2. `ai-dlc install`
3. `ai-dlc doctor`
4. root-system repo で `ai-dlc init-project`
5. worktree 内で `ai-dlc init-workspace`
6. `ai-dlc validate-overlay`

補足:

- user-level hooks の正本は `~/.codex/hooks.json`
- hook 本体は `~/.codex/ai-dlc/hooks/dispatcher.py`
- project 側 `.codex/` には workspace 固有の境界設定だけを置く
- AI-DLC workspace ではない repo でも `.codex/config.toml` の `[guardrails] subagent_required = true` で controller-only 制約を有効化できる
