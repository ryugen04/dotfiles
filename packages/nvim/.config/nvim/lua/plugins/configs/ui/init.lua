return {
  {
    'petertriho/nvim-scrollbar',
    cond = not env.is_vscode(),
    -- config = function() require('plugins.configs.ui.scrollbar').setup() end,
    doc = "スクロールバー"
  },
  {
    'norcalli/nvim-colorizer.lua',
    -- config = function() require('plugins.configs.ui.colorizer').setup() end,
    doc = "カラーコードのハイライト"
  },
  {
    'simeji/winresizer',
    -- config = function() require('plugins.configs.ui.colorizer').setup() end,
    doc = "ウィンドウのリサイズ"
  },
}
