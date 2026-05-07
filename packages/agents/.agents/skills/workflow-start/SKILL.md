---
name: workflow-start
description: Use when starting or resuming an AI-DLC workflow from an AI-DLC task workspace, root-system, sango worktree, or IDE-created worktree, and coordinating initial controller actions with the 3-axis workflow model.
metadata:
  short-description: Start or resume workflow
---

# workflow-start

AI-DLC workflow の開始または再開で使う。開始地点は AI-DLC task workspace とは限らない。

## Controller Policy

- 現在の root session は controller-only。worker ではない。
- controller は tracked file を直接編集しない。
- 実装、テスト、env 修復、commit/export/cleanup は assignment を作って subagent に委譲する。
- Codex config/hooks/skills/subagents の編集は通常 source change と分け、`safety_domain=codex_config_edit` として扱う。

## Context Classification

1. まず `pwd` と親ディレクトリの `workspace.yaml` 有無で現在地を分類する。
2. `workspace.yaml` があれば task workspace として扱い、Required Sequence に進む。
3. `workspace.yaml` がなく `ai-dlc/project-metadata.yaml` または `sango.yaml` があれば root-system / control-plane にいる。`sango status`、`.sango/worktrees.json`、既存 `worktrees/**/workspace.yaml` から対象 task worktree を特定し、そこへ移動して再開する。
4. IDE などが先に worktree を作っていて `workspace.yaml` がない場合は、worktree を作り直さない。既存 child repo path を採用するため `workflow-bootstrap` に切り替える。
5. child repo 直下から始まった場合は、親の `workspace.yaml` または root-system を探す。見つからなければ通常 repo として扱い、AI-DLC 制約を推測で適用しない。

## Required Sequence

1. `workflow-classify` で `origin_mode`、`execution_intent`、`safety_domain` を判定する。
2. `workspace.yaml` を読み、`ai-dlc inspect`、`ai-dlc validate-overlay`、必要なら `ai-dlc validate` を実行する。
3. bootstrap 状態、WIP=1、active work item、plan/work-items の stale 状態を確認する。未初期化なら `workflow-bootstrap`、破損なら `workflow-repair` に切り替える。
4. `planning`: `dlc_plan_writer` に plan/decisions を完成させる。完了 report 後に `plan_ready` へ遷移する。
5. `plan_ready` / `assigning`: `dlc_scope_manager` に work-items、WIP=1、verifier/evaluator gate、assignment boundary を作らせる。
6. 必要なら planning/plan_ready/assigning 中に read-only の `dlc_explorer` を並列起動する。
7. active work item が 1 件だけ存在し、bootstrap が ready になったら `executing` へ遷移する。
8. `executing`: active repo assignment ごとに 1 つだけ `dlc_repo_worker` を起動する。controller は raw diff だけで前進しない。
9. repo worker report と release 後に `verifying` へ遷移し、`dlc_verifier` に verification evidence を作らせる。
10. verifier evidence 後に `evaluating` へ遷移し、repo worker と独立した `dlc_evaluator` を起動する。
11. evaluator verdict 後に `handoff_ready` へ遷移し、`dlc_handoff_writer` に handoff を更新させる。
12. handoff report 後に `ready_to_finish`、`blocked`、`needs_decision` のいずれかへ遷移する。

## Block Recovery

hook / permission / tool block を観測したら、最初の block で停止せず、以下の順で許可された復旧経路を探す。

1. `workflow-classify` で通常の 3 軸に加えて `block_type` を分類する。
2. block message、blocked command/tool、現在 phase、target root、workspace.yaml 有無を読み、許可された read-only 経路または assignment 経路を探す。
3. recovery route を 1 つ選ぶ: read-only retry、`workflow-bootstrap`、`workflow-repair`、正しい phase owner への assignment、approval request、または明示停止。
4. controller が直接編集・実装・修復する必要がある場合は、該当 phase の subagent に委譲する。phase owner が違う場合は先に `dlc_scope_manager` で assignment を直す。
5. `needs_assignment` かつ現在のユーザー依頼が既に実装/repair を許可している場合、ユーザー再確認には戻らない。assignment を作成して phase owner に即委譲する。
6. plan / decisions / work-items が不足または古い場合は `dlc_plan_writer` または `dlc_scope_manager` に作成・修復させる。
7. 復旧後は最小再現、関連 validation、実運用 path の順で確認し、block_type、選んだ route、残リスクを report に残す。

