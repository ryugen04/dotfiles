return {
  {
    'EdenEast/nightfox.nvim',
    lazy = false,
    priority = 1000,
    cond = not env.is_vscode(),
    config = function()

  require('nightfox').setup({
    options = {
      transparent=true,
      styles = {
        comments = "italic",
        keywords = "bold",
        types = "italic,bold",
      },
      inverse = {
        match_paren = true,
        visual = true,
        search = true,
      },
    },
    groups = {
      all = {
        -- カスタムハイライトグループの設定
        CursorLine = { bg = "bg2" },
      }
    }
  })
  vim.cmd("colorscheme nightfox")

    end,
    doc = "メインのカラースキーム"
  },

}
