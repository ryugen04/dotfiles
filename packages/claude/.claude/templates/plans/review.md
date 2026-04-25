<!-- このテンプレートを新 plan にコピーして使う -->
---
status: draft                 # enum: draft|in_progress|ready|testing|done|archived (Phase 3-B 拡張後 `reviewing` 追加予定)
genre: review                # enum: coding|bugfix|spike|refactoring|review|ui-verification|po-work
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
    scope: レビュー対象差分
review_process:
  mode: dual_parallel         # enum: dual_parallel|single|skip
  agents: [codex-implementer, pr-review-toolkit:code-reviewer]
  iteration_limit: 4
  stop_condition: "Critical/Major ゼロ、Minor のみ"
  applies_to: [each_phase_output]
learnings: []
---

# {Review Plan Title}

## Phase Dashboard

| Phase | 状態 | レビューiter | ユーザー承認 |
|---|---|---|---|
| Phase -1: plan 自体のレビュー | [ ] | iter-1 pending | pending |
| Phase 0: レビュー設計 | [ ] | - | - |
| Phase 1: 並列レビュー実施 | [ ] | - | - |
| Phase 2: 指摘収束 | [ ] | - | - |

### 現在地
- flow_status: **<frontmatter flow_status と同じ値>**
- 実施中: <現在の Phase 名>
- 次のアクション: <次に取るべきアクション>

## Context

## Workflow
- Review Scope を固定してから実行
- Checklist を先に合意
- 重大度で収束条件を管理

## Team Composition
- 標準 12 エージェント構成（実在するものは実名、カスタム枠は `<...>` で表記）:
- `pr-review-toolkit:code-reviewer` (pr-review-toolkit プラグイン、実在)
- `codex-implementer` (dotfiles agents/code/、実在)
- `ui-verifier` (custom project agents/、任意)
- `Explore` (Claude Code 組み込み、実在)
- `Plan` (Claude Code 組み込み、実在)
- `general-purpose` (Claude Code 組み込み、実在)
- `<custom-reviewer-01-security>` ← プロジェクト固有に定義（現時点で未実装、`.claude/agents/` に追加してから使用）
- `<custom-reviewer-02-performance>` ← 同上
- `<custom-reviewer-03-test-coverage>` ← 同上
- `<custom-reviewer-04-architecture>` ← 同上
- `<custom-reviewer-05-data-integrity>` ← 同上
- `<custom-reviewer-06-observability>` ← 同上

**注意**: `<...>` で囲まれたエージェントは現時点で実在しない。実際に `/code:review-*` コマンドで起動する前に `.claude/agents/` 配下に定義を追加すること。`skills/review/SKILL.md` で定義される場合はそちらを参照。

## Output Targets

## Review Process
- dual_parallel を基本とし、必要に応じて 12 エージェントへ拡張
- 各 iter で Critical/Major/Minor を再分類

## Phase 一覧
### Phase 0: レビュー設計
- 作業内容: 対象差分、観点、重大度基準の確定
- done_condition: Review Scope と Checklist が固定
- next: Phase 1

### Phase 1: 並列レビュー実施
- 作業内容: 複数エージェントで並列レビュー
- done_condition: 指摘一覧の統合が完了
- next: Phase 2

### Phase 2: 指摘収束
- 作業内容: 修正と再レビューの反復
- done_condition: 停止条件を満たす
- next: 完了

## チェックポイント
- [ ] Review Scope が明確
- [ ] Checklist が合意済み
- [ ] 重大度分類が一貫している

## 検証方法
- 差分レビュー:
- テストレビュー:
- リスクレビュー:

## リスク
| ID | リスク | 軽減策 |
|---|---|---|

## 除外事項

## 完了基準
- [ ] Critical/Major が解消
- [ ] 残件が許容 Minor のみ
- [ ] learnings を更新
