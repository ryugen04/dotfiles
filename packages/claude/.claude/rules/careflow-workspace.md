# Careflow Workspace Rule（絶対遵守）

NO NON-TRIVIAL EXECUTION WITHOUT CAREFLOW CONTEXT
NO CROSS-AGENT HANDOFF WITHOUT ORDER AND RESULT PATH

## 目的

Claude から Codex / Claude subagent / Cursor / 外部CLIへ作業を渡す時、
`.careflow` を配置場所・連携場所・完了判定場所の正本にする。

`.claude/plans` や `.claude/work` は Claude ローカルの補助領域であり、
非自明な実装・レビュー・調査・複数agent連携の正本ではない。

## 必須ストレージ

| 種類 | 正本 |
|---|---|
| Case | `.careflow/cases/<case_id>/CASE.yaml` |
| Plan | `.careflow/cases/<case_id>/PLAN.md` |
| Order / Subplan | `.careflow/cases/<case_id>/orders/<order_id>.order.md` |
| Result | `.careflow/cases/<case_id>/results/<order_id>.result.md` |
| Evidence | `.careflow/cases/<case_id>/evidence/` |
| Review / Incident | `.careflow/cases/<case_id>/reviews/`, `.careflow/cases/<case_id>/incidents/` |

## Workspace / Worktree 配置

- workspace-henry のような polyrepo でも、単一 repo でも、`.careflow` は workspace 共有 store を指す。
- worktree root に `.careflow` の実体をコピーしない。`.worktrees/.../.careflow` は共有 store への symlink が原則。
- case/order/result/evidence は共有する。`active_case` / `active_order` は worktree/session scope で扱う。
- `.careflow` が見つからない場合は、実装に入る前に bootstrap または user確認を行う。

## 実装前ゲート

以下のいずれかに当てはまる作業は、実装・レビュー承認・完了報告の前に careflow context を必須にする。

- 3ファイル以上に触れる可能性がある
- Codex / Claude subagent / Cursor へ委託する
- 調査、レビュー、検証、CI修正、リリース、設定変更
- workspace / worktree / polyrepo をまたぐ
- 後で証跡が必要になる可能性がある

必須確認:

```bash
agent-careflow workspace
agent-careflow order status --case <case_id> --order <order_id>
```

context がない場合は、実装せずに case / plan / order を作る。

```bash
agent-careflow case new --title "<title>" --risk C2
agent-careflow hash plan --case <case_id> --write-lock
agent-careflow order issue --case <case_id> --order ORD-001 --role implementer
agent-careflow order result-skeleton --case <case_id> --order ORD-001 --status in_progress --write
```

## Handoff Header

Claude から Codex / Claude subagent / Cursor に渡す時は、説明文より前に必ずこの固定ヘッダを置く。

```text
PLAN_FILE: .careflow/cases/<case_id>/PLAN.md
ORDER_FILE: .careflow/cases/<case_id>/orders/<order_id>.order.md
SUBPLAN_FILE: .careflow/cases/<case_id>/orders/<order_id>.order.md
EXPECTED_RESULT_PATH: .careflow/cases/<case_id>/results/<order_id>.result.md
CASE_ID: <case_id>
ORDER_ID: <order_id>
ASSIGNED_ROLE: <researcher|implementer|verifier|reviewer|incident-commander>
TARGET_TOOL: <codex|claude|cursor>
```

ORDER が委託先の subplan。chat要約だけで委託しない。

## Result / Evidence

- 委託先は `EXPECTED_RESULT_PATH` を書くまで完了扱いしない。
- 検証ログ、調査ソース、git status、失敗理由は `.careflow/cases/<case_id>/evidence/` に残す。
- `.claude/work` に中間メモを置いてもよいが、最終result/evidenceは `.careflow` に転記する。

## Red Flags -- STOP

- `.claude/plans` だけで実装に入ろうとしている
- Codexにplan本文だけ渡し、ORDER/RESULTを渡していない
- subagentに「調べて」だけ渡し、expected result pathを渡していない
- worktree内に独立した `.careflow` directory を作ろうとしている
- `.careflow/state.json` の global active だけを信じて、worktree scope を確認していない

---

**最終更新**: 2026-06-17
