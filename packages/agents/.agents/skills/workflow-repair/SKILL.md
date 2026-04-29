---
name: workflow-repair
description: Use when repairing local overlay, runtime, hook, or git pointer issues instead of source implementation changes.
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

1. state を `repairing` に寄せ、`ai-dlc validate-overlay` で故障範囲を確認する。
2. repair assignment を作成し、`dlc_repairer` を起動する。
3. repair report の後で `ai-dlc validate-overlay` と必要な健全性確認を再実行する。
4. 修復結果の再現確認が必要なら `dlc_verifier` を起動し、runtime / overlay evidence を残す。
5. 修復後の再開可否や残留リスクの独立判断が必要なら `dlc_evaluator` を起動する。
6. previous state に戻すか、`blocked` / `needs_decision` に遷移する。
7. 再開条件や未解決事項があれば `dlc_handoff_writer` に handoff を更新させる。

## Boundaries

- `dlc_repo_worker` は repair skill では起動しない。
- `dlc_git_operator` は repair では使わない。destructive cleanup は別途明示承認が必要。
