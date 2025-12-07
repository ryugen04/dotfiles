return {
  {
    'folke/which-key.nvim',
    event = 'VeryLazy',
    init = function()
      vim.o.timeout = true
      vim.o.timeoutlen = 300
    end,
    config = function()
      vim.o.timeout = true
      vim.o.timeoutlen = 300
      local wk = require("which-key")

      -- default keymap
      wk.add({
        {
          "<C-a>",
          function()
            require("dial.map").manipulate("increment", "normal")
          end
          ,
          desc = "Increment"
        },
        {
          "<C-x>",
          function()
            require("dial.map").manipulate("decrement", "normal")
          end
          ,
          desc = "Decrement"
        },
      })

      -- leader keymap
      wk.add({
        { "<leader>c", group = "Convert Commands" },
        {
          mode = { "n", "v" },

          {
            "<leader>cgi",
            function()
              require("dial.map").manipulate("increment", "gnormal")
            end
            ,
            desc = "Increment"
          },
          {
            "<leader>cgd",
            function()
              require("dial.map").manipulate("decrement", "gnormal")
            end
            ,
            desc = "Decrement"
          },
        },
      })


      wk.add({
        { "<leader>l", group = "LSP" },
        {
          mode = { "n", "v" },
          {
            "<leader>lR",
            function()
              vim.lsp.buf.rename()
              vim.cmd('silent! wa')
            end,
            desc = "Rename (リネーム)"
          },
          { "<leader>l,", "<cmd>lua vim.diagnostic.goto_previous()<CR>",                 desc = "Previous diagnostic (前の診断)" },
          { "<leader>l.", "<cmd>lua vim.diagnostic.goto_next()<CR>",                     desc = "Next diagnostic (次の診断)" },
          { "<leader>la", "<cmd>lua vim.lsp.buf.code_action()<CR>",                      desc = "Code action (コードアクション)" },
          { "<leader>ld", "<cmd>lua require('telescope.builtin').lsp_definitions()<CR>", desc = "Go to definition (定義へジャンプ)" },
          { "<leader>lf", "<cmd>lua vim.lsp.buf.format()<CR>",                           desc = "Format (フォーマット)" },
          { "<leader>li", "<cmd>lua vim.lsp.buf.implementation()<CR>",                   desc = "Go to implementation (実装へジャンプ)" },
          { "<leader>lk", "<cmd>lua vim.lsp.buf.hover()<CR>",                            desc = "Hover info (ホバー情報)" },
          { "<leader>lo", "<cmd>lua vim.diagnostic.open_float()<CR>",                    desc = "Open diagnostic float (診断をフロート表示)" },
          { "<leader>lr", "<cmd>lua require('telescope.builtin').lsp_references()<CR>",  desc = "Show references (参照を表示)" },
          { "<leader>ls", "<cmd>lua vim.lsp.buf.signature_help()<CR>",                   desc = "Signature help (シグネチャヘルプ)" },
          { "<leader>lD", "<cmd>lua vim.lsp.buf.type_definition()<CR>",                  desc = "Go to type definition (型定義へジャンプ)" },
        },
        {
          { "<leader>lt",  group = "LSP: Troubles (問題一覧)" },
          mode = { "n", "v" },
          { "<leader>ltd", "<cmd>Trouble diagnostics toggle<CR>",                        desc = "Diagnostics (診断一覧)" },
          { "<leader>ltb", "<cmd>Trouble diagnostics toggle filter.buf=0<cr>",           desc = "Buffer Diagnostics (バッファ診断)" },
          { "<leader>lts", "<cmd>Trouble symbols toggle focus=false<cr>",                desc = "Symbols (シンボル一覧)" },
          { "<leader>ltl", "<cmd>Trouble lsp toggle focus=false win.position=right<cr>", desc = "LSP Definitions / references (定義/参照一覧)" },
          { "<leader>lti", "<cmd>Trouble loclist toggle<cr>",                            desc = "Location List (ロケーションリスト)" },
          { "<leader>ltq", "<cmd>Trouble qflist toggle<cr>",                             desc = "Quickfix List (Quickfixリスト)" },
        },
      }
      )

      if not vim.g.vscode then
        wk.add({
          { "<leader>e",  group = "NvimTree" },
          { "<leader>ee", "<cmd>NvimTreeOpen | NvimTreeFindFile<CR>", desc = "NvimTreeFindFile" },
          { "<leader>ef", "<cmd>NvimTreeFindFile<CR>",                desc = "NvimTreeFindFile" },
          { "<leader>eq", "<cmd>NvimTreeClose<CR>",                   desc = "NvimTreeClose" },
          { "<leader>er", "<cmd>NvimTreeRefresh<CR>",                 desc = "NvimTreeRefresh" },
        })

        local function open_in_new_tab(cmd)
          vim.cmd("tabnew")
          local win = vim.api.nvim_get_current_win()
          local buf = vim.api.nvim_get_current_buf()
          vim.cmd(cmd)
          return { win = win, buf = buf }
        end
        wk.add({
          { "<leader>d",  group = "Debug" },
          { "<leader>db", function() require('dap').toggle_breakpoint() end,             desc = "toggle breakpoint" },
          { "<leader>dc", function() require('dap').continue() end,                      desc = "continue" },
          { "<leader>do", function() require('dap').step_over() end,                     desc = "step over" },
          { "<leader>di", function() require('dap').step_into() end,                     desc = "step into" },

          { '<leader>du', require 'dapui'.toggle,                                        desc = 'Debug: Toggle UI' },
          { '<leader>dh', function() require 'dap.ui.widgets'.hover() end,               desc = 'Debug: Hover' },
          { '<leader>dp', function() require 'dap.ui.widgets'.preview() end,             desc = 'Debug: Preview' },
          { '<leader>dh', function() require 'dap.ui.widgets'.hover() end,               desc = 'Debug: Hover' },

          -- テスト関連の設定を追加
          { "<leader>t",  group = "Test" },
          { "<leader>tt", function() require("neotest").run.run() end,                   desc = "Run Nearest" },
          { "<leader>tf", function() require("neotest").run.run(vim.fn.expand("%")) end, desc = "Run File" },
          {
            "<leader>td",
            function()
              local neotest = require("neotest")

              local ts_utils = require("nvim-treesitter.ts_utils")
              local node = ts_utils.get_node_at_cursor()
              local test_name = nil
              local class_name = nil

              while node do
                local node_type = node:type()
                if node_type == "function_definition" then
                  local name_node = node:field("name")[1]
                  if name_node then
                    local name = vim.treesitter.get_node_text(name_node, 0)
                    if string.match(name, "^test_") then
                      test_name = name
                      break
                    end
                  end
                elseif node_type == "method_declaration" then
                  -- メソッド名を取得
                  local name_node = node:field("name")[1]
                  if name_node then
                    local method_text = vim.treesitter.get_node_text(node, 0)
                    -- @Testアノテーションを含むかチェック
                    if method_text:match("@Test") then
                      test_name = vim.treesitter.get_node_text(name_node, 0)
                      break
                    end
                  end
                end

                node = node:parent()
              end

              if not test_name then
                vim.notify("No test found near cursor", vim.log.levels.ERROR)
                return nil
              end

              -- pytestの場合、-kオプションでテストを指定
              position = { id = test_name }

              if not position then
                vim.notify("No test found near cursor", vim.log.levels.ERROR)
                return nil
              end
              local function get_test_debug_config(filetype)
                local configs = {
                  java = {
                    strategy = "dap",
                    extra_args = {
                      "-Dmaven.surefire.debug",
                      "-DforkCount=0",
                      "-DreuseForks=false"
                    },
                    scope = "nearest",
                    dap = {
                      justMyCode = false,
                      testScope = "method",
                      console = "integratedTerminal",
                      hotReload = "auto"
                    }
                  },
                  python = {
                    position = position.id,
                    strategy = "dap",
                    scope = "nearest",
                    extra_args = { "-k", position.id },
                    dap = {
                      justMyCode = false,
                      console = "integratedTerminal"
                    }
                  }
                }

                return configs[filetype] or {
                  strategy = "dap",
                  scope = "nearest"
                }
              end
              local filetype = vim.bo.filetype
              local config = get_test_debug_config(filetype)
              require("neotest").run.run(
                config
              )
            end,
            desc = "Debug Test"
          },
          { "<leader>ts", function() require("neotest").summary.toggle() end,              desc = "Toggle Summary" },
          { "<leader>to", function() require("neotest").output.open({ enter = true }) end, desc = "Show Output" },
        })

        wk.add(
          {
            { "<leader>f",                   group = "telescope" },
            { "<leader>fr",                  "<cmd>Telescope file_browser<CR>",                                       desc = "file browser" },
            { "<leader>fb",                  "<cmd>lua require('telescope.builtin').buffers()<CR>",                   desc = "find buffers" },
            { "<leader>ff",                  "<cmd>lua require('telescope.builtin').find_files()<CR>",                desc = "find files" },
            { "<leader>fg",                  "<cmd>lua require('telescope.builtin').live_grep()<CR>",                 desc = "live grep" },
            { "<leader>fc",                  "<cmd>lua require('telescope.builtin').commands()<CR>",                  desc = "show commands" },
            { "<leader>fm",                  "<cmd>lua require('telescope.builtin').marks()<CR>",                     desc = "show marks" },
            { "<leader>fv",                  "<cmd>lua require('telescope.builtin').registers()<CR>",                 desc = "show registers" },
            { "<leader>fy",                  "<cmd>lua require('neoclip.fzf')({'a', 'star', 'plus', 'unnmaed'})<CR>", desc = "yank" },
            { mode = { "n", "i", "v", "t" }, { "<c-q>", "<cmd>ToggleTermToggleAll<CR>", desc = "close toggle" } }

          }
        )
        wk.add(
          {
            { "<leader>g",   group = "Git" },
            { "<leader>gg",  "<cmd>LazyGit<CR>",                                       desc = "open lazygit" },
            { "<leader>gs",  "<cmd>lua require('telescope.builtin').git_status()<CR>", desc = "git status files" },
            { "<leader>gb",  "<cmd>BlamerToggle<CR>",                                  desc = "show git blame" },
            { "<leader>gvo", "<cmd>DiffviewOpen<CR>",                                  desc = "show git diff" },
            { "<leader>gvc", "<cmd>DiffviewClose<CR>",                                 desc = "close git diff" },
            -- octo.nvim
            { "<leader>go",  group = "Octo" },
            { "<leader>goc", "<cmd>Octo pr<CR>",                                       desc = "現在のPR" },
            { "<leader>gon", "<cmd>Octo pr create<CR>",                                desc = "PR作成" },
            { "<leader>gof", "gf",                                                     desc = "ファイルを開く" },
            -- レビュー
            { "<leader>gor", group = "Review" },
            { "<leader>gors", "<cmd>Octo review start<CR>",                            desc = "開始" },
            { "<leader>gorr", "<cmd>Octo review resume<CR>",                           desc = "再開" },
            { "<leader>gorb", "<cmd>Octo review submit<CR>",                           desc = "提出" },
            { "<leader>gord", "<cmd>Octo review discard<CR>",                          desc = "破棄" },
            -- コメント
            { "<leader>gom", group = "Comment" },
            { "<leader>goma", "<cmd>Octo comment add<CR>",                             desc = "追加" },
            { "<leader>goms", "<cmd>Octo suggestion<CR>",                              desc = "提案" },
            { "<leader>gomd", "<cmd>Octo comment delete<CR>",                          desc = "削除" },
            { "<leader>gomr", "<cmd>Octo thread resolve<CR>",                          desc = "解決" },
            -- リアクション
            { "<leader>goa", group = "Reaction" },
            { "<leader>goa+", "<cmd>Octo reaction thumbs_up<CR>",                      desc = "👍" },
            { "<leader>goa-", "<cmd>Octo reaction thumbs_down<CR>",                    desc = "👎" },
            { "<leader>goah", "<cmd>Octo reaction heart<CR>",                          desc = "❤️" },
            { "<leader>goae", "<cmd>Octo reaction eyes<CR>",                           desc = "👀" },
            { "<leader>goar", "<cmd>Octo reaction rocket<CR>",                         desc = "🚀" },
            { "<leader>goap", "<cmd>Octo reaction hooray<CR>",                         desc = "🎉" },
            -- コピー
            { "<leader>goy", group = "Copy URL" },
            { "<leader>goyu", "<cmd>Octo pr url<CR>",                                  desc = "PR URL" },
            { "<leader>goyc", "<cmd>Octo comment url<CR>",                             desc = "コメントURL" },
          }
        )

        wk.add({
          { "<leader>s", group = "Image Commands" },
          {
            mode = { "v" },
            {
              "<leader>sc",
              function()
                require("nvim-silicon").clip()
              end
              ,
              desc = "Silicon save clipboard"
            },
            {
              "<leader>sf",
              function()
                require("nvim-silicon").file()
              end
              ,
              desc = "Silicon save file"
            },
            {
              "<leader>sv",
              "<cmd>PasteImage<cr>"
              ,
              desc = "Silicon save file"
            },
          },
        })

        -- flash.nvimのキーマップはflash.lua内で定義されています
        wk.add({
          { "<leader>w", group = "Window" },
          {
            mode = { "n", },
            {
              "<leader>wt",
              "<cmd>WinResizerStartResize<CR>",
              desc = "window resize"
            },
          },
        })

        -- AI アシスタント (avante.nvim)
        wk.add({
          { "<leader>ai", group = "AI Assistant" },
          {
            mode = { "n", "v" },
            { "<leader>aia", "<cmd>AvanteAsk<CR>",                                   desc = "Avante Ask (Chat)" },
            { "<leader>air", "<cmd>AvanteRefresh<CR>",                               desc = "Avante Refresh" },
            { "<leader>aie", "<cmd>AvanteEdit<CR>",                                  desc = "Avante Edit" },
            { "<leader>ait", "<cmd>AvanteToggle<CR>",                                desc = "Avante Toggle" },
            { "<leader>aic", function() require('avante').apply_cursor() end,        desc = "Apply suggestion at cursor" },
            { "<leader>aiA", function() require('avante').apply_all() end,           desc = "Apply all suggestions" },
            { "<leader>ain", function() require('avante').next_suggestion() end,     desc = "Next suggestion" },
            { "<leader>aip", function() require('avante').previous_suggestion() end, desc = "Previous suggestion" },
          },
        })
      else
        vim.keymap.set("n", "<leader>fb", "<Cmd>call VSCodeNotify('workbench.action.quickOpen')<CR>")
        vim.keymap.set("n", "H", "<Cmd>call VSCodeNotify('workbench.action.previousEditor')<CR>")
        vim.keymap.set("n", "L", "<Cmd>call VSCodeNotify('workbench.action.nextEditor')<CR>")
      end
    end,
    dependencies = {
      'echasnovski/mini.icons',
    },
  },

}
