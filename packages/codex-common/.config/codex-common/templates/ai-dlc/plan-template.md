---
id: YYYYMMDD-topic-slug
title: タイトル
status: draft
owner: codex
created_at: 2026-04-24T00:00:00+09:00
updated_at: 2026-04-24T00:00:00+09:00
related_issue:
active_branch:
task_size: small # small | medium | large
split_strategy:
gate_plan_review: required
gate_impl_requires_review: true
gate_close_requires_execution: true
metric_primary:
metric_secondary:
rollback_trigger:
rollback_owner: codex
artifacts:
  plan:
  research:
  review:
  execution:
  learnings:
---

# Title

## Context

- 背景
- 現状
- 参照ドキュメント

## 完了基準

- [ ] ユーザーに見える完了条件
- [ ] 技術的な完了条件
- [ ] 必須テストと確認

## Phase Checklist

### Phase 1: Investigation

- [ ] 必要な調査対象を列挙する（Owner: Codex）
- [ ] 影響範囲を確定する

### Phase 2: Plan Review

- [ ] `claude-plan-review` で review artifact を作成する
- [ ] 修正を反映し `status` を `approved` にする

### Phase 3: Implementation

- [ ] 実装する（review artifact が存在すること）
- [ ] 必要なテストを追加・更新する
- [ ] 最小限の検証を通す

### Phase 4: Final Review

- [ ] `claude-code-review` でサブレビューを行う
- [ ] execution artifact を残す

### Phase 5: Learnings

- [ ] 再発防止を設定へ昇格する
- [ ] feedback loop を close する

## Agent Assignment

| Phase | Owner | Support | Output |
| --- | --- | --- | --- |
| Investigation | Codex main | - | context notes |
| Plan Review | Claude CLI | - | review artifact |
| Implementation | Codex main | - | code changes |
| Final Review | Claude CLI | - | review notes |

## Review Loop

1. plan を作成する
2. plan review を反映する
3. 実装・検証する
4. execution/learnings を残して close する
