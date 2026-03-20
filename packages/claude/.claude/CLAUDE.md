# Claude AI 基本設定

## 言語
- 対話: 日本語 / コード変数名: 英語 / コード内コメント: 日本語

## Iron Law（例外なし）
- git push 禁止（ユーザー明示指示必須）
- コミット: 1行 `<type>(<scope>): <日本語>` のみ。Co-Authored-By/HEREDOC/2行目以降 禁止
- git -C 必須（マルチリポジトリ）
- コードブロックにはGitHubリンク必須（repo/branch/path#L行番号）
- mcp.json トークン直接記載禁止（1Password CLI使用）
- ログに絵文字禁止
- 過度なエラーハンドリング・フォールバック禁止

## 責務分担
Claude Code = オーケストレーター（対話/判断/Plan/軽微修正1-2ファイル）。
大規模操作はサブエージェントに委託。メインコンテキストを汚染しない。
→ 詳細: ~/.claude/rules/delegation.md
