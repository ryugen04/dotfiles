---
description: "差分レビュー: before/afterのアーキテクチャ比較とコードレビュー分析"
argument-hint: "[ref]"
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Write
  - Task
---

# Visual Diff Review

**引数:** "$ARGUMENTS"

Generate a comprehensive visual diff review as a Markdown document. **Output must be written in Japanese.**

## ガイドライン

@skills/visual-explain/SKILL.md

## スコープ検出

引数から差分範囲を判定:
- ブランチ名 (例: `main`, `develop`): working tree vs そのブランチ
- コミットハッシュ: そのコミットの差分 (`git show <hash>`)
- `HEAD`: uncommitted changesのみ (`git diff` と `git diff --staged`)
- PR番号 (例: `#42`): `gh pr diff 42`
- 範囲 (例: `abc123..def456`): 2つのコミット間の差分
- 引数なし: デフォルトは `main`

## データ収集フェーズ

以下を先に実行してスコープを把握:
- `git diff --stat <ref>` でファイルレベルの概要
- `git diff --name-status <ref> --` で新規/変更/削除ファイル
- 行数比較: 主要ファイルを`<ref>`とworking treeで比較
- 新規公開API: exportシンボル、public関数、クラス、interfaceをgrep
- 変更ファイルを全て読み込む
- `CHANGELOG.md` にエントリがあるか確認
- `README.md` や `docs/*.md` の更新が必要か確認
- 決定の根拠を再構築: commit message、PR description、会話履歴から

## 検証チェックポイント

Markdown生成前に、提示する全主張のファクトシートを作成:
- 全定量値: 行数、ファイル数、関数数、テスト数
- 参照する全関数名、型名、モジュール名
- 全動作説明: コードの動作、変更内容、before vs. after
- 各項目のソースを引用

## ドキュメント構造

1. **概要** — 変更の直感的理解、スコープ（Xファイル、Y行）
2. **変更指標** — 追加/削除行、変更ファイル、CHANGELOG更新(✅/❌)
3. **モジュール構成** — ファイル構造変更、Mermaid依存グラフ
4. **主要な変更点** — 各変更領域の`<details>`折りたたみ、before/after説明
5. **フローダイアグラム** — 新パターンのMermaid図
6. **ファイルマップ** — 絵文字カラーコード（✨ new、📝 modified、🗑️ deleted）
7. **テストカバレッジ** — before/afterテストファイル数
8. **コードレビュー** — Good/Bad/Ugly/Questions分析
9. **設計判断ログ** — Decision、Rationale、Alternatives、Confidence
10. **引き継ぎコンテキスト** — Key invariants、Non-obvious coupling、Gotchas

## 視覚的言語

✅ added/after、❌ removed/before、⚠️ modified/warning、ℹ️ neutral

## 出力

`~/.agent/diagrams/` に説明的ファイル名で書き込み、パスを伝える。

Ultrathink.
