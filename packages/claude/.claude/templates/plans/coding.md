<!-- このテンプレートを新 plan にコピーして使う -->
---
status: draft                 # enum: draft|in_progress|ready|testing|done|archived (Phase 3-B 拡張後 `reviewing` 追加予定)
genre: coding                # enum: coding|bugfix|spike|refactoring|review|ui-verification|po-work
flow_status: planning         # enum: discovery|planning|implementing|reviewing|verifying|done
branch: {username}/{name}
created: YYYY-MM-DD
updated: YYYY-MM-DD
team:
  orchestrator: main
  implementers: [codex-implementer]
  reviewers: [codex-implementer, pr-review-toolkit:code-reviewer]
  verifiers: [ui-verifier]
output_targets:
  - path: <path>
    scope: 新機能実装範囲
review_process:
  mode: dual_parallel         # enum: dual_parallel|single|skip
  agents: [codex-implementer, pr-review-toolkit:code-reviewer]
  iteration_limit: 4
  stop_condition: "Critical/Major ゼロ、Minor のみ"
  applies_to: [each_phase_output]
learnings: []
---

# {Coding Plan Title}

## Phase Dashboard

| Phase | 状態 | レビューiter | ユーザー承認 |
|---|---|---|---|
| Phase -1: plan 自体のレビュー | [ ] | iter-1 pending | pending |
| Phase 0: 実装準備 | [ ] | - | - |
| Phase 1: 実装 | [ ] | - | - |
| Phase 2: テストと仕上げ | [ ] | - | - |

### 現在地
- flow_status: **<frontmatter flow_status と同じ値>**
- 実施中: <現在の Phase 名>
- 次のアクション: <次に取るべきアクション>

## Context

## Workflow
- 新規実装の手順を明記する
- 実装前に API/型/データ影響を確定する
- 失敗時のロールバック手順を記載する

## Team Composition

## Output Targets

## Review Process
- 実装ごとに dual_parallel レビューを実施
- 変更量が大きい場合は Phase を分割して逐次レビュー

## Phase 一覧
### Phase 0: 実装準備
- 作業内容: 要件確定、影響範囲調査、設計
- done_condition: 実装方針とテスト戦略が確定
- next: Phase 1

### Phase 1: 実装
- 作業内容: 機能追加、必要な関連修正
- done_condition: 仕様通りに動作
- next: Phase 2

### Phase 2: テストと仕上げ
- 作業内容: テスト、lint、最終レビュー
- done_condition: 回帰なし、レビュー停止条件達成
- next: 完了

## チェックポイント
- [ ] 実装手順が具体化されている
- [ ] テスト戦略（単体/結合/E2E）を定義
- [ ] 状態記号・承認 enum を遵守

## 検証方法
- 単体テスト:
- 結合テスト:
- 目視確認:

## リスク
| ID | リスク | 軽減策 |
|---|---|---|

## 除外事項

## 完了基準
- [ ] 新機能が受け入れ条件を満たす
- [ ] 回帰テストが成功
- [ ] learnings を更新
