# Plan駆動ワークフロー（絶対遵守）

NO IMPLEMENTATION WITHOUT APPROVED PLAN
NO PLAN WITHOUT WORKFLOW DEFINITION

## ワークフロー

1. **ドキュメント確認**: プロジェクトのドキュメントディレクトリ（例: `.claude/docs/reference/domain/`）で関連設計書を検索
2. **Plan策定**: プランファイルを作成（`.claude/plans/YYYYMMDD-{genre}-{name}.md`。テンプレートは `~/.claude/templates/plans/{genre}.md`）
3. **Workflow定義**: genre に応じたワークフローテンプレート（プロジェクトの `.claude/workflows/` または `~/.claude/templates/plans/` 等）を参照し、## Workflow セクションに記述
4. **完了基準作成**: 機能要件・技術要件・検証方法・除外事項
5. **ユーザーレビュー**: ExitPlanMode で承認を得る
6. **実装開始**: Workflowに沿って実行

> AI-DLC `docs-then-impl` / `autonomous-impl` モードでは、ExitPlanMode 承認 = impl 承認とみなす。
> 承認後は commit/push 直前まで中間確認なし。scope を超えた変更が必要になった時のみ自発停止する。

## プランファイル必須項目

| 項目 | 内容 |
|------|------|
| フロントマター | status, genre, branch, created, updated, learnings |
| 機能要件 | 実装すべき振る舞い（Gherkin推奨） |
| 技術要件 | 変更対象ファイル、影響範囲 |
| 検証方法 | ビルド確認、テスト実行、UI検証の手順 |
| 除外事項 | このプランでやらないこと |
| Workflow | 各ステップの agent / done_condition / next |

## 情報アーキテクチャ（3層）

| Layer | ソース | 内容 |
|-------|--------|------|
| 1. Issue | チケット管理（例: Linear / Notion / Jira / GitHub Issues） | 要件、受入基準、影響範囲 |
| 2. コードベース | CLAUDE.md, rules/, docs/ | ルール、ドメイン設計、リポジトリガイド |
| 3. 自動取得 | AI実行時 | ディレクトリ構造、依存関係、既存パターン |

## ドキュメント参照（必須）

タスク着手前にプロジェクトのドキュメントディレクトリ（例: `.claude/docs/reference/domain/`）を検索。
サブエージェント委託時は関連ドキュメントのパスを明示的に指定。

## DoR（着手前チェック）

- [ ] 要件が明確か（Gherkin AC推奨）
- [ ] 影響範囲が特定できるか
- [ ] 関連ドキュメントを確認したか

## 合理化対策

| 言い訳 | 反論 |
|--------|------|
| "小さな修正だから" | 小さな修正が膨らんで手戻りした回数を思い出せ |
| "もう何をすべきか分かっている" | 分かっているなら5分でプランが書ける |
| "Workflow不要" | 形式がないから品質が不安定なのだ |
| "前回と同じ" | コピーしろ。ただし done_condition は更新しろ |

## Red Flags -- STOP and Start Over

以下の状態になったら作業を中断し、プランを見直す:
- 想定外のファイルを3つ以上変更している
- プランに書いていないスコープに手を出している
- ビルドエラーをコード削除で回避しようとしている

---

**最終更新**: 2026-03-20
