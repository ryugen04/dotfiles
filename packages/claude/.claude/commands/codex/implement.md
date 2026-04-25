---
description: Codex CLIを使用してplanファイルに基づく実装を委託
argument-hint: PLAN=<plan-file-path>
allowed-tools: Bash, Read, Write, Glob, Grep
---

# /codex:implement - Codex CLI 実装委託

planファイルを読み込み、Codex CLIに実装を委託します。

## 引数

- `PLAN`: 実装対象の計画ファイルパス（必須）

## 対象タスク

- CRUD実装
- 既存パターンの踏襲
- テスト生成
- リファクタリング

---

## 実行手順

### 1. planファイルの確認

```bash
# 計画ファイルの存在確認
ls -la $PLAN
```

planファイルを読み込み、実装タスクを把握。

### 2. 作業フォルダの準備

```bash
# planファイル名からフォルダ名を生成
PLAN_NAME=$(basename $PLAN .md)
mkdir -p .claude/work/plans/$PLAN_NAME
```

### 3. Codex CLI で実装実行

```bash
codex exec "以下のplanに従って実装してください。
既存のコードパターンを参照し、一貫性を保ってください。

plan: @$PLAN" --full-auto --sandbox network-off
```

### 4. 実装結果の検証

```bash
# Kotlinの場合
./gradlew compileKotlin

# TypeScriptの場合
pnpm type-check
```

### 5. 結果の保存

実装結果を保存:
- `.claude/work/plans/{plan-name}/implementation-result.md`

### 6. 結果の報告

ユーザーに以下を報告:
- 変更されたファイル一覧
- コンパイル/型チェック結果
- 未完了項目（あれば）

---

## 出力フォーマット

```markdown
# Implementation: {plan-name}

## Summary
{1-3行の要約}

## Changes
| ファイル | 変更内容 |
|---------|---------|
| `path/to/file1.kt` | {概要} |

## Verification
- [x] コンパイル: PASS / FAIL
- [x] 型チェック: PASS / FAIL

## Remaining
{未完了項目があれば}

## Next Steps
{次のアクション}
```

---

## フォールバック条件

以下の場合、impl-integrator への切り替えを検討:

- Codex CLIがplanを理解できない
- アーキテクチャ判断が必要
- 複数コンポーネントの連携が必要
- 3回以上リトライしても失敗

フォールバック時:
```
Task → impl-integrator に委託
```

---

## 注意事項

- planファイルが存在しない場合はエラー報告
- 必ず `--sandbox network-off` を使用
- コンパイル確認を必ず実行
- 失敗時はフォールバックを検討
