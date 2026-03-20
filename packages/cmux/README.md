# cmux integration tools

cmuxのブラウザペイン機能を活用するツール群。

## 依存ツール

### difit (yoshiko-pg/difit)
Git diffのGitHub風ビューア。

```bash
cd packages/cmux
npm install
```

### mo (k1LoW/mo)
Markdownリアルタイムプレビュー。

```bash
brew install k1LoW/tap/mo
```

### yq (mikefarah/yq)
YAML/JSONパーサー。プリセット機能で使用。

```bash
brew install yq
```

## スクリプト

| スクリプト | 説明 |
|-----------|------|
| `cmux-difit.sh` | Git diffをcmuxブラウザで表示 |
| `cmux-mo.sh` | Markdownをcmuxブラウザでプレビュー |
| `cmux-open.sh` | URLまたはプリセットをcmuxブラウザで開く |

## Claude Code スラッシュコマンド

| コマンド | 説明 |
|---------|------|
| `/cmux:difit` | 現在のブランチのdiffをブラウザ表示 |
| `/cmux:mo <file>` | Markdownファイルをブラウザプレビュー |
| `/cmux:open <target>` | URL/プリセット/local:pathをブラウザで開く |

## プリセット設定

`presets.yaml` でURLプリセットを定義できます。

```yaml
presets:
  dashboard: "http://localhost:3000/dashboard"
  docs: "https://docs.example.com"

local:
  port: 3000  # local:path 形式のデフォルトポート
```

使用例:
- `/cmux:open dashboard` → プリセットURLを開く
- `/cmux:open local:api/users` → http://localhost:3000/api/users を開く
- `/cmux:open https://example.com` → URLを直接開く

## セットアップ

```bash
# PATHを通す or シンボリックリンク作成
ln -sf ~/dev/projects/dotfiles/packages/cmux/scripts/cmux-difit.sh ~/bin/cmux-difit
ln -sf ~/dev/projects/dotfiles/packages/cmux/scripts/cmux-mo.sh ~/bin/cmux-mo
ln -sf ~/dev/projects/dotfiles/packages/cmux/scripts/cmux-open.sh ~/bin/cmux-open
```

## 参考

- [difit](https://github.com/yoshiko-pg/difit)
- [mo](https://github.com/k1LoW/mo)
- [cmux連携スクリプト by azu](https://gist.github.com/azu/cef84c98aeef832d43dfb640c7e321f5)
