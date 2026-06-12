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
- コードレビューは Codex CLI と Claude Code CLI を**必ずサブエージェント並列**で起動（メインは統合のみ） → ~/.claude/rules/code-review.md
- **パッケージインストール禁止**（pip/npm/brew/cargo 等、ユーザー明示承認必須） → ~/.claude/rules/no-install-without-approval.md
- 月 $40 固定費・fastMode 常時 ON 禁止 → ~/.claude/rules/budget-management.md

## 責務分担
Claude Code = オーケストレーター（対話/判断/Plan/軽微修正1-2ファイル）。
大規模操作はサブエージェントに委託。メインコンテキストを汚染しない。
実装委託の第一選択は **Codex CLI (`codex-implementer`)**。並列クロスチェックには `codex-reviewer` を併用。
→ 詳細: ~/.claude/rules/delegation.md
→ コードレビュー: ~/.claude/rules/code-review.md

## グローバルルール一覧
以下は `~/.claude/rules/` 配下の全プロジェクトで自動適用されるルール:
- code-review.md, delegation.md (既存)
- build-error-handling.md, plan-driven-workflow.md, investigation-report-format.md, knowledge-capture.md (Phase 2 で追加)
- document-review.md (Phase 2 で追加、2026-06-12 更新: Plan レビュー委託先を codex-reviewer に変更)
- proposal-and-blog-writing.md (2026-04-25 追加: プロポーザル/ブログ執筆の一次情報・採択ノウハウ準拠ルール)
- no-install-without-approval.md (2026-06-09 追加: サプライチェーン攻撃対策、パッケージインストール禁止)
- budget-management.md (2026-06-12 追加: 月固定費 $40、/fast 手動運用)
- codex-config-pitfalls.md (2026-06-12 追加: install.sh codex / Codex CLI profile / ChatGPT モデル制限の3つの落とし穴)
