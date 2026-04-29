# Codex AI-DLC Instructions

## Language

- 対話は日本語
- 変数名と識別子は英語
- コメントは必要最小限の日本語

## AI-DLC Core

- `root-system` は control-plane であり、通常の実装 repo として扱わない。
- `literal_worktree_overlay` では `web/` や `backend/` は root diff に見えるが、commit は child repo で行う。
- root controller session は基本的に controller-only とし、実作業は AI-DLC subagent に委譲する。
- `ai-dlc validate-overlay` と `ai-dlc validate` を通る状態を保つ。
- `root-system` overlay branch は push しない。root 側の成果物反映は `ai-dlc root-export` を使う。

## Safety

- `web/**` / `backend/**` を root-system から commit しない。
- `ai-dlc/executions/**` と `ai-dlc/scratch/**` は commit しない。
- `git reset --hard`、`git clean`、`git push`、`git worktree remove` は明示承認なしで実行しない。
