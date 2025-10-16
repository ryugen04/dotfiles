return {
  -- Kotlin Language Server (コミュニティ版)
  {
    'neovim/nvim-lspconfig',
    cond = not env.is_vscode(),
    ft = 'kotlin',
    config = function()
      local lspconfig = require('lspconfig')
      local capabilities = vim.lsp.protocol.make_client_capabilities()
      capabilities.textDocument.completion.completionItem.snippetSupport = true

      lspconfig.kotlin_language_server.setup({
        capabilities = capabilities,
        cmd = { "kotlin-language-server" },
        filetypes = { "kotlin" },
        root_dir = lspconfig.util.root_pattern(
          "settings.gradle",
          "settings.gradle.kts",
          "build.gradle",
          "build.gradle.kts",
          "pom.xml",
          "build.xml",
          ".git"
        ),
        init_options = {
          -- キャッシュパスを指定してパフォーマンス向上
          storagePath = vim.fn.stdpath("cache") .. "/kotlin_language_server"
        },
        settings = {
          kotlin = {
            compiler = {
              jvm = {
                target = "17"
              }
            }
          }
        }
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
