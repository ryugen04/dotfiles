---
name: workflow-start
description: Use when starting or resuming an AI-DLC workspace and coordinating initial controller actions.
metadata:
  short-description: Start or resume workflow
---

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

## Mode Classification

着手前にユーザー指示文と現在地から、以下 4 モードを判定する。判定結果は
`${workspace_or_root}/ai-dlc/decisions/<issue>.md` の frontmatter に `mode:` で記録する。

- `docs-only-pure`: 調査専用。`ai-dlc/docs/**` へ出力し、worktree は作らない。
- `docs-only-with-future-impl`: 調査中心 + 将来実装あり。plan 作成後に継続確認。
- `docs-then-impl`: ExitPlanMode 承認後に実装まで連続実行。
- `autonomous-impl`: ExitPlanMode 承認後に commit 直前まで無停止。

判定後の挙動:
- `docs-only-pure`: `dlc_docs_writer` を起動し Required Sequence は実行しない。
- `docs-only-with-future-impl`: workflow-bootstrap 経由で worktree 作成後に plan を作成。
- `docs-then-impl` / `autonomous-impl`: workflow-bootstrap → Required Sequence を連続実行。

- ExitPlanMode 後の中間ユーザー確認は行わない。`docs-then-impl` と `autonomous-impl` では plan 承認 = impl 承認とみなす。
- 例外として `dlc_git_operator` の起動（commit / push / root-export / overlay-cleanup）は明示承認必須。
- plan に書いていないファイルを 3 つ以上変更しそうになったら自発停止し、ユーザーに状況報告する。
- `docs-only-pure` モードでは sango worktree を作らず、root-system の `ai-dlc/docs/**` に直接書く。
