# Claude AI 基本設定

## 言語
- ユーザーとの対話は日本語
- コード内の変数名・関数名は英語
- コード内コメントは日本語

## Gemini MCP 責務分担

Claude CodeとGemini MCPは明確に役割を分担する。

### Gemini MCPに委託すべきタスク
- ローカルコードベースの大規模調査（@構文でファイル指定）
- 長文ログファイルの解析
- 複雑なリファクタリング提案（changeMode使用）
- 大量コードからのドキュメント生成
- Web検索（プロンプトで「web searchを使って」と指示）
- ブレインストーミング・アイデア生成

### Claude Codeが担当するタスク
- ユーザーとの対話・質問応答
- タスク管理・進捗管理（TodoWrite）
- 軽微なコード修正・編集
- 最終的な成果物の確認・統合

### 利用ルール
- コンテキスト消費が大きいタスクは積極的にGeminiに委託
- Web検索はGeminiに「web searchで〜を調べて」と指示
- skillsで定義された操作はsubagentを起動して実行

### Gemini委託時の品質基準
- 省略禁止: 「他にも...」「など」で逃げない、全件列挙
- 私見禁止: 推測・提案は書かない、事実のみ
- 具体性: 必ず引用元（ファイル:行番号 or URL）を付ける
- 出力先: プロジェクトルートの `.claude/gemini-reports/` に書き出させる
  （プロジェクト固有のデータとして管理）

## コード品質
- 明示的な指示がない限り、過度なエラーハンドリングやフォールバック処理は実装しない
- ログ出力に絵文字は使用しない
- 簡潔で必要最小限のコードを心がける

## Git コミット
- Conventional Commits形式を使用
- descriptionは日本語で記述
- 50文字以内で簡潔に

## シークレット管理

**mcp.jsonへのトークン直接記載は禁止**

MCPサーバーでトークンが必要な場合は1Password CLIを使用:
```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "op://vault/item/credential"
  }
}
```

または起動スクリプトで`op read`を使用:
```bash
export GITHUB_TOKEN=$(op read "op://Personal/GitHub PAT/credential")
```

## Claude Code 機能活用

### LSP機能
- go-to-definition: 関数やクラスの定義元に移動
- find-references: シンボルの参照箇所を検索
- 大規模調査時はGemini MCPに委託し、ピンポイント調査時はLSP機能を活用

### Ultrathink Mode
- `alwaysThinkingEnabled: true` で常時有効
- 複雑なロジック設計・アーキテクチャ判断時に特に有効
- 単純な修正タスクでは通常思考で十分

### /teleport
- セッションをNeovim等の別環境に移動
- コンテキストを維持したまま作業環境を切り替え可能