`approval_required` は非破壊コマンドだけ承認を求める。`destructive_forbidden` はユーザーの明示承認がない限り実行せず、代替の read-only 証跡を集める。`hook_schema_error` は `codex-hooks-authoring` と `codex-runtime-probing` に切り替えて、受け手の schema と active runtime を確認する。

## Phase Ownership

| Plan status | Owner | Required report/deliverable |
|---|---|---|
| `planning` | `dlc_plan_writer` | `plan_delta` |
| `plan_ready` | `dlc_scope_manager` | `work_items_delta` |
| `assigning` | `dlc_scope_manager` | `work_items_delta` |
| `executing` | `dlc_repo_worker` | `worker_report` |
| `verifying` | `dlc_verifier` | `evidence_ref` |
| `evaluating` | `dlc_evaluator` | `evaluator_verdict` |
| `handoff_ready` | `dlc_handoff_writer` | `handoff_ref` |
| `ready_to_finish` | `dlc_git_operator` | `git_result_ref` |

Assignment creation must match the owner for the current plan status. A mismatch requires an explicit break-glass decision and should normally transition through the correct phase instead.

## Boundaries

- verifier は同じ repo の active writer と重ねない。
- evaluator は実装した repo worker と論理的に独立させる。
- `dlc_git_operator` はここでは使わない。commit、push、root-export、overlay-cleanup は `workflow-finish` と明示承認が前提。
- 既定順序の skip または reorder は `ai-dlc/decisions/<issue>.md` に根拠を残した場合だけ許可する。
- root-system や sango root で hook が "task workspace ではない" と示すのは正常。実装を始める前に対象 task workspace へ移動するか、既存 worktree を `workflow-bootstrap` で採用する。

## Workflow Classification

着手前にユーザー指示文、現在地、変更対象から 3 軸を判定する。判定結果は
`${workspace_or_root}/ai-dlc/decisions/<issue>.md` の frontmatter に `workflow:` で記録する。

```yaml
workflow:
  origin_mode: new_workspace_from_plan | from_remote_ref | resume_existing_workspace | docs_only_no_workspace
  execution_intent: docs_only | plan_then_stop | docs_then_impl | autonomous_until_git_boundary
  safety_domain: source_change | codex_config_edit | docs_report | git_finish
```

旧 4 モードは `execution_intent` に対応する:

- `docs-only-pure` -> `docs_only` + `docs_only_no_workspace`
- `docs-only-with-future-impl` -> `plan_then_stop`
- `docs-then-impl` -> `docs_then_impl`
- `autonomous-impl` -> `autonomous_until_git_boundary`

## codex_config_edit Rules

- prompt marker `AI_DLC_SAFETY_DOMAIN=codex_config_edit` があれば、必ず `safety_domain=codex_config_edit`。
- `--profile codex-config-edit` は Codex config 側の runtime posture を選ぶために使う。
- `-c` は AI-DLC 独自 mode の主入力にしない。
- Codex hooks/config/skills/subagents を変更する前に、対応する Codex authoring skills を使う。
- hooks 設計または修正の plan には、実装前に hook event matrix を含める。
- high-risk な hook/config 挙動は、公式 docs、openai/codex source schema、local runtime probe の 3 点で確認する。

## Classification Behavior

- `docs_only`: `dlc_docs_writer` を起動し Required Sequence は実行しない。
- `plan_then_stop`: workflow-bootstrap 経由で worktree 作成後に plan を作成し、実装前にユーザー確認で停止する。
- `docs_then_impl`: plan 承認後に実装まで連続実行する。
- `autonomous_until_git_boundary`: plan 承認後に commit 直前まで無停止で進める。

- ExitPlanMode 後の中間ユーザー確認は行わない。`docs_then_impl` と `autonomous_until_git_boundary` では plan 承認 = impl 承認とみなす。
- 例外として `dlc_git_operator` の起動（commit / push / root-export / overlay-cleanup）は明示承認必須。
- plan に書いていないファイルを 3 つ以上変更しそうになったら自発停止し、ユーザーに状況報告する。
- `docs_only` かつ `origin_mode=docs_only_no_workspace` では sango worktree を作らず、root-system の `ai-dlc/docs/**` に直接書く。
