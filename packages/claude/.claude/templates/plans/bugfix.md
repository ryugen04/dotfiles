<!-- このテンプレートを新 plan にコピーして使う -->
---
status: draft                 # enum: draft|in_progress|ready|testing|done|archived (Phase 3-B 拡張後 `reviewing` 追加予定)
genre: bugfix                # enum: coding|bugfix|spike|refactoring|review|ui-verification|po-work
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
    scope: 不具合修正範囲
review_process:
  mode: dual_parallel         # enum: dual_parallel|single|skip
  agents: [codex-implementer, pr-review-toolkit:code-reviewer]
  iteration_limit: 4
  stop_condition: "Critical/Major ゼロ、Minor のみ"
  applies_to: [each_phase_output]
learnings: []
---

# {Bugfix Plan Title}

## Phase Dashboard

| Phase | 状態 | レビューiter | ユーザー承認 |
|---|---|---|---|
| Phase -1: plan 自体のレビュー | [ ] | iter-1 pending | pending |
| Phase 0: 再現と原因分析 | [ ] | - | - |
| Phase 1: 修正実装 | [ ] | - | - |
| Phase 2: 再発防止確認 | [ ] | - | - |

### 現在地
- flow_status: **<frontmatter flow_status と同じ値>**
- 実施中: <現在の Phase 名>
- 次のアクション: <次に取るべきアクション>

## Context
- 現象:
- 影響範囲:
- 優先度:

## Workflow
- 再現手順を先に固定する
- Root Cause を特定してから修正に入る
- 再発防止策を同時に定義する

## Team Composition

## Output Targets

## Review Process

## Phase 一覧
### Phase 0: 再現と原因分析
- 作業内容: 再現手順、ログ/メトリクス確認、根本原因特定
- done_condition: Root Cause が 1 つに特定される
- next: Phase 1

### Phase 1: 修正実装
- 作業内容: 最小変更で修正実装
- done_condition: 再現手順で不具合が解消
- next: Phase 2

### Phase 2: 再発防止確認
- 作業内容: 回帰テスト追加、監視/アラート確認
- done_condition: 再発防止策が反映される
- next: 完了

## チェックポイント
- [ ] 再現手順が再現性を持つ
- [ ] Root Cause と修正の因果が説明可能
- [ ] 再発防止策が含まれる

## 検証方法
- 再現テスト:
- 修正確認:
- 回帰確認:

## リスク
| ID | リスク | 軽減策 |
|---|---|---|

## 除外事項

## 完了基準
- [ ] 不具合が再発しないことを確認
- [ ] 監視/テストの不足を補完
- [ ] learnings を更新
