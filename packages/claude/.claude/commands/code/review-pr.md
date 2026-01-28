---
description: "PRレビュー: merge baseとの差分を12個の専門エージェントで包括的にレビュー"
argument-hint: "[parallel]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# PR Review (Merge Base)

**引数:** "$ARGUMENTS"

## スコープ特定

```bash
git merge-base HEAD origin/main
git diff $(git merge-base HEAD origin/main)...HEAD --name-only
```

## レビュー定義

@skills/review/SKILL.md

## 実行

上記スキルに従い、12エージェントの起動・結果フォーマットを適用する。

レビュータイプ: `PR (MERGE BASE)`
