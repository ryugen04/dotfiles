return {
  -- Kotlin Language Server
  {
    'neovim/nvim-lspconfig',
    cond = not env.is_vscode(),
    event = { "BufReadPre *.kt", "BufNewFile *.kt" },
    ft = 'kotlin',
    config = function()
      local lspconfig = require('lspconfig')
      local capabilities = vim.lsp.protocol.make_client_capabilities()
      capabilities.textDocument.completion.completionItem.snippetSupport = true

      lspconfig.kotlin_language_server.setup({
        capabilities = capabilities,
        filetypes = { "kotlin" },
        root_dir = lspconfig.util.root_pattern(
          "settings.gradle.kts",
          "settings.gradle",
          "build.gradle.kts",
          "build.gradle",
          ".git"
        ),
        single_file_support = true,
        on_attach = function(client, bufnr)
          -- 診断を明示的に有効化
          vim.diagnostic.enable(bufnr)

          -- LSP基本キーマップ
          local function buf_map(mode, lhs, rhs, desc)
            vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, desc = desc, silent = true })
          end

          buf_map('n', 'gD', vim.lsp.buf.declaration, 'Go to declaration')
          buf_map('n', 'gd', vim.lsp.buf.definition, 'Go to definition')
          buf_map('n', 'K', vim.lsp.buf.hover, 'Hover documentation')
          buf_map('n', 'gi', vim.lsp.buf.implementation, 'Go to implementation')
          buf_map('n', '<leader>rn', vim.lsp.buf.rename, 'Rename')
          buf_map('n', '<leader>ca', vim.lsp.buf.code_action, 'Code action')
          buf_map('n', 'gr', vim.lsp.buf.references, 'References')
          buf_map('n', '[d', vim.diagnostic.goto_prev, 'Previous diagnostic')
          buf_map('n', ']d', vim.diagnostic.goto_next, 'Next diagnostic')
          buf_map('n', '<leader>e', vim.diagnostic.open_float, 'Show diagnostic')

          -- 診断を手動で確認するキーマップ
          buf_map('n', '<leader>dd', function()
            local diags = vim.diagnostic.get(bufnr)
            vim.notify("Diagnostics count: " .. #diags, vim.log.levels.INFO)
            if #diags > 0 then
              for _, d in ipairs(diags) do
                print(string.format("[%s] %s", d.severity, d.message))
              end
            end
          end, 'Show all diagnostics')

          -- Detekt実行キーマップ
          buf_map('n', '<leader>kd', function()
            vim.cmd('split | terminal ./gradlew detekt')
          end, 'Run detekt')

          buf_map('n', '<leader>kf', function()
            vim.cmd('split | terminal ./gradlew detekt --auto-correct')
            -- 実行後にファイルを再読み込み
            vim.defer_fn(function()
              vim.cmd('checktime')
            end, 2000)
          end, 'Format with detekt')
        end,
        settings = {
          kotlin = {
            compiler = {
              jvm = {
                target = "21"
              }
            }
          }
        }
      })

      -- Kotlinファイルを開いたときに確実にLSPをアタッチ
      vim.api.nvim_create_autocmd("FileType", {
        pattern = "kotlin",
        callback = function()
          local bufnr = vim.api.nvim_get_current_buf()
          -- 既にLSPがアタッチされているか確認
          local clients = vim.lsp.get_clients({ bufnr = bufnr })
          local has_kotlin_lsp = false
          for _, client in ipairs(clients) do
            if client.name == "kotlin_language_server" then
              has_kotlin_lsp = true
              break
            end
          end

          -- アタッチされていない場合は起動
          if not has_kotlin_lsp then
            vim.cmd('LspStart kotlin_language_server')
          end
        end,
        desc = "Auto-attach Kotlin LSP"
      })
    end
  },
  -- Kotlinシンタックスハイライト
  {
    'udalov/kotlin-vim',
    cond = not env.is_vscode(),
    ft = { 'kotlin' }
  }
}
