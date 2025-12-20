return {
  -- ナビゲーション
  {
    'rhysd/clever-f.vim',
    doc = "f/t検索の拡張"
  },

  -- 自動括弧補完
  {
    'windwp/nvim-autopairs',
    event = 'InsertEnter',
    config = function()
      require('nvim-autopairs').setup({
        -- 特定のファイルタイプで無効化
        disable_filetype = { 'TelescopePrompt', 'vim' },
        -- 括弧の前にスペースがあるときのチェック
        check_ts = true,
        -- Treesitterを使用した括弧のペアリング
        ts_config = {
          lua = { 'string' },
          javascript = { 'template_string' },
          java = false,
        },
      })
    end,
  },
}
