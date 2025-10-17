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
            desc = "vim.lsp.buf.rename()"
          },
          { "<leader>l,", "<cmd>lua vim.diagnostic.goto_previous()<CR>",                 desc = "vim.diagnostic.goto_previous()" },
          { "<leader>l.", "<cmd>lua vim.diagnostic.goto_next()<CR>",                     desc = "vim.diagnostic.goto_next()" },
          { "<leader>la", "<cmd>lua vim.lsp.buf.code_action()<CR>",                      desc = "vim.lsp.buf.code_action()" },
          { "<leader>ld", "<cmd>lua require('telescope.builtin').lsp_definitions()<CR>", desc = "move definitions under cursor" },
          { "<leader>lf", "<cmd>lua vim.lsp.buf.format()<CR>",                           desc = "vim.lsp.buf.format()" },
          { "<leader>li", "<cmd>lua vim.lsp.buf.implementation()<CR>",                   desc = "vim.lsp.buf.implementation()" },
          { "<leader>lk", "<cmd>lua vim.lsp.buf.hover()<CR>",                            desc = "vim.lsp.buf.hover()" },
          { "<leader>lo", "<cmd>lua vim.diagnostic.open_float()<CR>",                    desc = "vim.diagnostic.open_float()" },
          { "<leader>lr", "<cmd>lua require('telescope.builtin').lsp_references()<CR>",  desc = "show references" },
          { "<leader>ls", "<cmd>lua vim.lsp.buf.signature_help()<CR>",                   desc = "show signature help" },
          { "<leader>lD", "<cmd>lua vim.lsp.buf.type_definition()<CR>",                  desc = "move type definitions" },
        },
        {
          { "<leader>lt",  group = "LSP: Troubles" },
          mode = { "n", "v" },
          { "<leader>ltd", "<cmd>Trouble diagnostics toggle<CR>",                        desc = "Diagnostics (Trouble)" },
          { "<leader>ltb", "<cmd>Trouble diagnostics toggle filter.buf=0<cr>",           desc = "Buffer Diagnostics (Trouble)" },
          { "<leader>lts", "<cmd>Trouble symbols toggle focus=false<cr>",                desc = "Symbols (Trouble)" },
          { "<leader>ltl", "<cmd>Trouble lsp toggle focus=false win.position=right<cr>", desc = "LSP Definitions / references / ... (Trouble)" },
          { "<leader>lti", "<cmd>Trouble loclist toggle<cr>",                            desc = "Location List (Trouble)" },
          { "<leader>ltq", "<cmd>Trouble qflist toggle<cr>",                             desc = "Quickfix List (Trouble)" },
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
            { "<leader>gvo", "<cmd>DiffviewClose<CR>",                                 desc = "close git diff" },
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

        wk.add({
          { "<leader>m",  group = "Move Commands" },
          { "<leader>mh", "<cmd>HopWord<CR>",     desc = "HopWord" },
        })
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
