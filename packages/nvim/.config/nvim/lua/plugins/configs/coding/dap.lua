return {
  {
    "rcarriga/nvim-dap-ui",
    dependencies = { "mfussenegger/nvim-dap", "nvim-neotest/nvim-nio", "mfussenegger/nvim-dap-python", },
    config = function()
      require("dap-python").setup("uv")
      -- DAP UIの基本設定
      require("dapui").setup({
        layouts = {
          {
            elements = {
              { id = "scopes",      size = 0.25 },
              { id = "breakpoints", size = 0.25 },
              { id = "stacks",      size = 0.25 },
              { id = "watches",     size = 0.25 },
            },
            position = "left",
            size = 40
          },
          {
            elements = {
              { id = "repl",    size = 0.5 },
              { id = "console", size = 0.5 }
            },
            position = "bottom",
            size = 10
          }
        },
      })

      -- DAPイベントにUIを連動させる
      local dap, dapui = require("dap"), require("dapui")

      -- pandasのデータフレーム表示用の設定
      dap.configurations.python = {
        {
          type = 'python',
          request = 'launch',
          name = 'Python: Current File',
          program = "${file}",
          console = "integratedTerminal",
          -- デバッグ時の表示設定
          postDebugTask = "stopDebugging",
          justMyCode = false,
          -- pandas表示の設定
          env = {
            PYTHONBREAKPOINT = "ipdb.set_trace",
            COLUMNS = "120",       -- データフレーム表示幅
            DISPLAY_MAX_ROWS = "50", -- 表示する最大行数
          },
        }
      }

      local function open_in_new_tab(cmd)
        vim.cmd("tabnew")
        local win = vim.api.nvim_get_current_win()
        local buf = vim.api.nvim_get_current_buf()
        vim.cmd(cmd)
        return { win = win, buf = buf }
      end

      dap.listeners.after.event_initialized["dapui_config"] = function()
        open_in_new_tab("")
        dapui.open()
      end
      dap.listeners.before.event_terminated["dapui_config"] = function()
        dapui.close()
      end
      dap.listeners.before.event_exited["dapui_config"] = function()
        dapui.close()
      end
      vim.fn.sign_define('DapBreakpoint', { text = '🛑', texthl = 'DapBreakpoint', linehl = '', numhl = '' })
      vim.fn.sign_define('DapBreakpointCondition',
        { text = '🔍', texthl = 'DapBreakpointCondition', linehl = '', numhl = '' })
      vim.fn.sign_define('DapLogPoint', { text = '📝', texthl = 'DapLogPoint', linehl = '', numhl = '' })
    end
  }
}
