---
description: Codex CLIを使用して実装計画をレビュー・改善
argument-hint: PLAN=<plan-file-path>
allowed-tools: Bash, Read, Write, Glob
---

# /codex:plan - Codex CLI 実装計画レビュー

Codex CLIを使用して、実装計画の妥当性をレビューし改善提案を行います。

## 引数

- `PLAN`: レビュー対象の計画ファイルパス（必須）

## 実行手順

### 1. 計画ファイルの読み込み

```bash
# 計画ファイルの存在確認
ls -la $PLAN
```

計画ファイルを読み込み、内容を把握。

### 2. Codex CLI で計画レビュー

```bash
codex exec "以下の実装計画をレビューしてください:
- 技術的な実現可能性
- リスクと対策の妥当性
- 見落としている観点
- より良いアプローチの提案

計画ファイル: $PLAN" --full-auto --sandbox read-only
```

### 3. 関連コードの確認

計画で言及されているファイルの現状を確認:

```bash
codex exec "計画で言及されている以下のファイルの現状を確認し、
計画との整合性を検証してください" --full-auto --sandbox read-only
```

### 4. 結果の整理と保存

レビュー結果を保存:
- `.claude/work/plans/{plan-name}/plan-review.md`

### 5. 改善提案の報告

ユーザーに以下を報告:
- 計画の妥当性評価
- 懸念点とリスク
- 改善提案

---

## 出力フォーマット

```markdown
# Plan Review: {計画名}

## 評価サマリー
{全体的な評価: Good / Needs Improvement / Major Concerns}

## 技術的実現可能性
{分析結果}

## リスク評価
| リスク | 影響度 | 対策の妥当性 |
|-------|-------|-------------|
| {リスク1} | High/Medium/Low | {評価} |

## 見落としている観点
{あれば記載}

## 改善提案
1. {提案1}
2. {提案2}

## 推奨アクション
{次にすべきこと}
```

---

## 注意事項

- 計画ファイルが存在しない場合はエラー報告
- 必ず `--sandbox read-only` を使用
- 計画の変更は提案のみ、直接編集はしない
