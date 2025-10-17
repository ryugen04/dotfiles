local env = require('core.env')

return {
  -- スニペットエンジン
  {
    'L3MON4D3/LuaSnip',
    cond = not env.is_vscode(),
    version = 'v2.*',
    build = 'make install_jsregexp',
    dependencies = {
      'rafamadriz/friendly-snippets',
    },
    config = function()
      local ls = require('luasnip')

      -- 基本設定
      ls.setup({
        history = true,
        updateevents = 'TextChanged,TextChangedI',
        enable_autosnippets = true,
        ext_opts = {
          [require('luasnip.util.types').choiceNode] = {
            active = {
              virt_text = { { '●', 'GruvboxOrange' } },
            },
          },
        },
      })

      -- friendly-snippetsを読み込み
      require('luasnip.loaders.from_vscode').lazy_load()

      -- カスタムスニペットを読み込み
      require('luasnip.loaders.from_lua').load({
        paths = { vim.fn.stdpath('config') .. '/snippets' }
      })

      -- LuaSnipEditコマンドを作成
      vim.api.nvim_create_user_command(
        'LuaSnipEdit',
        ':lua require("luasnip.loaders").edit_snippet_files()',
        {}
      )

      -- キーマップ設定
      vim.keymap.set({ 'i', 's' }, '<C-j>', function()
        if ls.expand_or_jumpable() then
          ls.expand_or_jump()
        end
      end, { silent = true, desc = 'LuaSnip: 展開またはジャンプ' })

      vim.keymap.set({ 'i', 's' }, '<C-k>', function()
        if ls.jumpable(-1) then
          ls.jump(-1)
        end
      end, { silent = true, desc = 'LuaSnip: 前のジャンプポイントへ' })

      vim.keymap.set('i', '<C-l>', function()
        if ls.choice_active() then
          ls.change_choice(1)
        end
      end, { silent = true, desc = 'LuaSnip: 選択肢を変更' })
    end,
  },
}
