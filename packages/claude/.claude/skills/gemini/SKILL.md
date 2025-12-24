---
name: gemini
description: Gemini MCPの効果的な活用ガイド。コンテキスト節約のための委託判断を支援する。使用タイミング: (1) 大規模なコード調査が必要な時、(2) 長文ログの解析が必要な時、(3) コンテキスト消費を抑えたい時、(4) Geminiへの委託方法を確認したい時。
---

# Gemini MCP 活用ガイド

## 利用可能なツール

| ツール | 用途 |
|--------|------|
| `ask-gemini` | プロンプト送信、ファイル分析、Web検索 |
| `brainstorm` | アイデア生成、創造的思考 |

## 能力

### ローカルファイル分析
`@`構文でファイルを指定して分析を委託する。

```
prompt: "@src/auth/login.ts @src/auth/session.ts この認証フローを解析して"
```

### Web検索（Google Search Grounding）
プロンプトで「web searchを使って」と明示的に指示する。

```
prompt: "Please use a web search to find the latest Claude Code plugins and MCP servers"
```

```
prompt: "web searchで2025年のReact best practicesを調べて"
```

### 編集提案モード
changeMode=trueで構造化された編集提案を取得する。

```
prompt: "@src/api/users.ts エラーハンドリングを改善して"
changeMode: true
```

### コード実行（sandbox）
sandbox=trueでコードを安全に実行する。Web検索とは無関係。

```
prompt: "このPythonスクリプトを実行して結果を教えて"
sandbox: true
```

## 委託判断フロー

1. 外部の最新情報が必要？ → Gemini（web search指示付き）
2. ローカルファイルの大量読み込み？ → Gemini（@構文）
3. コンテキスト節約が重要？ → Gemini
4. ユーザー対話が必要？ → Claude Code直接対応

## 使い分け

| タスク | ツール | 備考 |
|--------|--------|------|
| 最新情報の調査 | Gemini + web search指示 | Google Search Grounding |
| 大規模コード分析 | Gemini + @構文 | 100万トークンウィンドウ活用 |
| ブレインストーミング | brainstorm | 構造化されたアイデア生成 |
| 軽微なコード編集 | Claude Code | 直接対応が効率的 |
