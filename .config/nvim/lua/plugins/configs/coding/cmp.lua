local env = require('core.env')

return {
  -- 補完エンジン
  {
    'saghen/blink.cmp',
    cond = not env.is_vscode(),
    version = '1.*',
    dependencies = {
      'rafamadriz/friendly-snippets',
      'L3MON4D3/LuaSnip',
    },
    opts = {
      -- キーマップ設定（nvim-cmpの設定を踏襲しつつカスタマイズ）
      keymap = {
        preset = 'none',
        ['<Down>'] = { 'select_next', 'fallback' },
        ['<Up>'] = { 'select_prev', 'fallback' },
        ['<C-d>'] = { 'scroll_documentation_up', 'fallback' },
        ['<C-u>'] = { 'scroll_documentation_down', 'fallback' },
        ['<C-Tab>'] = { 'show', 'fallback' },
        ['<C-space>'] = { 'show', 'show_documentation', 'hide_documentation' },
        ['<Esc>'] = { 'hide', 'fallback' },
        ['<Tab>'] = { 'accept', 'fallback' },
        ['<C-k>'] = { 'show_signature', 'hide_signature', 'fallback' },
        ['<C-n>'] = { 'select_next', 'fallback' },
        ['<C-p>'] = { 'select_prev', 'fallback' },
        ['<C-e>'] = { 'hide', 'fallback' },
      },

      appearance = {
        nerd_font_variant = 'mono',
      },

      completion = {
        -- ドキュメント表示設定
        documentation = {
          auto_show = true,
          auto_show_delay_ms = 200,
          window = {
            border = 'rounded',
          },
        },

        -- メニュー設定（nvim-cmpの枠線付きスタイルを踏襲）
        menu = {
          auto_show = true,
          border = 'rounded',
          draw = {
            columns = {
              { 'label',     'label_description', gap = 1 },
              { 'kind_icon', 'kind',              gap = 1 },
            },
          },
        },

        -- ゴーストテキスト有効化
        ghost_text = {
          enabled = true,
        },

        -- 補完候補の選択設定
        list = {
          selection = {
            preselect = true,
            auto_insert = true,
          },
        },
      },

      -- 補完ソース設定
      sources = {
        default = { 'lsp', 'path', 'snippets', 'buffer' },

        -- ソースごとの詳細設定
        providers = {
          lsp = {
            name = 'LSP',
            score_offset = 100,
            fallbacks = { 'buffer' },
          },
          path = {
            name = 'Path',
            score_offset = 80,
            opts = {
              trailing_slash = true,
              label_trailing_slash = true,
            },
          },
          snippets = {
            name = 'Snippet',
            score_offset = 90,
            opts = {
              friendly_snippets = true,
              search_paths = { vim.fn.stdpath('config') .. '/snippets' },
            },
          },
          buffer = {
            name = 'Buffer',
            score_offset = -3,
            min_keyword_length = 3,
            max_items = 5,
            opts = {
              -- 表示されているバッファのみから補完
              get_bufnrs = function()
                return vim
                    .iter(vim.api.nvim_list_wins())
                    :map(function(win) return vim.api.nvim_win_get_buf(win) end)
                    :filter(function(buf) return vim.bo[buf].buftype ~= 'nofile' end)
                    :totable()
              end,
            },
          },
        },
      },

      -- スニペット設定
      snippets = {
        preset = 'luasnip',
      },

      -- シグネチャヘルプ有効化
      signature = {
        enabled = true,
        window = {
          border = 'rounded',
        },
      },

      -- コマンドライン補完設定
      cmdline = {
        enabled = true,
        keymap = { preset = 'cmdline' },
        sources = { 'buffer', 'cmdline', 'path' },
        completion = {
          list = {
            selection = {
              preselect = true,
              auto_insert = true,
            },
          },
          menu = { auto_show = true },
          ghost_text = { enabled = true },
        },
      },

      -- Rust製fuzzyマッチャーを使用（パフォーマンス最適化）
      fuzzy = {
        implementation = 'prefer_rust_with_warning',
      },
    },
    opts_extend = { 'sources.default' },
  },
}
