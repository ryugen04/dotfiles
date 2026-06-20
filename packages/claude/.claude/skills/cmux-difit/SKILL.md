---
name: cmux-difit
description: 現在のgitリポジトリのdiff（PR優先、なければマージベース比較）をcmuxブラウザの分割ペインに表示する。ユーザーが「difitで開いて」「右ペインにdiff」「PRの差分を見せて」「cmuxでdiff」「git diffをブラウザで」等の表現で差分表示を依頼した場合に使う。PR作成直後やレビュー時の視覚的差分確認に適用する。
allowed-tools: Bash
---

# cmux-difit

Git diff を `difit`（GitHub 風 diff ビューア）+ bridge 経由で cmux のブラウザ分割ペインに表示するスキル。PR 作成直後やレビュー時に右ペインで差分を目視確認したいときに使う。

## トリガー例

以下のような発話で発動する:

- 「difit で開いて」「difit で表示」
- 「右ペインに diff」「cmux に diff 出して」
- 「PR の差分を見せて」「この PR の diff をブラウザで」
- 「git diff をブラウザで」「差分を可視化」
- PR 作成直後に流れで差分確認したいとき

## 実行手順

### 1. 前提確認

- 現在のカレントディレクトリが git リポジトリであること（スクリプトが `pwd` を対象にする）
- `difit` が `packages/cmux/node_modules/.bin/difit` または PATH 上に存在すること
- 複数リポジトリを同時に開くことはできない（port 4966/4967 を単一プロセスが占有）
- **必ず `run_in_background: true` で実行する**。スクリプトが `wait` で difit / bridge プロセスを保持するため、foreground 実行するとブロックする

### 2. コマンド

```bash
<dotfiles-root>/packages/cmux/scripts/cmux-difit.sh
```

引数なし。cwd の git リポジトリを自動検出する。

スクリプトの挙動:

1. `git fetch origin <defaultBranch>` でリモート最新化
2. 現在ブランチに対応する PR を `gh pr list --head` で検索
3. PR あり: `difit --pr <PR_URL>` モードで起動
4. PR なし: `git merge-base origin/<defaultBranch> HEAD`..HEAD のローカル比較で起動（`--include-untracked` 付き）
5. 既存 `difit` / `bridge` プロセス（port 4966 / 4967）を `pkill` で停止
6. 新しい `difit` サーバーを port 4966 で起動（`--no-open --keep-alive`）
7. `cmux-difit-bridge.mjs` を port 4967 で起動（difit への中継）
8. ワークスペース内のフォーカス外ペインを探し、以下の順で `http://localhost:4967/` を開く:
   - 既存ブラウザサーフェスがあれば `cmux browser navigate` で navigate（3 ペイン以上に増えない）
   - ブラウザ無しなら `cmux new-surface --type browser --pane ...` でそのペインに新規タブ追加
   - フォーカス外ペインが無ければ `cmux browser open-split` で右に新規分割
9. `wait` で difit / bridge プロセスを保持（Ctrl+C / 次回起動時の pkill まで維持）

### 3. 起動確認

バックグラウンド実行後、以下で動作確認する:

```bash
sleep 3 && tail -20 /tmp/claude-*/tasks/<background-id>.output 2>/dev/null
```

期待される出力:

```
Showing PR: https://github.com/...  (PRあり時)  または
Showing diff: <sha>..HEAD (vs origin/develop)  (PRなし時)

🚀 difit server started on http://localhost:4966
📋 Reviewing: ...
🔒 Keep-alive mode: server will stay running after browser disconnects

Bridge server listening on http://localhost:4967
Proxying to difit at http://localhost:4966
OK ... placement=navigate    (既存ブラウザペインを再利用)
   または placement=tab      (既存ペインに新規ブラウザタブ追加)
   または placement=split    (右に新規分割)
```

`difit server started` と `OK ... placement=...` の 2 行が出ていれば成功。
`placement` は呼び出し時のペイン構成に応じて自動で切り替わる（3 ペイン以上に増えないよう優先順に試行）。

### 4. 再実行・切替

同じスキルを別の worktree / ブランチで再呼び出しすれば、自動的に前の difit / bridge プロセスが kill されて新リポジトリ・新ブランチに切り替わる。ユーザーから「次は XX の diff を見せて」と言われたら、該当の cwd に移動してから再実行する。

## 静的起動（サーバ常駐モード）

このスキルはサーバ常駐（静的起動）方式で動作する:

- `difit` は `--keep-alive` でブラウザ切断後も走り続ける
- `bridge` は `cmux-difit-bridge.mjs` として単発起動
- 次回 `cmux-difit.sh` 実行時に `pkill -f "difit.*4966"` / `pkill -f "cmux-difit-bridge.*4967"` で古いプロセスを落としてから再起動
- ポート 4966 / 4967 は固定。これ以外の値に変えるならスクリプト本体を修正する

## 制約・注意点

| 項目 | 内容 |
|------|------|
| 対象 | git リポジトリの作業ディレクトリ |
| 同時表示 | 1 リポジトリのみ（port 4966 / 4967 固定） |
| 必須オプション | `run_in_background: true` |
| cwd 依存 | スクリプトは `pwd` を対象にする。worktree 切替時は cwd 移動後に実行 |
| PR 検出 | `gh pr list --head <currentBranch>` に依存。未認証時は自動でローカル比較にフォールバック |
| 依存ツール | `difit`（dotfiles/packages/cmux の node_modules か global）、`gh`、cmux.app |

## 禁止事項

- foreground 実行（ブロックする）
- 4966 / 4967 を占有した状態で別用途のサーバを立てる
- 対象が git 管理外のディレクトリのときに無理に実行（スクリプトがエラー終了する）
- PR 本文の全文貼り付けと同時に呼び出す（ペイン表示の意図に反する）

## 関連

- スクリプト本体: `<dotfiles-root>/packages/cmux/scripts/cmux-difit.sh`
- bridge: `<dotfiles-root>/packages/cmux/scripts/cmux-difit-bridge.mjs`
- difit: Git diff ビューア（https://github.com/yoshiko-pg/difit）
- cmux: ターミナル多重化ブラウザ統合
- 姉妹スキル: `cmux-mo-preview`（Markdown 表示）
