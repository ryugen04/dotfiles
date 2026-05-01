---
name: workflow-review
description: Use when progressing review, runtime connectivity evidence, evaluator review, and handoff rather than implementation.
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

1. 現在地が task workspace であることを確認する。root-system や sango root なら対象 `workspace.yaml` のある worktree に移動する。
2. `ai-dlc validate-overlay`、`ai-dlc overlay-status`、必要なら `ai-dlc validate` を実行する。
3. root diff、child repo diff、assignment/report/evidence の連鎖を確認する。
4. runtime 疎通が要件なら `sango status`、`sango up --profile ...`、再度 `sango status` を verification 対象に含める。
5. verifier evidence が欠けている、または stale なら `dlc_verifier` を起動して overlay、test、runtime connectivity の証跡を更新する。
6. evidence がそろった後で、実装担当と独立した `dlc_evaluator` を起動する。
7. evaluator verdict、残課題、branch/export/PR readiness、疎通確認結果を `dlc_handoff_writer` に記録させる。
8. `ready_to_finish`、`blocked`、`needs_decision`、または `executing` へ戻す判断を行う。

## Boundaries

- review 中に source 修正は行わない。修正が必要なら別 assignment に切り出す。
- `dlc_repo_worker` は review skill の既定フローには含めない。
- `dlc_git_operator` は review では使わない。
