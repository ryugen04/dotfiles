return {
  -- Flutter/Dart
  {
    'akinsho/flutter-tools.nvim',
    cond = not env.is_vscode(),
    lazy = true,
    dependencies = {
      'nvim-lua/plenary.nvim',
      'stevearc/dressing.nvim',
    },
    config = function()
      require("flutter-tools").setup {
        ui = {
          border = "none",
        },
        decorations = {
          statusline = {
            app_version = false,
            device = false,
          }
        },
        debugger = {
          enabled = false,
          run_via_dap = false,
        },
        fvm = true,
        widget_guides = {
          enabled = true,
        },
        closing_tags = {
          highlight = "ClosingTags",
          prefix = " ",
          enabled = true
        },
        dev_log = {
          enabled = true,
          open_cmd = "tabedit",
        },
        dev_tools = {
          autostart = false,
          auto_open_browser = false,
        },
        outline = {
          open_cmd = "30vnew",
          auto_open = false
        },
        lsp = {
          on_attach = function(client, bufnr)
            vim.cmd [[hi FlutterWidgetGuides ctermfg=237 guifg=#33374c]]
            vim.cmd [[hi ClosingTags ctermfg=244 guifg=#8389a3]]
            on_attach(client, bufnr)
          end,
          capabilities = capabilities,
          settings = {
            showTodos = false,
            completeFunctionCalls = true,
            analysisExcludedFolders = {
              "~/.pub-cache",
              "~/fvm"
            }
          }
        }
      }
    end,
    doc = "Flutter開発支援"
  },
}
