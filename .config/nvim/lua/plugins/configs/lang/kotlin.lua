-- Kotlin開発環境設定
-- JetBrains公式kotlin-lspをベースとした環境構築
return {
  {
    'ryugen04/kotlin-extended-lsp.nvim',
    ft = 'kotlin',
    config = function()
      require('kotlin-extended-lsp').setup()

      -- which-key統合: Kotlinファイル用のキーバインディング
      local ok_wk, wk = pcall(require, 'which-key')
      if ok_wk then
        local ok_api, kotlin_api = pcall(require, 'kotlin-extended-lsp.api')
        if ok_api then
          -- Kotlinファイル用の<leader>lグループ設定
          wk.add({
            {
              mode = { "n", "v" },
              { "<leader>ld", function() kotlin_api.goto_definition() end,      desc = "Go to definition (定義へジャンプ)", buffer = 0 },
              { "<leader>lD", function() kotlin_api.goto_type_definition() end, desc = "Go to type definition (型定義へジャンプ)", buffer = 0 },
              -- 注: goto_implementation はkotlin-lspがサポートしていないため削除
              { "<leader>lr", function() vim.lsp.buf.references() end,          desc = "Show references (参照を表示)", buffer = 0 },
              { "<leader>lk", function() vim.lsp.buf.hover() end,               desc = "Hover info (ホバー情報)", buffer = 0 },
              { "<leader>lR", function() vim.lsp.buf.rename() end,              desc = "Rename (リネーム)", buffer = 0 },
              { "<leader>la", function() kotlin_api.code_actions() end,         desc = "Code action (コードアクション)", buffer = 0 },
            },
          })

          -- Kotlin固有の追加機能
          wk.add({
            { "<leader>lx", group = "Kotlin Extended (Kotlin拡張機能)" },
            {
              mode = { "n", "v" },
              { "<leader>lxd", function() kotlin_api.decompile() end,        desc = "Decompile (逆コンパイル)", buffer = 0 },
              { "<leader>lxo", function() kotlin_api.organize_imports() end, desc = "Organize imports (import整理)", buffer = 0 },
              { "<leader>lxf", function() kotlin_api.apply_fix() end,        desc = "Apply fix (修正を適用)", buffer = 0 },
              { "<leader>lxr", function() kotlin_api.refactor() end,         desc = "Refactor menu (リファクタリング)", buffer = 0 },
            },
          })

          -- テスト関連（既存の<leader>tグループに統合）
          wk.add({
            {
              mode = { "n", "v" },
              { "<leader>tt", function() kotlin_api.test_nearest() end,   desc = "Run nearest test (最寄りのテスト実行)", buffer = 0 },
              { "<leader>tf", function() kotlin_api.test_file() end,      desc = "Run file tests (ファイル内テスト実行)", buffer = 0 },
              { "<leader>ta", function() kotlin_api.test_all() end,       desc = "Run all tests (全テスト実行)", buffer = 0 },
            },
          })
        end
      end
    end
  } -- LSP設定（JetBrains公式kotlin-lsp）
  -- {
  --   'neovim/nvim-lspconfig',
  --   cond = not env.is_vscode(),
  --   ft = 'kotlin',
  --   config = function()
  --     local lspconfig = require('lspconfig')
  --     local lspconfig_configs = require('lspconfig.configs')
  --
  --     -- JetBrains公式kotlin-lspのカスタム設定
  --     -- Homebrewでインストール: brew install JetBrains/utils/kotlin-lsp
  --     if not lspconfig_configs.kotlin_lsp then
  --       lspconfig_configs.kotlin_lsp = {
  --         default_config = {
  --           cmd = { 'kotlin-lsp', '--stdio' },
  --           filetypes = { 'kotlin' },
  --           root_dir = lspconfig.util.root_pattern(
  --             'settings.gradle.kts',
  --             'settings.gradle',
  --             'build.gradle.kts',
  --             'build.gradle',
  --             'pom.xml',
  --             '.git'
  --           ),
  --           settings = {
  --             kotlin = {
  --               compiler = {
  --                 jvm = {
  --                   target = '21'
  --                 }
  --               },
  --               -- IntelliJ IDEA準拠の設定
  --               codeGeneration = {
  --                 useJavaStyleBraces = false,
  --               },
  --               completion = {
  --                 snippets = {
  --                   enabled = true
  --                 }
  --               },
  --               formatting = {
  --                 -- IntelliJ IDEAのデフォルト設定を使用
  --                 -- .editorconfigで詳細設定
  --                 enabled = true
  --               },
  --               diagnostics = {
  --                 enabled = true
  --               }
  --             }
  --           },
  --           capabilities = vim.lsp.protocol.make_client_capabilities(),
  --         }
  --       }
  --     end
  --
  --     -- kotlin-lspの起動
  --     lspconfig.kotlin_lsp.setup({
  --       capabilities = vim.lsp.protocol.make_client_capabilities(),
  --       on_attach = function(client, bufnr)
  --         -- LSP基本キーマップ
  --         local opts = { noremap = true, silent = true, buffer = bufnr }
  --         vim.keymap.set('n', 'gd', vim.lsp.buf.definition, opts)
  --         vim.keymap.set('n', 'gr', vim.lsp.buf.references, opts)
  --         vim.keymap.set('n', 'K', vim.lsp.buf.hover, opts)
  --         vim.keymap.set('n', '<leader>rn', vim.lsp.buf.rename, opts)
  --         vim.keymap.set('n', '<leader>ca', vim.lsp.buf.code_action, opts)
  --         vim.keymap.set('n', '<leader>e', vim.diagnostic.open_float, opts)
  --         vim.keymap.set('n', '[d', vim.diagnostic.goto_prev, opts)
  --         vim.keymap.set('n', ']d', vim.diagnostic.goto_next, opts)
  --
  --         -- フォーマット（IntelliJ IDEA準拠）
  --         if client.server_capabilities.documentFormattingProvider then
  --           vim.keymap.set('n', '<leader>lf', function()
  --             vim.lsp.buf.format({ async = true })
  --           end, opts)
  --         end
  --       end,
  --     })
  --   end
  -- },
  --
  -- -- シンタックスハイライト
  -- {
  --   'udalov/kotlin-vim',
  --   cond = not env.is_vscode(),
  --   ft = { 'kotlin' },
  --   config = function()
  --     -- Kotlinファイルタイプの追加設定
  --     vim.api.nvim_create_autocmd('BufRead', {
  --       pattern = '*.kt',
  --       callback = function()
  --         vim.bo.filetype = 'kotlin'
  --       end,
  --     })
  --   end
  -- },
  --
  -- -- Kotestテスト実行用キーマップ
  -- -- 注: neotest-kotlinアダプタはtest.luaで設定済み
  -- {
  --   'nvim-neotest/neotest',
  --   optional = true,
  --   ft = 'kotlin',
  --   keys = {
  --     {
  --       '<leader>tn',
  --       function()
  --         require('neotest').run.run()
  --       end,
  --       desc = 'Run nearest Kotlin test',
  --     },
  --     {
  --       '<leader>tf',
  --       function()
  --         require('neotest').run.run(vim.fn.expand('%'))
  --       end,
  --       desc = 'Run current Kotlin file tests',
  --     },
  --     {
  --       '<leader>ts',
  --       function()
  --         require('neotest').summary.toggle()
  --       end,
  --       desc = 'Toggle Kotlin test summary',
  --     },
  --     {
  --       '<leader>to',
  --       function()
  --         require('neotest').output.open({ enter = true })
  --       end,
  --       desc = 'Open Kotlin test output',
  --     },
  --   }
  -- },
  --
  -- -- デバッグ（DAP）
  -- {
  --   'mfussenegger/nvim-dap',
  --   optional = true,
  --   dependencies = {
  --     'Mgenuit/nvim-dap-kotlin',
  --   },
  --   ft = 'kotlin',
  --   config = function()
  --     -- nvim-dap-kotlinが自動的にkotlin-debug-adapterを設定
  --     -- 手動設定が必要な場合は以下を使用
  --     local dap = require('dap')
  --
  --     if not dap.adapters.kotlin then
  --       dap.adapters.kotlin = {
  --         type = 'executable',
  --         command = 'kotlin-debug-adapter',
  --         options = {
  --           auto_continue_if_many_stopped = false,
  --         }
  --       }
  --     end
  --
  --     if not dap.configurations.kotlin then
  --       dap.configurations.kotlin = {
  --         {
  --           type = 'kotlin',
  --           request = 'launch',
  --           name = 'Launch Kotlin Program',
  --           projectRoot = vim.fn.getcwd(),
  --           mainClass = function()
  --             return vim.fn.input('Main class (e.g., com.example.MainKt): ')
  --           end,
  --         },
  --         {
  --           type = 'kotlin',
  --           request = 'attach',
  --           name = 'Attach to Kotlin Process',
  --           hostName = 'localhost',
  --           port = 5005,
  --           timeout = 2000,
  --         },
  --         {
  --           type = 'kotlin',
  --           request = 'launch',
  --           name = 'Debug Kotest',
  --           projectRoot = vim.fn.getcwd(),
  --           mainClass = 'io.kotest.runner.console.KotestConsoleRunner',
  --           args = function()
  --             local test_class = vim.fn.expand('%:t:r')
  --             return { '--spec=' .. test_class }
  --           end,
  --         }
  --       }
  --     end
  --
  --   end
  -- },
  --
  -- -- Kotlin専用デバッグキーマップ
  -- {
  --   'mfussenegger/nvim-dap',
  --   optional = true,
  --   ft = 'kotlin',
  --   keys = {
  --     {
  --       '<leader>db',
  --       function()
  --         require('dap').toggle_breakpoint()
  --       end,
  --       desc = 'Toggle Kotlin breakpoint',
  --     },
  --     {
  --       '<leader>dc',
  --       function()
  --         require('dap').continue()
  --       end,
  --       desc = 'Continue Kotlin debugging',
  --     },
  --     {
  --       '<leader>ds',
  --       function()
  --         require('dap').step_over()
  --       end,
  --       desc = 'Step over in Kotlin debug',
  --     },
  --     {
  --       '<leader>di',
  --       function()
  --         require('dap').step_into()
  --       end,
  --       desc = 'Step into in Kotlin debug',
  --     },
  --   }
  -- },
  --
  -- -- Gradle統合ユーティリティ
  -- {
  --   'nvim-lua/plenary.nvim',
  --   optional = true,
  --   keys = {
  --     {
  --       '<leader>kg',
  --       function()
  --         local gradle_tasks = {
  --           'build',
  --           'clean',
  --           'test',
  --           'detekt',
  --           'ktlintFormat',
  --           'ktlintCheck',
  --         }
  --
  --         vim.ui.select(gradle_tasks, {
  --           prompt = 'Select Gradle task:',
  --         }, function(choice)
  --           if choice then
  --             vim.cmd('split | terminal ./gradlew ' .. choice)
  --           end
  --         end)
  --       end,
  --       desc = 'Run Gradle task',
  --       ft = 'kotlin',
  --     },
  --     {
  --       '<leader>kd',
  --       function()
  --         vim.cmd('split | terminal ./gradlew detekt')
  --       end,
  --       desc = 'Run Detekt analysis',
  --       ft = 'kotlin',
  --     },
  --     {
  --       '<leader>kf',
  --       function()
  --         vim.cmd('split | terminal ./gradlew ktlintFormat')
  --         vim.defer_fn(function()
  --           vim.cmd('checktime')
  --         end, 2000)
  --       end,
  --       desc = 'Format with ktlint (Gradle)',
  --       ft = 'kotlin',
  --     },
  --   }
  -- },
}
