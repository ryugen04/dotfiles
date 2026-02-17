---
description: "計画レビュー: 現在のコードベースと実装計画の比較分析"
argument-hint: "<plan-file> [codebase]"
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Write
  - Task
---

# Visual Plan Review

**引数:** "$ARGUMENTS"

Generate a comprehensive visual plan review as a Markdown document. **Output must be written in Japanese.**

## ガイドライン

@skills/visual-explain/SKILL.md

## 入力

- Plan file: `$1` (markdown plan, spec, RFC)
- Codebase: `$2` or current working directory

## データ収集フェーズ

1. **計画ファイルを全文読み込み** — 問題文、各変更提案、却下案、スコープ
2. **計画が参照する全ファイルを読み込み** — 依存ファイルも含む
3. **影響範囲をマッピング** — import元、テストファイル、config、public API
4. **計画とコードをクロスチェック** — 参照先が実在するか、動作説明が正確か

## 検証チェックポイント

提示する全主張のファクトシートを作成:
- 定量値、関数名、型名、モジュール名
- 動作説明: 現在 vs 計画
- ソースを引用

## ドキュメント構造

1. **計画概要** — 解決する問題、核心的洞察、スコープ
2. **影響指標** — 変更/作成/削除ファイル、テスト計画(✅/❌)、docs(✅/⚠️/❌)
3. **現在のアーキテクチャ** — 影響部分のMermaid図
4. **計画後のアーキテクチャ** — 同レイアウトで差分を可視化
5. **変更詳細** — 各変更の`<details>`: 現状、計画、根拠
6. **依存関係分析** — `<details>`折りたたみ、✅ covered/⚠️ affected/❌ missed
7. **リスク評価** — Edge cases、Assumptions、Ordering、Rollback、Cognitive complexity（🔴/🟡/🔵）
8. **計画レビュー** — Good/Bad/Ugly/Questions
9. **理解ギャップ** — 根拠不明の変更数、認知複雑性フラグ

## 視覚的言語

ℹ️ current、✅ planned、⚠️ concern、❌ gap/risk

## 出力

`~/.agent/diagrams/` に書き込み、パスを伝える。

Ultrathink.
