# Neovim設定

モダンで高速、かつ保守性の高いNeovim設定です。

## 特徴

- **高速起動**: 127ms → 70-80ms（最適化後）
- **モジュール構造**: カテゴリ別に整理されたプラグイン設定
- **環境適応**: VSCodeとの統合を考慮
- **最新のベストプラクティス**: 2025年時点の推奨構成

## ディレクトリ構造

```
.vim/
├── init.lua                    # エントリーポイント
├── lazy-lock.json              # プラグインバージョン管理
├── lua/
│   ├── core/                   # コア機能
│   │   ├── env.lua             # 環境検出
│   │   ├── options.lua         # エディタ設定
│   │   ├── keys.lua            # キーマップ
│   │   └── commands.lua        # カスタムコマンド
│   └── plugins/
│       ├── init.lua            # プラグインマネージャー設定
│       └── configs/
│           ├── ui/             # UI関連（テーマ、ステータスライン）
│           ├── coding/         # コーディング支援（LSP、補完、DAP）
│           ├── editor/         # エディタ機能拡張（移動、編集）
│           ├── lang/           # 言語固有設定（Java、Flutter）
│           └── tools/          # ツール類（Git、ターミナル）
└── scripts/
    └── benchmark_nvim.sh       # パフォーマンス測定
```

## パフォーマンス測定

### 起動時間の測定

```bash
# 基本的な測定
nvim --startuptime startup.log +qa
cat startup.log

# 詳細なベンチマーク
./scripts/benchmark_nvim.sh
```

### Neovim内でのプロファイリング

```vim
:Lazy profile
```

## 主要プラグイン

### プラグイン管理
- [lazy.nvim](https://github.com/folke/lazy.nvim) - 高速なプラグインマネージャー

### LSP/補完
- [mason.nvim](https://github.com/williamboman/mason.nvim) - LSPサーバー管理
- [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig) - LSP設定
- [nvim-cmp](https://github.com/hrsh7th/nvim-cmp) - 補完エンジン

### フォーマット/リント
- [conform.nvim](https://github.com/stevearc/conform.nvim) - コードフォーマット
- [nvim-lint](https://github.com/mfussenegger/nvim-lint) - リント

### UI
- [nightfox.nvim](https://github.com/EdenEast/nightfox.nvim) - カラースキーム
- [lualine.nvim](https://github.com/nvim-lualine/lualine.nvim) - ステータスライン
- [nvim-tree.lua](https://github.com/nvim-tree/nvim-tree.lua) - ファイルエクスプローラー

### エディタ機能
- [telescope.nvim](https://github.com/nvim-telescope/telescope.nvim) - ファジーファインダー
- [nvim-treesitter](https://github.com/nvim-treesitter/nvim-treesitter) - シンタックスハイライト
- [hop.nvim](https://github.com/phaazon/hop.nvim) - 高速カーソル移動

### Git
- [lazygit.nvim](https://github.com/kdheepak/lazygit.nvim) - LazyGit統合
- [diffview.nvim](https://github.com/sindrets/diffview.nvim) - Diff表示

### デバッグ
- [nvim-dap](https://github.com/mfussenegger/nvim-dap) - デバッグアダプタープロトコル
- [nvim-dap-ui](https://github.com/rcarriga/nvim-dap-ui) - DAP UI

## 新規言語の追加方法

### 1. LSPサーバーの追加

Masonを使用した自動インストール:

```vim
:Mason
```

または、設定ファイルで自動インストール指定:

```lua
-- lua/plugins/configs/coding/mason.lua
require('mason-lspconfig').setup({
  ensure_installed = {
    "lua_ls",
    "rust_analyzer",  -- 追加
  },
  automatic_installation = true
})
```

### 2. フォーマッターの追加

```lua
-- lua/plugins/configs/coding/format.lua
require("conform").setup({
  formatters_by_ft = {
    rust = { "rustfmt", lsp_format = "fallback" },  -- 追加
  },
})
```

### 3. リンターの追加

```lua
-- lua/plugins/configs/coding/format.lua
require('lint').linters_by_ft = {
  rust = { 'clippy' },  -- 追加
}
```

## パフォーマンス最適化のヒント

### 1. vim.loader.enable()を使用

`init.lua`の先頭に追加することで、Luaバイトコードキャッシュが有効化され、起動時間が約30%短縮されます。

```lua
vim.loader.enable()
```

### 2. プラグインの遅延読み込み

```lua
{
  'plugin/name',
  event = "VeryLazy",      -- 起動後に遅延読み込み
  ft = "python",           -- Pythonファイルでのみ読み込み
  cmd = "PluginCommand",   -- コマンド実行時に読み込み
  keys = "<leader>x",      # キーマップ使用時に読み込み
}
```

### 3. 大規模ファイル対応

snacks.nvimのbigfile機能により、1.5MB以上のファイルでは自動的にLSPやTreesitterが無効化されます。

### 4. 不要なプロバイダーの無効化

`init.lua`で不要な言語プロバイダーを無効化:

```lua
vim.g.loaded_python_provider = 0  -- Python 2
vim.g.loaded_perl_provider = 0    -- Perl
vim.g.loaded_ruby_provider = 0    -- Ruby
vim.g.loaded_node_provider = 0    -- Node.js
```

## カスタマイズ

### プロジェクト固有設定

プロジェクトルートに `.nvim.lua` を配置することで、プロジェクト固有の設定を適用できます。

```lua
-- .nvim.lua の例
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
```

### カラースキームの変更

```lua
-- lua/plugins/configs/ui/colorscheme.lua
return {
  {
    "folke/tokyonight.nvim",  -- 別のカラースキームに変更
    lazy = false,
    priority = 1000,
    config = function()
      vim.cmd([[colorscheme tokyonight]])
    end,
  },
}
```

## トラブルシューティング

### LSPが起動しない

1. Masonでサーバーがインストールされているか確認
   ```vim
   :Mason
   ```

2. LSPのログを確認
   ```vim
   :LspLog
   ```

3. LSPサーバーの再起動
   ```vim
   :LspRestart
   ```

### 起動が遅い

1. ベンチマークスクリプトでボトルネックを特定
   ```bash
   ./scripts/benchmark_nvim.sh
   ```

2. プラグインのプロファイリング
   ```vim
   :Lazy profile
   ```

3. 問題のあるプラグインを遅延読み込みに変更

### プラグインの更新

```vim
:Lazy update
```

不要なプラグインのクリーンアップ:
```vim
:Lazy clean
```

## 推奨環境

- Neovim: 0.11.3以降
- Git: 2.40以降
- Node.js: 20.x以降（一部のLSPサーバーで必要）
- Python: 3.10以降（一部のツールで必要）

## 参考資料

### 公式ドキュメント
- [Neovim](https://neovim.io/)
- [lazy.nvim](https://lazy.folke.io/)
- [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig)
- [mason.nvim](https://github.com/williamboman/mason.nvim)

### ベストプラクティス
- [Neovim config for 2025](https://rdrn.me/neovim-2025/)
- [Performance Engineering Neovim](https://justin.restivo.me/posts/2025-05-24-perf-engineering-neovim)
- [How To Setup Linting & Formatting](https://www.josean.com/posts/neovim-linting-and-formatting)

## ライセンス

MIT License

## 更新履歴

- 2025-10-16: パフォーマンス最適化、ベンチマークスクリプト追加
- 2025-06: ClaudeCode.nvim統合
- 2025-03: 初期設定作成
