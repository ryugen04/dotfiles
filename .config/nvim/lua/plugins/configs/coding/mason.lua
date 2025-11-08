return {
  -- LSP
  {
    'williamboman/mason.nvim',
    cond = not env.is_vscode(),
    event = "VeryLazy",  -- 遅延読み込みで起動時間を短縮
    config = function()
      require('mason').setup({
        ui = {
          check_outdated_packages_on_open = true,
          border = 'rounded',
          icons = {
            package_installed = "✓",
            package_pending = "➜",
            package_uninstalled = "✗"
          }
        }
      })

      require('mason-lspconfig').setup({
        ensure_installed = {
          -- 頻繁に使用する言語のみに限定（起動時間短縮のため）
          "lua_ls",
          "bashls",
          "pyright",
          -- Kotlin: JetBrains公式kotlin-lspはHomebrewでインストール
        },
        automatic_installation = true  -- 必要に応じて自動インストール
      })

      local capabilities = vim.lsp.protocol.make_client_capabilities()
      capabilities.textDocument.completion.completionItem.snippetSupport = true

      -- LSPサーバー固有の設定
      --
      local server_settings = {
        pyright = {
          settings = {
            python = {
              extraPaths = { "." },
              venvPaths = '.',
              pythonPath = "./.venv/bin/python",
              analysis = {
                typeCheckingMode = "basic",
                reportOptionalSubscript = "none",
                reportAttributeAccessIssue = "none",
                reportOptionalMemberAccess = false,
                reportReturnType = "none",
                reportGeneralTypeIssues = "none",
                reportMissingImports = "none",    -- importエラーの抑制
                reportUnknownMemberType = "none", -- メンバーの型エラーの抑制
                useLibraryCodeForTypes = true,
                autoSearchPaths = true,
              }
            }
          }
        },
        ruby_lsp = {
          enabled = true,
        },
        rubocop = {
          -- If Solargraph and Rubocop are both enabled as an LSP,
          -- diagnostics will be duplicated because Solargraph
          -- already calls Rubocop if it is installed
          enabled = true,
        },
      }

      -- デフォルトのLSP設定を生成する関数
      local function make_default_config()
        return {
          capabilities = capabilities
        }
      end

      -- 除外するLSPサーバーのリスト
      local excluded_servers = {
        ["jdtls"] = true, -- null-lsから起動するため除外
        -- kotlin-lspはkotlin.luaから起動（Homebrew経由でインストール）
      }

      local ok, mason_lspconfig = pcall(require, 'mason-lspconfig')
      if ok and mason_lspconfig.setup_handlers then
        mason_lspconfig.setup_handlers({
          function(server_name)
            if excluded_servers[server_name] then
              return
            end
            local config = vim.tbl_deep_extend(
              "force",
              make_default_config(),
              server_settings[server_name] or {}
            )
            -- jdtls launch from null-ls
            -- Use new vim.lsp.config API for nvim 0.11+
            if vim.lsp.config then
              vim.lsp.config[server_name] = config
              vim.lsp.enable(server_name)
            else
              -- Fallback for older nvim versions
              require('lspconfig')[server_name].setup(config)
            end
          end
        })
      elseif not ok then
        vim.notify('Failed to load mason-lspconfig', vim.log.levels.ERROR)
      end
    end,
    dependencies = {
      'williamboman/mason-lspconfig.nvim',
      'neovim/nvim-lspconfig',
    },
    doc = "LSPマネージャー"
  },
  {
    "tamago324/nlsp-settings.nvim",

    cond = not env.is_vscode(),
    cmd = "LspSettings",
    lazy = true
  },
}
