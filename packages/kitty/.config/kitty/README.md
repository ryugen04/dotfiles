# Kitty Terminal 設定

## ペイン・ウィンドウ移動の仕組み

### 概要

`Ctrl+h/j/k/l` でkittyペインとneovim分割ウィンドウをシームレスに移動できる。neovim内では内部の分割を移動し、端に到達するとkittyペインへ移動する。

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                        Kitty Terminal                        │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │     Kitty Pane 1    │    │        Kitty Pane 2         │ │
│  │                     │    │  ┌─────────┬─────────────┐  │ │
│  │    (shell, etc.)    │◄───┼──┤  nvim   │    nvim     │  │ │
│  │                     │    │  │ split 1 │   split 2   │  │ │
│  │                     │    │  └─────────┴─────────────┘  │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Ctrl+h: nvim split 2 → nvim split 1 → Kitty Pane 1
Ctrl+l: Kitty Pane 1 → nvim split 1 → nvim split 2
```

### 実装方式: vim-kitty-navigator + pass_keys.py

kitty側でプロセスを検出し、neovimならキーをパススルー、それ以外ならペイン移動を実行するアプローチ。

### 処理フロー

```
Ctrl+h/j/k/l キー押下
        │
        ▼
┌───────────────────────────────┐
│  kitty: pass_keys.py kitten   │
│  フォアグラウンドプロセス確認  │
└───────────────┬───────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
   [neovim検出]    [その他のプロセス]
        │               │
        ▼               ▼
┌───────────────┐ ┌─────────────────┐
│キーをneovimに │ │neighboring_window│
│  パススルー   │ │   コマンド実行  │
└───────┬───────┘ └─────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  neovim: vim-kitty-navigator  │
│  内部ウィンドウ移動を試行     │
└───────────────┬───────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
  [移動可能]      [端に到達]
        │               │
        ▼               ▼
┌───────────────┐ ┌─────────────────┐
│ neovim内で    │ │ kittyへ移動指示 │
│ ウィンドウ移動│ │ (kitten経由)    │
└───────────────┘ └─────────────────┘
```

### 構成ファイル

| ファイル | 役割 |
|---------|------|
| `kittens/pass_keys.py` | neovimプロセス検出、キーパススルー判定 |
| `kittens/get_layout.py` | 現在のレイアウト情報取得 |
| `kitty.conf` | キーマッピング定義 |
| `nvim: vim-kitty-navigator` | neovim側のナビゲーション処理 |

### pass_keys.py の動作

1. `is_window_vim()` でフォアグラウンドプロセスのコマンドラインを正規表現で検査
2. `n?vim` パターンにマッチすればneovimと判定
3. neovimの場合: キーをエンコードして子プロセスに送信
4. それ以外: `neighboring_window` で隣接ペインに移動

### キーマッピング

```conf
# kitty.conf
map ctrl+h kitten kittens/pass_keys.py left   ctrl+h
map ctrl+j kitten kittens/pass_keys.py bottom ctrl+j
map ctrl+k kitten kittens/pass_keys.py top    ctrl+k
map ctrl+l kitten kittens/pass_keys.py right  ctrl+l
```

### neovim側の設定

```lua
-- plugins/configs/editor/kitty-navigator.lua
{
  'knubie/vim-kitty-navigator',
  lazy = false,
  init = function()
    vim.g.kitty_navigator_password = "claude-dev"
  end,
}
```

プラグインが提供するコマンド:
- `KittyNavigateLeft`
- `KittyNavigateDown`
- `KittyNavigateUp`
- `KittyNavigateRight`

### リモートコントロール設定

kitty.confでリモートコントロールを有効化:

```conf
allow_remote_control password
listen_on unix:/tmp/kitty-socket-{kitty_pid}
remote_control_password "claude-dev" get-text ls launch send-text focus-window focus-tab
```

neovimプラグインは `kitty_navigator_password` を使用してkittyと通信する。

## キーバインド一覧

### ペイン操作

| キー | 動作 |
|------|------|
| `Ctrl+h/j/k/l` | ペイン移動（neovim連携） |
| `Ctrl+a > h/j/k/l` | ペイン移動（リーダーキー版） |
| `Ctrl+a > -` | 縦分割 |
| `Ctrl+a > /` | 横分割 |
| `Ctrl+a > q` | ペインを閉じる |
| `Ctrl+a > w` | ペインリサイズモード |

### タブ操作

| キー | 動作 |
|------|------|
| `Ctrl+,` | 前のタブ |
| `Ctrl+.` | 次のタブ |
| `Ctrl+a > t` | 新規タブ |
| `Ctrl+a > x` | タブを閉じる |
| `Ctrl+a > r` | タブ名変更 |
| `Ctrl+a > 1-9` | タブ番号で移動 |

## 参考

- [vim-kitty-navigator](https://github.com/knubie/vim-kitty-navigator)
- [Kitty Remote Control](https://sw.kovidgoyal.net/kitty/remote-control/)
