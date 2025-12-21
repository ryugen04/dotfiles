return {
  'knubie/vim-kitty-navigator',
  lazy = false,
  init = function()
    -- kittyリモートコントロール用パスワード（kitty.confで設定した値と一致させる）
    vim.g.kitty_navigator_password = "claude-dev"
    -- デフォルトのマッピングを使用（<C-h>, <C-j>, <C-k>, <C-l>）
    vim.g.kitty_navigator_no_mappings = 0
  end,
}
