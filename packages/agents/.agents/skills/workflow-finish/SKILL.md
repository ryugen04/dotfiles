---
name: workflow-finish
description: Use when preparing an AI-DLC session for completion, including child repo commits, root-export, PR creation, cleanup, and final connectivity checks with approved Git operations only.
metadata:
  short-description: Finish-stage workflow
---

# workflow-finish

AI-DLC セッションを終了可能な状態へまとめ、承認済みの Git 操作だけを進めるときに使う。

## Controller Policy

- root session は finish 段階でも controller-only。
- controller は child repo commit/push、root-export、overlay-cleanup を直接実行しない。
- finish 段階の Git 操作は明示承認のある `dlc_git_operator` だけが担当する。

## Required Sequence

1. 現在地が task workspace であることを確認する。root-system や sango root なら対象 worktree に移動する。
2. `ai-dlc clean-state-check` を実行し、assignment、lease、report、diff の取り残しを確認する。
3. 最新の `dlc_verifier` evidence が overlay/test/runtime connectivity を見ていることを確認し、足りなければ verifier を先に起動する。
4. 独立した `dlc_evaluator` verdict が最新 evidence を見ていることを確認し、不足なら evaluator を起動する。
5. finish 前の branch、assignment、lease、export、PR readiness、sango runtime 状態を `dlc_handoff_writer` に記録させる。
6. commit、push、PR 作成、`ai-dlc root-export`、`ai-dlc overlay-cleanup` が必要で、かつ明示承認がある場合だけ `dlc_git_operator` を起動する。
7. child repo commit は child repo で行う。root-system overlay branch は push せず、root 側反映は `ai-dlc root-export` を使う。
8. PR 作成が必要な repo は child repo branch push と `gh pr create` 等の対象を repo ごとに分ける。root overlay branch の PR は作らない。
9. 承認不足なら summary-only handoff で止め、承認済み操作と最終疎通確認が完了したら `done` へ進める。

## Boundaries

- verifier と evaluator を飛ばして finish しない。
- `dlc_git_operator` 以外の role は finish-stage Git 操作を行わない。
- cleanup は approval boundary の外では行わない。
- `docs-then-impl` / `autonomous-impl` モードでは、dlc_git_operator 起動前のユーザー承認のみが必須。実装フェーズの中間確認は行わない。
- `git push`、destructive cleanup、root export commit は明示承認なしに進めない。
