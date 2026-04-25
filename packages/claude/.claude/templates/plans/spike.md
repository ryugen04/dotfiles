<!-- このテンプレートを新 plan にコピーして使う -->
---
status: draft                 # enum: draft|in_progress|ready|testing|done|archived (Phase 3-B 拡張後 `reviewing` 追加予定)
genre: spike                # enum: coding|bugfix|spike|refactoring|review|ui-verification|po-work
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
    scope: 調査成果物
review_process:
  mode: dual_parallel         # enum: dual_parallel|single|skip
  agents: [codex-implementer, pr-review-toolkit:code-reviewer]
  iteration_limit: 4
  stop_condition: "Critical/Major ゼロ、Minor のみ"
  applies_to: [each_phase_output]
learnings: []
---

# {Spike Plan Title}

## Phase Dashboard

| Phase | 状態 | レビューiter | ユーザー承認 |
|---|---|---|---|
| Phase -1: plan 自体のレビュー | [ ] | iter-1 pending | pending |
| Phase 0: 調査設計 | [ ] | - | - |
| Phase 1: 調査実施 | [ ] | - | - |
| Phase 2: 意思決定 | [ ] | - | - |

### 現在地
- flow_status: **<frontmatter flow_status と同じ値>**
- 実施中: <現在の Phase 名>
- 次のアクション: <次に取るべきアクション>

## Context

## Workflow
- Investigation Targets を先に明文化する
- Findings は事実と推測を分離して記録する
- 最終 Decision は採用/不採用理由を残す

## Team Composition

## Output Targets

## Review Process

## Phase 一覧
### Phase 0: 調査設計
- 作業内容: 調査範囲、制約、評価軸の定義
- done_condition: 調査質問が具体化される
- next: Phase 1

### Phase 1: 調査実施
- 作業内容: 検証・比較・結果整理
- done_condition: Findings が揃う
- next: Phase 2

### Phase 2: 意思決定
- 作業内容: 採用案決定、未解決課題整理
- done_condition: Decision と次アクションが確定
- next: 完了

## チェックポイント
- [ ] Investigation Targets が列挙されている
- [ ] Findings に根拠がある
- [ ] Decision の理由が記録されている

## 検証方法
- 調査手順:
- 比較軸:
- 判断基準:

## リスク
| ID | リスク | 軽減策 |
|---|---|---|

## 除外事項

## 完了基準
- [ ] 意思決定に必要な情報が揃う
- [ ] 不確実性と追加調査項目を明示
- [ ] learnings を更新
