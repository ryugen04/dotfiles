---
name: workflow-finish
description: AI-DLC セッションを終了可能な状態へまとめ、承認済みの Git 操作に進む controller 向けワークフロー。
---

# workflow-finish

AI-DLC セッションを終了可能な状態へまとめ、承認済みの Git 操作だけを進めるときに使う。

## Controller Policy

- root session は finish 段階でも controller-only。
- controller は child repo commit/push、root-export、overlay-cleanup を直接実行しない。
- finish 段階の Git 操作は明示承認のある `dlc_git_operator` だけが担当する。

## Required Sequence

1. `ai-dlc clean-state-check` を実行し、assignment、lease、report、diff の取り残しを確認する。
2. 最新の `dlc_verifier` evidence が存在することを確認し、足りなければ verifier を先に起動する。
3. 独立した `dlc_evaluator` verdict が最新 evidence を見ていることを確認し、不足なら evaluator を起動する。
4. finish 前の branch、assignment、lease、export 状態を `dlc_handoff_writer` に記録させる。
5. commit、push、`ai-dlc root-export`、`ai-dlc overlay-cleanup` が必要で、かつ明示承認がある場合だけ `dlc_git_operator` を起動する。
6. 承認不足なら summary-only handoff で止め、承認済み操作が完了したら `done` へ進める。

## Boundaries

- verifier と evaluator を飛ばして finish しない。
- `dlc_git_operator` 以外の role は finish-stage Git 操作を行わない。
- cleanup は approval boundary の外では行わない。
