---
description: "ドメイン調査: PBI精緻化のための調査をGemini MCPで実行"
argument-hint: "[調査テーマ]"
allowed-tools: ["Read", "Write", "mcp__gemini-cli__ask-gemini"]
---

# ドメイン調査 (Spike)

**調査テーマ:** "$ARGUMENTS"

## 知識ベース

@skills/knowledge/scrum/SKILL.md
@skills/knowledge/gemini/SKILL.md

## 実行手順

1. 調査の問いを明確化
2. 調査の種類を判断（ドメイン知識 / 技術調査 / 競合調査）
3. Gemini MCPに委託
4. 結果を構造化してまとめ

## Gemini委託時のルール

- 省略禁止: 全件列挙
- 私見禁止: 事実のみ
- 具体性: ソースURL or ファイル:行番号を必ず付ける

## 出力

知識ベースの出力フォーマットに従い、以下に保存:

```
.claude/scrum/domain/{YYYYMMDD}-{日本語トピック}.md
```

**注意:** プロジェクト固有のファイルです。
