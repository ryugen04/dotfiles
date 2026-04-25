---
description: Codex CLIを使用してコードレビューを実行
argument-hint: [BRANCH=<branch-name>] [FOCUS=<focus-area>]
allowed-tools: Bash, Read, Write, Glob
---

# /codex:review - Codex CLI コードレビュー

Codex CLIを使用して、指定されたブランチまたは未コミット変更をレビューします。

## 引数

- `BRANCH`: レビュー対象ブランチ（省略時: 未コミット変更）
- `FOCUS`: 注目領域（例: "security", "performance", "all"）

## 実行手順

### 1. 対象の確認

```bash
# ブランチ指定がある場合
git fetch origin
git diff origin/develop...origin/$BRANCH --stat

# 未コミット変更の場合
git status
git diff --stat
```

### 2. Codex CLI でレビュー実行

```bash
# 未コミット変更（デフォルト）
codex exec "/review uncommitted" --full-auto --sandbox read-only

# ブランチ指定
codex exec "/review base-branch develop" --full-auto --sandbox read-only
```

カスタムフォーカスがある場合:
```bash
codex exec "/review uncommitted" --full-auto --sandbox read-only \
  -c 'developer_instructions="$FOCUS 観点に注目してレビュー"'
```

### 3. 結果の整理と保存

レビュー結果を以下に保存:
- プランファイル: `.claude/plans/review-{branch}.md`
- 中間成果物: `.claude/work/plans/review-{branch}/`

### 4. サマリー報告

重要な発見事項をユーザーに報告。

---

## 出力フォーマット

```markdown
# Codex Review: {対象}

## 概要
{1-3行のサマリー}

## Critical Issues
{重大な問題があれば記載}

## Recommendations
{改善提案}

## Review Details
{Codex出力の詳細}
```

---

## 注意事項

- 必ず `--sandbox read-only` を使用
- 結果は `.claude/work/` 配下に保存
- Codex CLI未インストール時はエラー報告
