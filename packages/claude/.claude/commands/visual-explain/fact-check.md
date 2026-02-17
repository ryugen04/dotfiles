---
description: "事実検証: ドキュメントの内容をコードベースと照合し修正"
argument-hint: "[file-path]"
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Write
  - Edit
---

# Visual Fact Check

**引数:** "$ARGUMENTS"

Verify factual accuracy of a document against codebase.

## ガイドライン

@skills/visual-explain/SKILL.md

## 対象ファイル

- 明示的パス: そのファイルを検証
- 引数なし: `~/.agent/diagrams/` の最新 `.md` ファイル

## フェーズ

### 1. 主張の抽出

検証可能な事実のみ抽出:
- **定量**: 行数、ファイル数、関数数、テスト数
- **名前**: 関数名、型名、モジュール名、ファイルパス
- **動作**: コードの動作説明、before/after比較
- **構造**: アーキテクチャ、依存関係
- **時間**: git履歴、タイムライン

主観的分析（意見、設計判断）はスキップ。

### 2. ソースと照合

- 参照ファイルを再読み込み
- git履歴の主張: gitコマンドを再実行
- diff-review: `git show <ref>:file` と working tree を比較
- plan docs: 参照先の実在と動作を確認

分類:
- **✅ Confirmed**: 正確
- **🔧 Corrected**: 不正確 → 修正
- **❓ Unverifiable**: 検証不可

### 3. 直接修正

- 不正確な数値、関数名、パス、動作説明を修正
- before/after入れ替えを修正
- レイアウト、Mermaid図は保持

### 4. 検証サマリー追加

```markdown
---

## 検証サマリー

| 項目 | 件数 |
|------|------|
| 検証済み | X件 ✅ |
| 修正済み | Y件 🔧 |
| 検証不可 | Z件 ❓ |

### 修正内容
- `processCleanup` → `runCleanup` に修正
- ファイル数 12 → 14 に修正
```

### 5. 報告

検証結果とファイルパスをユーザーに伝える。

Ultrathink.
