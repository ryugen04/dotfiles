<!-- このテンプレートを新 plan にコピーして使う -->
---
status: draft                 # enum: draft|in_progress|ready|testing|done|archived (Phase 3-B 拡張後 `reviewing` 追加予定)
genre: <genre>                # enum: coding|bugfix|spike|refactoring|review|ui-verification|po-work
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
    scope: <scope>
review_process:
  mode: dual_parallel         # enum: dual_parallel|single|skip
  agents: [codex-implementer, pr-review-toolkit:code-reviewer]
  iteration_limit: 4
  stop_condition: "Critical/Major ゼロ、Minor のみ"
  applies_to: [each_phase_output]
learnings: []
---

# {Plan Title}

## Phase Dashboard

| Phase | 状態 | レビューiter | ユーザー承認 |
|---|---|---|---|
| Phase -1: plan 自体のレビュー | [ ] | iter-1 pending | pending |
| Phase 0: <name> | [ ] | - | - |
| Phase 1: <name> | [ ] | - | - |

### 現在地
- flow_status: **<frontmatter flow_status と同じ値>**
- 実施中: <現在の Phase 名>
- 次のアクション: <次に取るべきアクション>

## Context

## Workflow

## Team Composition

## Output Targets

## Review Process

## Phase 一覧
### Phase 0: <name>
- 作業内容:
- done_condition:
- next:

## チェックポイント
- [ ] Phase 状態記号は `[ ]` / `[~]` / `[r]` / `[x]` のみを使用
- [ ] ユーザー承認は `pending` / `approved` / `changes_requested` / `-` を使用
- [ ] 各 Phase の done_condition を満たす

## 検証方法

## リスク
| ID | リスク | 軽減策 |
|---|---|---|

## 除外事項

## 完了基準
- [ ] 全 Phase のチェックポイント達成
- [ ] learnings を更新
- [ ] レビュー停止条件を満たす
