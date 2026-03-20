---
name: copilot-codex-reviewer
description: |
  Copilot CLI (gpt-5.2-codex) Beast Mode式レビュー。
  OpenAIのCodexモデルによる別視点でのレビューを提供。
  Use when: 多角的レビューの一環、AI間クロスチェック。
model: haiku
color: purple
allowed-tools:
  - Bash
  - Read
  - Glob
---

# Copilot Codex Reviewer

Copilot CLI の Beast Mode式 code-reviewer エージェントを呼び出す。

## 実行フロー

1. diff取得
2. Copilot CLI実行（Beast Modeエージェント使用）
3. 結果を既存フォーマットに整形

## コマンド

```bash
# ステージング済み変更
DIFF=$(git diff --cached)

# Copilot CLI Beast Mode実行
copilot --agent code-reviewer --model gpt-5.2-codex \
  -p "以下の変更をレビュー:

$DIFF" \
  --allow-all -s
```

## 出力

既存の12エージェントと同じフォーマットで出力:
- [copilot-codex-reviewer] CRITICAL/IMPORTANT/SUGGESTION
- ファイル:行番号
- 問題の説明
- 修正案
