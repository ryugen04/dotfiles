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
        },
        automatic_installation = true  -- 必要に応じて自動インストール
      })

      local capabilities = vim.lsp.protocol.make_client_capabilities()
      capabilities.textDocument.completion.completionItem.snippetSupport = true

      -- 公式Kotlin LSPの設定
      local lspconfig = require('lspconfig')
      if not lspconfig.configs.kotlin_official_lsp then
        lspconfig.configs.kotlin_official_lsp = {
          default_config = {
            cmd = { 
              "/home/glaucus03/dev/projects/dotfiles/lib/kotlin-lsp.sh"
            },
            filetypes = { "kotlin" },
            root_dir = require('lspconfig.util').root_pattern(
              "build.gradle", 
              "build.gradle.kts", 
              "settings.gradle",
              "settings.gradle.kts",
              ".git"
            ),
            settings = {
              kotlin = {
                -- 必要に応じて設定を追加
              }
            },
            init_options = {
              -- storagePathを明示的に設定（セッション管理の問題回避）
              storagePath = vim.fn.stdpath("cache") .. "/kotlin_official_lsp"
            }
          },
          docs = {
            description = "Official Kotlin Language Server from JetBrains",
            default_config = {
              root_dir = "root_pattern('build.gradle', 'build.gradle.kts', 'settings.gradle', '.git')"
            }
          }
        }
      end

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
        -- 公式Kotlin LSPの設定を追加
        kotlin_official_lsp = {
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
        ["kotlin_language_server"] = true, -- 公式LSPを使用するため除外
      }

      require('mason-lspconfig').setup_handlers({
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
          require('lspconfig')[server_name].setup(
            config
          )
        end
      })

      -- 公式Kotlin LSPのセットアップ（masonの管理外）
      -- setup()関数が定義されているか確認してから実行
      local kotlin_lsp = lspconfig.kotlin_official_lsp
      if kotlin_lsp and type(kotlin_lsp.setup) == "function" then
        kotlin_lsp.setup(
          vim.tbl_deep_extend(
            "force",
            make_default_config(),
            server_settings.kotlin_official_lsp or {}
          )
        )
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
