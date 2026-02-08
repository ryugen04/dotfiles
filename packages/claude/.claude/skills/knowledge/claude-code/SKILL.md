---
name: claude-code
description: |
  Claude Codeのバージョン管理、ベストプラクティス調査に関する知識。
  情報源の品質基準、調査方法、設定更新のワークフロー。
disable-model-invocation: true
---

# Claude Code 知識ベース

## バージョン管理

### バージョン取得方法

| 種類 | 取得方法 |
|------|----------|
| インストール済み | `claude --version` |
| npm最新 | `npm view @anthropic-ai/claude-code dist-tags --json` |
| 準拠バージョン | `packages/claude/.claude/claude-code/VERSION.md` |

### アップデート方法

```bash
# グローバルアップデート
npm update -g @anthropic-ai/claude-code

# または公式コマンド
claude update
```

---

## 情報源の品質基準

### エキスパート情報源の判定基準

1. **技術力の確認**
   - GitHubプロフィール: OSS貢献、スター数
   - 過去の投稿: 技術的深さ、正確性
   - 所属: Anthropic社員、著名企業のエンジニア

2. **実践度の確認**
   - 実際に使った上での知見か
   - 設定例・コード例が具体的か
   - 問題と解決策が明確か

3. **鮮度の確認**
   - 最新バージョンに対応しているか
   - 日付が明記されているか
   - 非推奨になった機能に言及していないか

### 除外すべき情報源の特徴

- **浅いまとめ記事**
  - 「〇〇選」「初心者向け」「入門」
  - 公式ドキュメントの転載
  - 広告やアフィリエイト目的

- **非エンジニアの記事**
  - 技術的な深さがない
  - 設定例がない
  - 推測や伝聞が多い

- **古い情報**
  - 1年以上前の記事
  - 非推奨機能の紹介
  - バージョンが明記されていない

---

## 調査対象

### 検索クエリ例

```
# X (Twitter)
"claude code" settings OR hooks OR tips since:2025-01-01
"@anthropic" claude code best practices
claude code workflow -ad -promo

# GitHub
repo:anthropics/claude-code discussions
repo:anthropics/claude-code issues

# 技術ブログ
site:zenn.dev "claude code" 設定
site:qiita.com "claude code" tips
```

### 収集すべき項目

1. **設定関連**
   - settings.json のベストプラクティス
   - パフォーマンス最適化設定
   - セキュリティ設定

2. **拡張機能**
   - hooks の実用例
   - skills/commands のカスタマイズ
   - MCP サーバー連携

3. **ワークフロー**
   - 効率的な使い方
   - チーム開発での活用
   - CI/CD連携

4. **トラブルシューティング**
   - よくある問題と解決策
   - パフォーマンス問題
   - 互換性問題

---

## 調査レポートフォーマット

```markdown
# Claude Code ベストプラクティス調査レポート

調査日: YYYY-MM-DD
トピック: [トピック名 or 全般]
調査者: Claude Code

## サマリー

- 収集した知見数: N件
- 主要な発見:
  1. ...
  2. ...

## 収集した知見

### カテゴリ1: [カテゴリ名]

#### 知見1: [タイトル]

- **情報源**: [URL]
- **著者**: [名前/ハンドル]
- **日付**: YYYY-MM-DD
- **信頼度**: 高/中/低

**内容**:
[具体的な知見の説明]

**設定例**（あれば）:
```json
{
  "example": "value"
}
```

**適用判断**:
- 推奨度: 高/中/低
- 理由: [なぜ推奨/非推奨か]

---

## 次のアクション

1. [ ] 適用検討: [項目]
2. [ ] 追加調査: [項目]
```

---

## dotfiles更新ワークフロー

### 1. 事前確認

- [ ] 現在の設定をバックアップ
- [ ] VERSION.md の準拠バージョン確認
- [ ] 変更履歴の確認

### 2. 調査実行

- [ ] /cc:research で最新情報収集
- [ ] 調査レポートの確認
- [ ] 適用すべき項目の選定

### 3. 変更適用

- [ ] 各変更をユーザーに提案
- [ ] 承認された変更を適用
- [ ] 変更後の動作確認

### 4. 記録更新

- [ ] VERSION.md の最終調査日更新
- [ ] 適用済みベストプラクティスに追記
- [ ] 必要に応じてCLAUDE.md更新

---

## 関連コマンド

| コマンド | 説明 |
|---------|------|
| `/cc:version` | バージョン比較表示 |
| `/cc:research` | ベストプラクティス調査 |
| `/cc:update` | dotfiles更新提案・実行 |

---

## データ保存先

```
packages/claude/.claude/
├── claude-code/
│   ├── VERSION.md           # バージョン情報
│   └── research/            # 調査レポート
│       └── YYYY-MM-DD.md
└── commands/cc/
    ├── version.md
    ├── research.md
    └── update.md
```
