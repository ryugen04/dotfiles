-- snacks.nvim: 大規模ファイル対応
return {
  {
    "folke/snacks.nvim",
    priority = 1000,
    lazy = false,
    opts = {
      bigfile = {
        enabled = true,
        notify = true,  -- 大規模ファイル検出時に通知
        size = 1.5 * 1024 * 1024,  -- 1.5MB以上
        line_length = 1000,  -- 1行1000文字以上（ミニファイされたファイル）

        -- 大規模ファイルで無効化する機能
        setup = function(ctx)
          -- mini.animateを無効化
          vim.b.minianimate_disable = true

          -- シンタックスハイライトを基本的なもののみに変更
          vim.schedule(function()
            vim.bo[ctx.buf].syntax = vim.filetype.match({ buf = ctx.buf }) or ""
          end)
        end,
      },
    },
  },
}
