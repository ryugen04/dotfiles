-- core/options.lua
local env = require('core.env')

local function setup()
  -- グローバルオプション
  local options = {
    -- 分割方向
    splitright = true,
    splitbelow = true,
    equalalways = false,  -- 新しいウィンドウ開いても他のウィンドウをリサイズしない

    -- システム連携
    clipboard = 'unnamedplus',
    mouse = 'a',

    -- 検索設定
    hlsearch = true,
    ignorecase = true,
    smartcase = true,
    wrapscan = true,

    -- 表示設定
    pumheight = 10,
    showmatch = true,
    matchtime = 1,
    showcmd = false,
    termguicolors = true,

    -- カーソル設定
    whichwrap = 'b,s,h,l,<,>,[,]',
    guicursor = vim.o.guicursor .. ',a:blinkon0',

    -- ファイル設定
    encoding = 'utf-8',
    fileencoding = 'utf-8',
    undodir = vim.fn.stdpath('state') .. '/backup',
    breakindent = true,
    -- タイムアウト設定
    ttimeout = true,
    ttimeoutlen = 50,
    timeout = true,
    timeoutlen = 1000,
  }
  

  -- ウィンドウローカルオプション
  local window_options = {
    cursorline = true,
    signcolumn = 'yes',
    number = true,
    relativenumber = true,
    foldmethod = 'marker',
    -- レンダリング最適化
    lazyredraw = true, -- マクロ実行中など画面描画を遅延
    ttyfast = true,    -- 高速ターミナル接続を想定
  }

  -- バッファローカルオプション
  local buffer_options = {
    autoindent = true,
    smartindent = true,
    tabstop = 2,
    shiftwidth = 2,
    expandtab = true,
    undofile = true,
    swapfile = false
  }

  -- オプションの適用
  for name, value in pairs(options) do
    vim.opt[name] = value
  end

  for name, value in pairs(window_options) do
    vim.opt[name] = value -- vim.optを使用することで、より安全に設定
  end

  for name, value in pairs(buffer_options) do
    vim.opt[name] = value
  end

  -- undoディレクトリの作成
  local undodir = vim.fn.stdpath('state') .. '/backup' -- 直接パスを使用
  if vim.fn.isdirectory(undodir) == 0 then
    vim.fn.mkdir(undodir, "p")
  end

  -- 環境依存の設定
  if env.is_windows() then
    -- Windowsの場合の特別な設定
    vim.opt.shellslash = true
  end

  -- runtimepathの設定
  vim.opt.runtimepath:append(vim.fn.expand('~/.vim'))
end

setup()

return {
  setup = setup
}
