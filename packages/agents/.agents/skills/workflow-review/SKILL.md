---
name: workflow-review
description: Use when progressing review, evidence collection, and handoff rather than implementation.
metadata:
  short-description: Review and handoff workflow
---

# workflow-review

実装ではなく review / evidence / handoff を進めるときに使う。

## Controller Policy

- root session は controller-only を維持する。
- controller は diff を見ても直接修正しない。
- 不足修正が必要なら `workflow-repair` または新しい implementation assignment に戻す。

## Required Sequence

1. `ai-dlc validate-overlay` と `ai-dlc overlay-status` を実行する。
2. root diff、child repo diff、assignment/report/evidence の連鎖を確認する。
3. verifier evidence が欠けている、または stale なら `dlc_verifier` を起動して証跡を更新する。
4. evidence がそろった後で、実装担当と独立した `dlc_evaluator` を起動する。
5. evaluator verdict、残課題、branch/export 状態を `dlc_handoff_writer` に記録させる。
6. `ready_to_finish`、`blocked`、`needs_decision`、または `executing` へ戻す判断を行う。

## Boundaries

- review 中に source 修正は行わない。修正が必要なら別 assignment に切り出す。
- `dlc_repo_worker` は review skill の既定フローには含めない。
- `dlc_git_operator` は review では使わない。
