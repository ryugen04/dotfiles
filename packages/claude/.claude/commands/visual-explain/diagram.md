---
description: "ダイアグラム生成: Mermaidを使った視覚的な図の作成"
argument-hint: "<description>"
allowed-tools:
  - Glob
  - Grep
  - Read
  - Write
---

# Visual Diagram Generator

**引数:** "$ARGUMENTS"

Generate a Markdown diagram. **Output must be written in Japanese.**

## ガイドライン

@skills/visual-explain/SKILL.md

## ダイアグラムタイプ

| タイプ | アプローチ |
|--------|-----------|
| Architecture (topology) | Mermaid `graph` |
| Architecture (text-heavy) | Markdown sections + tables |
| Flowchart / pipeline | Mermaid `graph TD/LR` |
| Sequence diagram | Mermaid `sequenceDiagram` |
| Data flow | Mermaid `graph` with edge labels |
| ER / schema | Mermaid `erDiagram` |
| State machine | Mermaid `stateDiagram-v2` |
| Mind map | Mermaid `mindmap` |
| Data table | Markdown table |
| Comparison | Tables or `<details>` |
| Timeline | Table with dates |
| Dashboard / KPI | Tables with bold values |

## Mermaidガイドライン

- `graph TD` for top-down, `graph LR` for left-right
- subgraphsでグループ化
- 短いラベル、詳細は凡例テーブル
- `classDef`は控えめに
- ラベルに特殊文字は避ける

## 状態インジケーター

✅ Match/Pass、❌ Gap/Fail、⚠️ Partial/Warning、ℹ️ Info
🔴 High、🟡 Medium、🔵 Low

## 出力

`~/.agent/diagrams/` に説明的ファイル名で書き込み、パスを伝える。
