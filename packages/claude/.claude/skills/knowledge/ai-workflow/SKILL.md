---
name: ai-workflow
description: AI駆動開発のツール選択・協業レベル判断の知識。Claude Code / Codex CLI / Gemini CLIの使い分け指針。
disable-model-invocation: true
---

# AI駆動開発ワークフロー

AI駆動開発（AI-DLC）におけるツール選択と協業レベルの判断基準。

---

## チーム構成

| 役割 | 担当 | 責務 |
|------|------|------|
| PO | ユーザー | バックログ優先度、受け入れ判断 |
| SM | ユーザー | プロセス改善、障害除去 |
| 開発者（設計） | Claude Code | アーキテクチャ、リファクタ、コードレビュー |
| 開発者（実装） | Codex CLI | 高速コーディング、テスト生成、並列タスク |
| 開発者（調査） | Gemini CLI | 技術調査、ドキュメント分析、Web検索 |

---

## 協業レベル（CAID）

| レベル | ユーザー関与 | AI担当 | 例 |
|--------|-------------|--------|-----|
| **C**onsult | 判断・決定 | 提案 | アーキテクチャ決定、技術選定 |
| **A**gree | 確認・承認 | 実行 | PBI分解、リファクタ計画 |
| **I**nquire | 最終確認 | 報告 | コードレビュー結果、テスト結果 |
| **D**elegate | 事後確認のみ | 完全委託 | フォーマット、テスト生成、定型実装 |

---

## ツール選択マトリクス

### タスク種別 → ツール

| タスク種別 | 推奨ツール | 理由 |
|-----------|-----------|------|
| 設計・アーキテクチャ | Claude Code | 深い思考、一貫性 |
| リファクタリング | Claude Code | コンテキスト理解 |
| コードレビュー | Claude Code | MCP統合、品質重視 |
| 単純実装（CRUD等） | Codex CLI | 高速、コスト効率 |
| テスト生成 | Codex CLI | 並列実行、高速 |
| フォーマット・lint | Codex CLI | 機械的処理 |
| 大規模調査 | Gemini CLI | トークン制限なし |
| Web検索 | Gemini CLI | 最新情報取得 |
| ドキュメント分析 | Gemini CLI | 長文処理 |

### 協業レベル → ツール

| レベル | 推奨ツール |
|--------|-----------|
| Consult | Claude Code（対話的） |
| Agree | Claude Code |
| Inquire | Claude Code or Codex CLI |
| Delegate | Codex CLI（高速委譲） |

---

## 判断フローチャート

```
タスクを受け取る
    │
    ├─ 設計・アーキテクチャに関わる？
    │   └─ Yes → Claude Code（Consult）
    │
    ├─ コードレビューが必要？
    │   └─ Yes → Claude Code（Inquire）
    │
    ├─ 大規模な調査が必要？
    │   └─ Yes → Gemini CLI
    │
    ├─ 定型的・機械的な作業？
    │   └─ Yes → Codex CLI（Delegate）
    │
    └─ その他
        └─ Claude Code（デフォルト）
```

---

## コスト意識

| ツール | 相対コスト | 速度 |
|--------|----------|------|
| Claude Code | 高 | 中 |
| Codex CLI | 低 | 高 |
| Gemini CLI | 低 | 中 |

**原則**: 品質が求められる場面はClaude Code、速度・コスト優先の場面はCodex CLI。

---

## アンチパターン

### 避けるべきパターン

1. **全部Claude Code**
   - 単純タスクにも高コストツールを使う
   - → 定型作業はCodex CLIに委譲

2. **調査なしで実装**
   - 不確実性の高いタスクをいきなり実装
   - → `/scrum:spike` で調査してから

3. **レビューなし**
   - 委譲タスクを確認せず受け入れ
   - → Inquireレベルで最低限の確認

4. **過剰な介入**
   - Delegateレベルのタスクに細かく指示
   - → 委譲したら結果だけ確認
