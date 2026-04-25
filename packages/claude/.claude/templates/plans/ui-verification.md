<!-- このテンプレートを新 plan にコピーして使う -->
---
status: draft                 # enum: draft|in_progress|ready|testing|done|archived (Phase 3-B 拡張後 `reviewing` 追加予定)
genre: ui-verification                # enum: coding|bugfix|spike|refactoring|review|ui-verification|po-work
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
    scope: UI 検証対象
review_process:
  mode: dual_parallel         # enum: dual_parallel|single|skip
  agents: [codex-implementer, pr-review-toolkit:code-reviewer]
  iteration_limit: 4
  stop_condition: "Critical/Major ゼロ、Minor のみ"
  applies_to: [each_phase_output]
learnings: []
---

# {UI Verification Plan Title}

## Phase Dashboard

| Phase | 状態 | レビューiter | ユーザー承認 |
|---|---|---|---|
| Phase -1: plan 自体のレビュー | [ ] | iter-1 pending | pending |
| Phase 0: 検証設計 | [ ] | - | - |
| Phase 1: UI 検証実行 | [ ] | - | - |
| Phase 2: 結果反映 | [ ] | - | - |

### 現在地
- flow_status: **<frontmatter flow_status と同じ値>**
- 実施中: <現在の Phase 名>
- 次のアクション: <次に取るべきアクション>

## Context

## Workflow
- UI Flow Reference を先に確定
- Playwright Steps で再現可能な検証手順を作成
- 期待値と実測差分を記録

## Team Composition

## Output Targets

## Review Process

## Phase 一覧
### Phase 0: 検証設計
- 作業内容: 画面遷移・検証観点・期待値の定義
- done_condition: UI Flow と操作手順が確定
- next: Phase 1

### Phase 1: UI 検証実行
- 作業内容: 手動/自動検証、証跡収集
- done_condition: 主要フローの結果が揃う
- next: Phase 2

### Phase 2: 結果反映
- 作業内容: 指摘整理、修正依頼、再検証
- done_condition: 重大な UI 問題が解消
- next: 完了

## チェックポイント
- [ ] UI Flow Reference が明記されている
- [ ] Playwright Steps が再実行可能
- [ ] 証跡（動画/スクショ/ログ）が紐付く

## 検証方法
- 対象ブラウザ:
- Playwright Steps:
- 期待結果:

## リスク
| ID | リスク | 軽減策 |
|---|---|---|

## 除外事項

## 完了基準
- [ ] 主要 UI フローが期待通り
- [ ] 重大 UI 問題なし
- [ ] learnings を更新
