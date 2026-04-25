---
name: cmux-mo-preview
description: Markdownファイルをcmuxブラウザの分割ペインに表示する。ユーザーが「moで開いて」「このペインに開いて」「右ペインに表示して」「cmuxに表示」等の表現でMarkdownファイルの表示を依頼した場合に使う。調査レポート・設計ドキュメント・plan等をユーザーが読みたいと言った時にも適用する。
allowed-tools: Bash, Read
---

# cmux-mo-preview

Markdown ファイルを `mo` サーバー経由で cmux のブラウザ分割ペインに表示するスキル。ユーザーが画面右側のブラウザペインで Markdown を読みたいときに使う。

## トリガー例

以下のような発話で発動する:

- 「mo で開いて」「moで表示」
- 「このペインに開いて」「右ペインに表示して」
- 「cmux に開いて」「cmux ペインに表示」
- 調査レポートや design doc を「読みます」「読みたい」とユーザーが言った時、過去に cmux-mo を使う運用だと判明している場合

## 実行手順

### 1. 前提確認

- 対象は `.md` ファイルであること
- 複数ファイルを同時に開くことはできない（port 6275 を単一 `mo` プロセスが占有）
- **必ず `run_in_background: true` で実行する**。スクリプトが `wait` で mo プロセスを保持するため、foreground 実行するとブロックする

### 2. コマンド

```bash
<dotfiles-root>/packages/cmux/scripts/cmux-mo.sh <absolute-or-relative-path-to.md>
```

スクリプトの挙動:

1. 既存 `mo` プロセス（port 6275）を `pkill` で停止
2. 新しい `mo` サーバーを指定ファイルで起動
3. cmux の `browser open-split` で右ペインに `http://localhost:6275/` を開く
4. `wait` で mo プロセスを保持（Ctrl+C / 次回起動時の pkill まで維持）

### 3. 起動確認

バックグラウンド実行後、以下で動作確認する:

```bash
sleep 1 && cat /tmp/claude-*/tasks/<background-id>.output 2>/dev/null | head -5
```

期待される出力:

```
{"time":"...","level":"INFO","msg":"serving","url":"http://localhost:6275"}
OK surface=surface:N pane=pane:N placement=split
```

この2行が出ていれば成功。

### 4. ファイル切替

同じスキルを別ファイルで再呼び出しすれば、自動的に前の mo プロセスが kill されて新ファイルに切り替わる。ユーザーから「次は XX を開いて」と言われたら素直に再実行する。

## 制約・注意点

| 項目 | 内容 |
|------|------|
| 対象フォーマット | Markdown（`.md`）のみ。その他の形式は Read で返す |
| 同時表示 | 1ファイルのみ（port 6275 固定） |
| 必須オプション | `run_in_background: true` |
| 絶対パス推奨 | スクリプトは相対パスも受け付けるが、cwd 依存を避けるため絶対パスで渡す |
| 依存ツール | `mo`（`brew install k1LoW/tap/mo`）、cmux.app |

## 禁止事項

- foreground 実行（ブロックする）
- Bash の別プロセスで `mo` を直接起動（cmux browser split の連携が途切れる）
- 対象ファイルが `.md` 以外の場合に無理に実行
- ユーザーに表示内容を本文で全文貼り付けながらスキル実行（ペイン表示の意図に反する）

## 関連

- スクリプト本体: `<dotfiles-root>/packages/cmux/scripts/cmux-mo.sh`
- mo: Markdown サーバー（https://github.com/k1LoW/mo）
- cmux: ターミナル多重化ブラウザ統合
