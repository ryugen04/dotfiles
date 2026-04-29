# workflow-bootstrap

bootstrap と local readiness が未完了のときに使う。

## Controller Policy

- root session は controller-only のまま動く。
- bootstrap の実作業は `dlc_initializer`、local repair は `dlc_repairer` に委譲する。
- controller 自身は source を編集しない。

## Required Sequence

1. `ai-dlc inspect` と `ai-dlc validate-overlay` を実行して、bootstrap 不足なのか overlay 破損なのかを切り分ける。
2. initializer assignment を作成し、`dlc_initializer` を起動する。
3. initializer が `.local`、git controller、child `.git` pointer の破損を報告した場合だけ `dlc_repairer` を起動する。
4. repair report の後で `dlc_initializer` を再実行し、bootstrap readiness を更新する。
5. controller は initializer / repairer report を集約し、`bootstrap.status=ready` と active work item 条件を確認する。
6. readiness が曖昧、または再確認が必要なら `dlc_verifier` を起動して bootstrap evidence を残す。
7. `plan_ready`、`blocked`、`needs_decision` のいずれかに遷移する。

## Boundaries

- `dlc_evaluator` は通常不要だが、bootstrap 判定に独立レビューが必要なときだけ使う。
- `dlc_handoff_writer` は blocked または引き継ぎ記録が必要なときだけ使う。
- `dlc_git_operator` は bootstrap では使わない。
