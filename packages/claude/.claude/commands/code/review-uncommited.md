---
description: "未コミット変更のレビュー: 12個の専門エージェントで包括的にレビュー"
argument-hint: "[parallel]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# Uncommited Changes Review

**引数:** "$ARGUMENTS"

## スコープ特定

```bash
git status --porcelain
git diff --cached --name-only  # ステージング済み
git diff --name-only           # 未ステージング
```

## レビュー定義

@skills/code/reviewing-code/SKILL.md

## 実行

上記スキルに従い、12エージェントの起動・結果フォーマットを適用する。

レビュータイプ: `UNCOMMITED CHANGES`
