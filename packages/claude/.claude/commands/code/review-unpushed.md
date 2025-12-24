---
description: "未プッシュコミットのレビュー: 12個の専門エージェントで包括的にレビュー"
argument-hint: "[parallel]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# Unpushed Commits Review

**引数:** "$ARGUMENTS"

## スコープ特定

```bash
git log @{u}..HEAD --oneline
git diff @{u}..HEAD --name-only
```

## レビュー定義

@skills/code/reviewing-code/SKILL.md

## 実行

上記スキルに従い、12エージェントの起動・結果フォーマットを適用する。

レビュータイプ: `UNPUSHED COMMITS`
