---
description: "プロジェクト振り返り: 現状・最近の判断・認知負債ホットスポットの可視化"
argument-hint: "[time-window]"
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Write
  - Task
---

# Visual Project Recap

**引数:** "$ARGUMENTS"

Generate a comprehensive visual project recap as a Markdown document. **Output must be written in Japanese.**

## ガイドライン

@skills/visual-explain/SKILL.md

## 時間窓

引数から期間を判定:
- `2w`, `30d`, `3m` → git's `--since` format
- 引数なし: デフォルト `2w`

## データ収集フェーズ

1. **プロジェクト情報** — README、CHANGELOG、package.json等
2. **最近の活動** — `git log --oneline --since=<window>`、`git shortlog -sn`
3. **現在の状態** — `git status`、stale branches、TODO/FIXME
4. **判断コンテキスト** — commit messages、plan docs、ADRs
5. **アーキテクチャ** — entry points、public API、頻繁に変更されるファイル

## 検証チェックポイント

提示する全主張のファクトシートを作成、ソースを引用

## ドキュメント構造

1. **プロジェクト概要** — 現状サマリ、version、dependencies、elevator pitch
2. **アーキテクチャスナップショット** — Mermaid図（概念モジュールと関係）
3. **最近の活動** — テーマ別ナラティブ（feature、bugfix、refactor）
4. **設計判断ログ** — `<details>`: what、why、considered
5. **現状ダッシュボード** — ✅ Working/🔄 In Progress/❌ Broken/🚫 Blocked
6. **メンタルモデルの要点** — invariants、coupling、gotchas、conventions
7. **認知負債ホットスポット** — 🔴/🟡/🔵 + 具体的提案
8. **次のステップ** — 最近の活動から推測されるモメンタム

## 出力

`~/.agent/diagrams/` に書き込み、パスを伝える。

Ultrathink.
