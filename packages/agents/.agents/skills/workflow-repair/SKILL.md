---
name: workflow-repair
description: Use when repairing local overlay, runtime, hook, sango state, nested submodule, or git pointer issues instead of source implementation changes.
metadata:
  short-description: Local repair workflow
---

# workflow-repair

overlay、`.local`、hook、git pointer などの local 問題を直すときに使う。

## Controller Policy

- root session は controller-only のまま `repairing` を管理する。
- 修復作業は `dlc_repairer` に委譲し、controller 自身は local runtime も直接いじらない。
- tracked source file は repair フローの対象外。

## Required Sequence

1. 現在地を分類する。task workspace でなければ root-system / sango worktree / IDE-created worktree のどれかを判定し、修復対象を限定する。
2. state を `repairing` に寄せ、`ai-dlc validate-overlay`、`ai-dlc overlay-status`、必要なら `sango status` で故障範囲を確認する。
3. repair assignment を作成し、`dlc_repairer` を起動する。
4. sango 登録、port offset、`.sango/worktrees.json`、symlink、`.git` pointer は既存差分を壊さず最小修復する。
5. nested submodule は top-level overlay repo と区別する。nested gitlink として扱い、top-level の overlay repo と混同しない。
6. hook が "AI-DLC workspace ではありません" を出す場合は、cwd が root-system なのか task workspace なのか、project-local `.codex/config.toml` の guardrails が効いているかを確認する。
7. repair report の後で `ai-dlc validate-overlay` と必要な健全性確認を再実行する。
8. 修復結果の再現確認が必要なら `dlc_verifier` を起動し、runtime / overlay evidence を残す。
9. 修復後の再開可否や残留リスクの独立判断が必要なら `dlc_evaluator` を起動する。
10. previous state に戻すか、`blocked` / `needs_decision` に遷移する。
11. 再開条件や未解決事項があれば `dlc_handoff_writer` に handoff を更新させる。

## Boundaries

- `dlc_repo_worker` は repair skill では起動しない。
- `dlc_git_operator` は repair では使わない。destructive cleanup は別途明示承認が必要。
