---
name: codex
description: |
  Codex CLIへの実装委託スキル。Claudeで作成したplanファイルをCodex CLIに渡して実装を依頼。
  Use when: 定型実装、CRUD、テスト生成などDelegateレベルのタスク。
prompts:
  - prompts/implement.md
allowed-tools:
  - Read
  - Glob
  - Bash
  - Write
disable-model-invocation: true
---

# Codex CLI 実装委託

Claudeで設計したplanをCodex CLIに渡して実装を委託するワークフロー。

## 前提

- **Claudeの役割**: 設計、plan作成、品質レビュー
- **Codexの役割**: 高速実装、定型作業、テスト生成

---

## 実装精度を高める3つの要素

### 1. AGENTS.md（必須）

プロジェクトルートまたは `.codex/` に配置。Codexが自動読み込み。

**含めるべき内容:**
- プロジェクト概要
- ビルド・テストコマンド
- コーディング規約
- 禁止事項（Boundaries）
- 参照ファイル

**配置優先順位:**
1. 作業ディレクトリ直下の `AGENTS.md`
2. `.codex/AGENTS.md`
3. プロジェクトルートの `AGENTS.md`

### 2. config.toml

`.codex/config.toml` でプロジェクト固有設定を定義。

**推奨設定:**
```toml
sandbox_mode = "workspace-write"  # スイートスポット
model_reasoning_effort = "high"   # 推論精度向上

[profiles.implement]
model = "gpt-5.3-codex"
approval_policy = "never"
sandbox_mode = "workspace-write"
```

### 3. Planの品質

Codexに渡すplanには以下を含める:

```markdown
# 実装タスク: {タスク名}

## 目的
{なぜこの実装が必要か}

## スコープ
- 変更対象ファイル: {ファイル一覧}
- 除外事項: {触らないもの}

## 詳細な実装手順
1. {ステップ1}
2. {ステップ2}

## 品質基準
- テスト: {必要なテスト}
- 型安全: {型定義の注意点}

## 制約
- {技術的制約}
```

---

## コマンド

### `/codex:implement [plan-file] [--profile name]`

planファイルを指定してCodex CLIに実装を委託する。

**引数:**
- `plan-file`: planファイルのパス（省略時は最新のplan）
- `--profile`: 使用するプロファイル（implement/fast/review）

**プロファイル:**
| 名前 | モデル | 用途 |
|------|--------|------|
| `implement` | gpt-5.3-codex | 標準実装（デフォルト） |
| `fast` | gpt-5.1-codex-mini | 高速・低コスト実装 |
| `review` | gpt-5.3-codex | 読み取り専用レビュー |

---

## 実行フロー

```
1. AGENTS.md確認
   └ なければ作成を推奨

2. Planファイル特定
   └ 引数または最新plan

3. Codex CLI実行
   └ codex exec --profile implement

4. 結果確認
   └ git diff, git status
```

---

## AGENTS.md テンプレート

新規プロジェクトでAGENTS.mdを作成する際のテンプレート:

```markdown
# {Project Name} - Codex Agent Instructions

## Project Overview
{プロジェクトの概要を1-2文で}

## Directory Structure
{主要ディレクトリの説明}

## Build & Test Commands
{ビルド・テスト・lint等のコマンド}

## Coding Rules
{言語設定、命名規則、スタイルガイド}

## Boundaries
✅ Safe: {安全な操作}
⚠️ Requires confirmation: {確認が必要な操作}
🚫 Forbidden: {禁止操作}

## Reference Files
{参照すべきドキュメント}
```

---

## 使い分けガイド

| 状況 | 推奨 |
|------|------|
| 設計が必要 | Claudeでplan作成 → Codex実装 |
| 単純な修正 | Codexに直接依頼でもOK |
| 複雑なリファクタ | Claudeで実装（コンテキスト重要） |
| テスト生成 | Codexに委託（--profile fast） |
| コードレビュー | Claudeが実施 |

---

## 安全性

- `workspace-write` はプロジェクト内の変更のみ許可
- `full-access` は必要最小限の場合のみ使用
- 実装後は必ず `git diff` で確認すること

---

## 関連

- `/plan:clarify`: plan作成前の要件明確化
- `/code:review-uncommited`: 実装後のレビュー
- `.codex/AGENTS.md`: Codex向けプロジェクト指示
- `.codex/config.toml`: プロファイル定義
