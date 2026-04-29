# workflow-start

AI-DLC workspace の開始または再開で使う。

## Controller Policy

- 現在の root session は controller-only。worker ではない。
- controller は tracked file を直接編集しない。
- 実装、テスト、env 修復、commit/export/cleanup は assignment を作って subagent に委譲する。

## Required Sequence

1. `workspace.yaml` を読み、`ai-dlc inspect`、`ai-dlc validate-overlay`、必要なら `ai-dlc validate` を実行する。
2. bootstrap 状態、WIP=1、active work item、plan/work-items の stale 状態を確認する。
3. 影響候補 repo ごとに read-only の `dlc_explorer` を並列起動する。
4. plan または current action が stale なら `dlc_plan_writer` を起動する。
5. work-items または verification gate が stale なら `dlc_scope_manager` を起動する。
6. work-items から assignment を作成し、active repo assignment ごとに 1 つだけ `dlc_repo_worker` を起動する。
7. controller は raw diff だけで前進せず、repo worker report を待つ。
8. repo worker report の後で `dlc_verifier` を起動し、verification evidence を作らせる。
9. verifier evidence の後で、repo worker と独立した `dlc_evaluator` を起動する。
10. reports と evidence がそろったら `dlc_handoff_writer` を起動する。
11. `ready_to_finish`、`blocked`、`needs_decision` のいずれかに遷移する。

## Boundaries

- verifier は同じ repo の active writer と重ねない。
- evaluator は実装した repo worker と論理的に独立させる。
- `dlc_git_operator` はここでは使わない。commit、push、root-export、overlay-cleanup は `workflow-finish` と明示承認が前提。
- 既定順序の skip または reorder は `ai-dlc/decisions/<issue>.md` に根拠を残した場合だけ許可する。
