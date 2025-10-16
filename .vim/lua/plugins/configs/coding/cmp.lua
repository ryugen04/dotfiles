return {
  -- 補完
  -- TODO: add luasnip and c-y mapping
  {
    'onsails/lspkind.nvim',
    cond = not is_vscode,
  },
  {
    'hrsh7th/nvim-cmp',
    cond = not env.is_vscode(),
    config = function()
      local cmp = require('cmp')
      local lspkind = require('lspkind')

      cmp.setup({
        snippet = {
          expand = function(args)
            vim.fn["vsnip#anonymous"](args.body)
          end,
        },

        -- パフォーマンス最適化
        performance = {
          debounce = 150,              -- 入力後の待機時間（デフォルト60ms → 150ms）
          throttle = 30,               -- 補完候補の更新頻度制限
          fetching_timeout = 500,      -- 補完取得のタイムアウト
          max_view_entries = 50,       -- 表示する補完候補の最大数（デフォルト200 → 50）
        },

        window = {
          completion = cmp.config.window.bordered(),
          documentation = cmp.config.window.bordered(),
        },

        mapping = cmp.mapping.preset.insert({
          ['<Down>'] = cmp.mapping.select_next_item(),
          ['<Up>'] = cmp.mapping.select_prev_item(),
          ['<C-d>'] = cmp.mapping.scroll_docs(-4),
          ['<C-u>'] = cmp.mapping.scroll_docs(4),
          ['<C-Tab>'] = cmp.mapping.complete(),
          ['<Esc>'] = cmp.mapping.abort(),
          ['<CR>'] = cmp.mapping.confirm({ select = true }),
        }),

        sources = cmp.config.sources({
          { name = 'nvim_lsp', priority = 100 },
          { name = 'vsnip', priority = 90 },
          { name = 'path', priority = 80 },
        }, {
          { name = 'buffer', keyword_length = 3, max_item_count = 5 },  -- バッファ補完の候補数を制限
          { name = 'calc', keyword_length = 2, max_item_count = 5 },
          { name = 'emoji', keyword_length = 2, max_item_count = 10 },
        }),

        formatting = {
          format = lspkind.cmp_format({
            mode = 'symbol_text',
            maxwidth = 50,
            ellipsis_char = '...',
            before = function(entry, vim_item)
              vim_item.menu = ({
                nvim_lsp = '[LSP]',
                vsnip = '[Snippet]',
                buffer = '[Buffer]',
                path = '[Path]'
              })[entry.source.name]
              return vim_item
            end
          })
        }
      })

      -- コマンドライン用の設定
      cmp.setup.cmdline(':', {
        mapping = cmp.mapping.preset.cmdline(),
        sources = cmp.config.sources({
          { name = 'path' }
        }, {
          { name = 'cmdline' }
        })
      })

      -- 検索用の設定
      cmp.setup.cmdline({ '/', '?' }, {
        mapping = cmp.mapping.preset.cmdline(),
        sources = {
          { name = 'buffer' }
        }
      })
    end,
    dependencies = {
      'hrsh7th/cmp-nvim-lsp',
      'hrsh7th/cmp-buffer',
      'hrsh7th/cmp-path',
      'hrsh7th/cmp-vsnip',
      'hrsh7th/cmp-cmdline',
      'hrsh7th/cmp-calc',
      'hrsh7th/cmp-emoji',
    },
    doc = "補完エンジン"
  },
}
