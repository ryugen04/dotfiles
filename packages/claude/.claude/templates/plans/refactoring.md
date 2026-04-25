<!-- このテンプレートを新 plan にコピーして使う -->
---
status: draft                 # enum: draft|in_progress|ready|testing|done|archived (Phase 3-B 拡張後 `reviewing` 追加予定)
genre: refactoring                # enum: coding|bugfix|spike|refactoring|review|ui-verification|po-work
flow_status: planning         # enum: discovery|planning|implementing|reviewing|verifying|done
branch: {username}/{name}
created: YYYY-MM-DD
updated: YYYY-MM-DD
team:
  orchestrator: main
  implementers: [codex-implementer]
  reviewers: [codex-implementer, pr-review-toolkit:code-reviewer]
  verifiers: []
output_targets:
  - path: <path>
    scope: リファクタリング範囲
review_process:
  mode: dual_parallel         # enum: dual_parallel|single|skip
  agents: [codex-implementer, pr-review-toolkit:code-reviewer]
  iteration_limit: 4
  stop_condition: "Critical/Major ゼロ、Minor のみ"
  applies_to: [each_phase_output]
learnings: []
---

# {Refactoring Plan Title}

## Phase Dashboard

| Phase | 状態 | レビューiter | ユーザー承認 |
|---|---|---|---|
| Phase -1: plan 自体のレビュー | [ ] | iter-1 pending | pending |
| Phase 0: スコープ固定 | [ ] | - | - |
| Phase 1: 構造改善 | [ ] | - | - |
| Phase 2: 回帰確認 | [ ] | - | - |

### 現在地
- flow_status: **<frontmatter flow_status と同じ値>**
- 実施中: <現在の Phase 名>
- 次のアクション: <次に取るべきアクション>

## Context

## Workflow
- Scope を厳密に限定する
- Before-After を説明できる差分にする
- 挙動保持を最優先し Regression Risk を管理する

## Team Composition

## Output Targets

## Review Process

## Phase 一覧
### Phase 0: スコープ固定
- 作業内容: 対象モジュールと非対象を確定
- done_condition: スコープ外変更が発生しない状態
- next: Phase 1

### Phase 1: 構造改善
- 作業内容: 命名/分割/依存整理
- done_condition: 可読性・保守性が改善
- next: Phase 2

### Phase 2: 回帰確認
- 作業内容: Before-After 比較、テスト、性能確認
- done_condition: 挙動保持が確認される
- next: 完了

## チェックポイント
- [ ] Scope が明確
- [ ] Before-After の説明がある
- [ ] Regression Risk 対策がある

## 検証方法
- 既存テスト:
- 追加確認:
- 性能比較:

## リスク
| ID | リスク | 軽減策 |
|---|---|---|

## 除外事項

## 完了基準
- [ ] 挙動を維持したまま構造改善
- [ ] 回帰なし
- [ ] learnings を更新
