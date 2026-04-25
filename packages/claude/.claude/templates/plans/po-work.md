<!-- このテンプレートを新 plan にコピーして使う -->
---
status: draft                 # enum: draft|in_progress|ready|testing|done|archived (Phase 3-B 拡張後 `reviewing` 追加予定)
genre: po-work                # enum: coding|bugfix|spike|refactoring|review|ui-verification|po-work
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
    scope: PO 作業成果物
review_process:
  mode: dual_parallel         # enum: dual_parallel|single|skip
  agents: [codex-implementer, pr-review-toolkit:code-reviewer]
  iteration_limit: 4
  stop_condition: "Critical/Major ゼロ、Minor のみ"
  applies_to: [each_phase_output]
learnings: []
---

# {PO Work Plan Title}

## Phase Dashboard

| Phase | 状態 | レビューiter | ユーザー承認 |
|---|---|---|---|
| Phase -1: plan 自体のレビュー | [ ] | iter-1 pending | pending |
| Phase 0: 依頼整理 | [ ] | - | - |
| Phase 1: 更新作業 | [ ] | - | - |
| Phase 2: 共有とクローズ | [ ] | - | - |

### 現在地
- flow_status: **<frontmatter flow_status と同じ値>**
- 実施中: <現在の Phase 名>
- 次のアクション: <次に取るべきアクション>

## Context

## Workflow
- Stakeholders を先に定義
- Linear / Notion の更新対象を明確化
- 更新後の通知・合意まで含める

## Team Composition

## Output Targets

## Review Process

## Phase 一覧
### Phase 0: 依頼整理
- 作業内容: 要件・優先度・関係者整理
- done_condition: 更新方針が合意される
- next: Phase 1

### Phase 1: 更新作業
- 作業内容: Linear / Notion の更新実施
- done_condition: 更新が完了し差分確認済み
- next: Phase 2

### Phase 2: 共有とクローズ
- 作業内容: 関係者共有、承認取得、残課題整理
- done_condition: クローズ条件を満たす
- next: 完了

## チェックポイント
- [ ] Stakeholders が定義されている
- [ ] Linear / Notion 更新対象が明記されている
- [ ] 共有先と承認フローが定義されている

## 検証方法
- 更新内容確認:
- リンク確認:
- 承認確認:

## リスク
| ID | リスク | 軽減策 |
|---|---|---|

## 除外事項

## 完了基準
- [ ] 更新内容が関係者に共有済み
- [ ] 承認または次アクションが確定
- [ ] learnings を更新
