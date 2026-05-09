---
name: workflow-bootstrap
description: Use when AI-DLC bootstrap or local readiness is incomplete, including new root-system setup, sango worktree creation, adoption of IDE-created worktrees, and overlay initialization or repair.
metadata:
  short-description: Bootstrap readiness workflow
---

# workflow-bootstrap

bootstrap と local readiness が未完了のときに使う。AI-DLC task workspace がまだ存在しない状態も含む。

## Controller Policy

- root session は controller-only のまま動く。
- bootstrap の実作業は `dlc_initializer`、local repair は `dlc_repairer` に委譲する。
- controller 自身は source を編集しない。
- task workspace 作成前の user-level install、root-system 初期化、sango worktree 作成・採用、`ai-dlc init-workspace` は controller の bootstrap 操作として扱う。
- workspace-less bootstrap/recovery assignment は `dlc_initializer` と `dlc_repairer` に限定する。
- assignment 作成や owner 起動が block された場合は `bootstrap/delegation deadlock` として停止し、`docs/codex/block-delegation-policy-matrix.md` に沿った恒久修正 plan を提示する。

## Bootstrap Modes

- `new-root-system`: dotfiles install、`ai-dlc install/doctor`、root-system `git init`、`ai-dlc init-project`、sango bootstrap/doctor まで行う。
- `sango-create`: sango が child repo の物理 worktree と port offset を作る。AI-DLC はその path を `--repo key=path` で採用するだけにする。
- `adopt-existing`: IDE などが先に worktree を作成済みのとき。worktree を作り直さず、既存 root/child repo path、branch、base ref を確認して `ai-dlc init-workspace` する。
- `repair-readiness`: `workspace.yaml` はあるが overlay、`.local`、hook、git pointer、runtime readiness が壊れているとき。必要に応じて `workflow-repair` に切り替える。

## Sango + AI-DLC Rules

- physical child worktree 作成は sango に一本化する。AI-DLC bootstrap で別名ディレクトリを新規作成しない。
- repo key は実ディレクトリ名に合わせる。
- base branch は各リポジトリの慣習に従う（`develop`, `main`, `master` 等）。リポジトリごとに異なる場合がある。
- sango の `.sango/worktrees.json` は task worktree、offset、`from_branch`、services の一次情報として確認する。既存登録がある場合は破壊せず採用する。
- `ai-dlc init-workspace` は sango worktree 内で実行し、`--root-canonical-path` は root-system canonical path、`--repo` は sango が作った実 path を渡す。

## Required Sequence

1. 現在地を分類する。`workspace.yaml` がなければ root-system、sango root、既存 worktree、child repo のどれかを判定する。
2. user-level install が疑わしい場合だけ dotfiles 更新、`ai-dlc install`、`ai-dlc doctor` を確認する。
3. plan-driven に進める通常 repo で `workspace.yaml` / `ai-dlc/project-metadata.yaml` がまだない場合は、source 編集前に project-local `.codex/config.toml` を作成し、`[features].codex_hooks = true` と `[guardrails].subagent_required = true` を設定する。bootstrap 中に controller が直接編集してよい path は `.codex/config.toml`、`.codex/plans/**`、`AGENTS.md` など初期構築に限る。
4. root-system が未初期化なら `ai-dlc init-project` と sango bootstrap/doctor を行う。
5. task worktree がなければ `sango worktree create` で作る。既存 worktree があるなら作り直さず採用する。
6. task worktree root が git repo でない場合は初期 commit を作り、child repo の branch/base ref を確認する。
7. `ai-dlc init-workspace` を実行する。repo key/path と repo base ref を実 child repo に一致させる。
8. `ai-dlc validate-overlay`、`ai-dlc bootstrap`、`ai-dlc overlay-status`、必要なら `ai-dlc validate` を実行する。
9. initializer assignment を作成し、`dlc_initializer` を起動する。既に bootstrap 済みなら evidence 更新だけにする。
10. initializer が `.local`、git controller、child `.git` pointer、nested submodule、sango state の破損を報告した場合だけ `dlc_repairer` を起動する。
11. repair report の後で readiness コマンドを再実行し、`bootstrap.status=ready` と active work item 条件を確認する。
12. readiness が曖昧、または再確認が必要なら `dlc_verifier` を起動して bootstrap evidence を残す。
13. `plan_ready`、`blocked`、`needs_decision` のいずれかに遷移する。

## Boundaries

- `dlc_evaluator` は通常不要だが、bootstrap 判定に独立レビューが必要なときだけ使う。
- `dlc_handoff_writer` は blocked または引き継ぎ記録が必要なときだけ使う。
- `dlc_git_operator` は bootstrap では使わない。
- `git reset --hard`、`git clean`、`git worktree remove`、既存 worktree の削除は bootstrap でも使わない。
- `git worktree list` は read-only、`git worktree add` は mutating として扱う。
- `needs_assignment` / `delegate_phase_owner` を受けたら bootstrap path や escalation を広げず、assignment / subagent / deadlock report のいずれかに限定する。

## Sango + AI-DLC Rules

- `sango worktree create / list / status` は controller / dlc_initializer 双方が直接実行できる。
- `sango worktree remove` は destructive 扱い。明示承認のもと dlc_git_operator または手動操作で実行する。

> `docs-then-impl` / `autonomous-impl` モードでは、ExitPlanMode 承認後は step を連続実行し、`blocked` / `needs_decision` 時のみ差し戻す。
