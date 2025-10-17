return {
  {
    {
      "nvim-neotest/neotest",
      dependencies = {
        "nvim-neotest/nvim-nio",
        "nvim-lua/plenary.nvim",
        "antoinemadec/FixCursorHold.nvim",
        "nvim-treesitter/nvim-treesitter",
        "rcasia/neotest-java"
      },
      config = function()
        -- neotest設定
        require("neotest").setup({
          adapters = {
            require("neotest-java")({
              -- アダプタ固有の設定
              dap = {
                config = {
                  name = "Debug Java Test",
                  type = "java",
                  request = "launch",
                  -- JUnitプラットフォームを指定
                  mainClass = "org.junit.platform.console.ConsoleLauncher",
                  -- プロジェクトパスの設定
                  projectName = "java-demo",
                  -- クラスパスの設定
                  classPaths = { "${workspaceFolder}/target/test-classes", "${workspaceFolder}/target/classes" },
                  -- メソッド単位でのテスト実行を強制
                  args = {
                    "--select-method",
                    "${testClass}#${testMethod}",
                    "--disable-banner",
                    "-quiet"
                  },
                  -- ソースパスの設定
                  sourcePaths = { "${workspaceFolder}/src/test/java" },
                  -- ホットリロードの設定
                  hotcodereplace = "auto",
                  -- テストスコープの設定
                  testScope = "method"
                }
              }
            })
          },
          -- UIレイアウトの設定
          summary = {
            enabled = true,
            expand_errors = true,
            follow = true,
            mappings = {
              attach = "a",
              expand = { "<CR>", "<2-LeftMouse>" },
              expand_all = "e",
              jumpto = "i",
              output = "o",
              run = "r",
              short = "O",
              stop = "u"
            }
          },
          -- DAPとの統合
          diagnostic = {
            enabled = true,
            severity = 1
          },
          floating = {
            enabled = true,
            border = "rounded",
            max_height = 0.6,
            max_width = 0.6,
            options = {}
          },
          -- ステータスラインとの統合
          status = {
            enabled = true,
            signs = true,
            virtual_text = false
          },
        })
      end
    }
  }
}
