return {
  {
    'MeanderingProgrammer/render-markdown.nvim',
    dependencies = { 'nvim-treesitter/nvim-treesitter', 'echasnovski/mini.nvim' }, -- if you use the mini.nvim suite
    opts = {
      heading = {
        width = "block",
        left_pad = 0,
        right_pad = 4,
        icons = {},
      },
      checkbox = {
        checked = { scope_highlight = "@markup.strikethrough" },
        custom = {
          -- デフォルトの`[-]`であるtodoは削除
          todo = { raw = "", rendered = "", highlight = "" },
          canceled = {
            raw = "[-]",
            rendered = "󱘹",
            scope_highlight = "@markup.strikethrough",
          },
        },
      },
    },
  },
  {
    "iamcco/markdown-preview.nvim",
    cmd = { "MarkdownPreviewToggle", "MarkdownPreview", "MarkdownPreviewStop" },
    ft = { "markdown" },
    build = function() vim.fn["mkdp#util#install"]() end,
    config = function()
      -- バッファを切り替えてもプレビューを閉じない
      vim.g.mkdp_auto_close = 0
      -- 他の便利な設定
      vim.g.mkdp_refresh_slow = 0 -- リアルタイムでプレビュー更新
      vim.g.mkdp_open_to_the_world = 0 -- ローカルホストのみ
      vim.g.mkdp_browser = '' -- デフォルトブラウザを使用

      -- Markdownバッファに入った時、プレビューが開いていれば自動的に切り替える
      vim.api.nvim_create_autocmd("BufEnter", {
        pattern = "*.md",
        callback = function()
          -- プレビューが開いているかチェック
          if vim.fn.exists('g:mkdp_preview_url') == 1 and vim.g.mkdp_preview_url ~= '' then
            -- 既にプレビューが開いている場合、現在のバッファで再起動
            vim.cmd('MarkdownPreviewStop')
            vim.defer_fn(function()
              vim.cmd('MarkdownPreview')
            end, 100) -- 少し遅延させて確実に切り替え
          end
        end,
      })
    end,
  }
}
