---
name: cmux-mo-preview
description: Markdownファイルをcmuxのmarkdownビューアで表示する。右ペインが既に存在すればそこに新規タブとして開き、3分割以上に増えるのを防ぐ。ユーザーが「moで開いて」「このペインに開いて」「右ペインに表示して」「cmuxに表示」等の表現でMarkdownファイルの表示を依頼した場合に使う。調査レポート・設計ドキュメント・plan等をユーザーが読みたいと言った時にも適用する。
allowed-tools: Bash, Read
---

# cmux-mo-preview

Markdown ファイルを cmux ネイティブの markdown ビューア（ライブリロード対応）に表示するスキル。
`mo` / port 6275 を使う旧実装は廃止し、cmux の `open` / `markdown` サブコマンドを直接呼ぶ構成に置き換わっている。

## トリガー例

- 「mo で開いて」「moで表示」
- 「このペインに開いて」「右ペインに表示して」
- 「cmux に開いて」「cmux ペインに表示」
- 調査レポートや design doc を「読みます」「読みたい」とユーザーが言った時

## 振る舞い

スクリプト `cmux-mo.sh` は呼び出し時に以下の判定を行う:

1. `cmux list-panes` でワークスペース内のペイン一覧を取得
2. フォーカスされていないペインが存在するか確認
   - **存在する** → そのペインに `cmux open <file> --pane <id>` で新規タブとして開く（分割は増えない）
   - **存在しない** → `cmux markdown <file> --direction right` で右に分割して開く

これにより、左右に分割済みの状態でさらにファイルを開いても 3 ペイン以上に増殖しない。

## 実行手順

### 1. 前提確認

- 対象は `.md` ファイルであること（cmux 側の markdown プレビューが起動する）
- foreground 実行で構わない（旧 `wait` ループは廃止済み。スクリプトは即終了する）
- バックグラウンド実行は不要。`run_in_background: true` は付けない

### 2. コマンド

```bash
<dotfiles-root>/packages/cmux/scripts/cmux-mo.sh <absolute-or-relative-path-to.md>
```

### 3. 起動確認

成功時は標準出力に以下のいずれかが出る:

```
OK opened=<file> pane=<pane:N> placement=tab     # 既存ペインへのタブ追加
OK opened=<file> placement=split                  # 右分割を新規作成
```

### 4. ファイル切替

別ファイルを開きたい場合、同じスクリプトを再実行するだけでよい。
すでに右ペインが存在していれば、そこに新タブとして追加される（前のタブは閉じない）。
前のタブを閉じたい場合はユーザーに cmux 上で操作してもらう。

## 制約・注意点

| 項目 | 内容 |
|------|------|
| 対象フォーマット | Markdown（`.md`）以外を渡すとファイルプレビュータブで開く挙動になる |
| 同時表示 | タブとして複数開ける（旧実装の「1 ファイルのみ」制約は解消） |
| 必須オプション | なし。foreground 実行で OK |
| 絶対パス推奨 | スクリプトは相対パスも受け付けるが cwd 依存を避けるため絶対パスで渡す |
| 依存ツール | `cmux.app`（ネイティブ markdown ビューア搭載版） |

## 禁止事項

- `run_in_background: true` を付けて呼ぶ（旧実装の名残。新実装ではブロックしないため不要）
- 対象ファイル本文を全文 Read で取得しながらスキルを実行（ペイン表示の意図に反する）
- 旧 `mo` サーバー（port 6275）の手動起動を併用

## 関連

- スクリプト本体: `<dotfiles-root>/packages/cmux/scripts/cmux-mo.sh`
- cmux markdown サブコマンド: `cmux markdown --help`
- cmux open サブコマンド: `cmux open --help`
