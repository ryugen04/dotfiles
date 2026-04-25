# 調査レポート・Plan のレビュールール（絶対遵守）
`code-review.md`（コードレビュー2エージェント）と本ルール（Plan/レポートのデュアルレビュー）は主題が異なる。

NO PLAN PRESENTATION WITHOUT CODEX CLI REVIEW
NO CHECKPOINT COMPLETION WITHOUT DUAL REVIEW

## Plan 提示前のレビュー

**ExitPlanMode を呼ぶ前に、Codex CLI でプランファイルをレビューすること。**

```
手順:
1. プランファイルを `.claude/plans/` に書き出す
2. codex-implementer エージェントにプランのレビューを依頼
3. レビュー指摘を反映
4. ExitPlanMode を呼ぶ
```

### レビュー観点（Plan）
- 要件の網羅性（スコープ漏れがないか）
- 作業順序の妥当性（依存関係が正しいか）
- チェックポイントの設定（各ステップに完了条件があるか）
- ユーザー操作ステップの明示（スクショ撮影、確認、判断ポイント）

## 各チェックポイントでのデュアルレビュー

調査レポートやドキュメントの各チェックポイントでは、以下の2つのレビューを必須とする。

### 1. Claude CLI レビュー（品質・網羅性）

```
レビュー観点:
- 図（Mermaid）の正確性・可読性
- コードブロックのファイルパス:行番号の正確性
- 説明の論理的整合性
- 抜け漏れの検出
```

### 2. Codex CLI レビュー（技術的正確性）

```
レビュー観点:
- コードブロック内の記述が実際のコードと一致しているか
- ファイルパス・行番号が現在の主幹ブランチ（例: develop / main）と一致しているか
- コールスタックの呼び出し順序が正しいか
- 型定義・引数の記述が正確か
```

### レビュー手順

```bash
# Step 1: Claude CLI レビュー（pr-review-toolkit:code-reviewer相当）
Task → general-purpose agent
  入力: レポートMDファイルのパス
  観点: 品質・網羅性

# Step 2: Codex CLI レビュー
Task → codex-implementer agent（/codex:review相当）
  入力: レポートMDファイルのパス + 参照先コードファイル群
  観点: 技術的正確性
```

## 適用タイミング

| タイミング | 必須レビュー |
|-----------|-------------|
| Plan策定完了時 | Codex CLI |
| 調査レポート各章完了時 | Claude CLI + Codex CLI |
| FigJam作成完了時 | Claude CLI（視覚的確認） |
| 最終統合時 | Claude CLI + Codex CLI |

## 違反時の対応

レビューなしで提示した場合:
1. 作業を中断
2. レビューを実施
3. 指摘を反映してから再提示

---

**最終更新**: 2026-03-24
**背景**: 調査レポートの品質・正確性を担保するため、デュアルレビューを必須化
