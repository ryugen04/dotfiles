return {
  {
    'nvim-lualine/lualine.nvim',
    cond = not env.is_vscode(),
    dependencies = { 'nvim-tree/nvim-web-devicons' },
    config = function()
      -- 選択範囲の情報を取得する関数
      local function selectionCount()
        local mode = vim.fn.mode()
        if not mode:match("[vV\22]") then return "" end

        local start_line = vim.fn.line("v")
        local end_line = vim.fn.line(".")
        local start_pos, end_pos

        if mode == "V" then
          -- 行選択モードの場合
          start_pos = 1
          end_pos = vim.fn.strlen(vim.fn.getline(end_line)) + 1
        else
          -- 文字選択モードの場合
          start_pos = vim.fn.col("v")
          end_pos = vim.fn.col(".")
        end

        local chars = 0
        for i = start_line, end_line do
          local line = vim.fn.getline(i)
          local line_len = vim.fn.strlen(line)
          local s_pos = (i == start_line) and start_pos or 1
          local e_pos = (i == end_line) and end_pos or line_len + 1
          chars = chars + vim.fn.strchars(line:sub(s_pos, e_pos - 1))
        end

        local lines = math.abs(end_line - start_line) + 1
        return string.format("%d lines, %d characters", lines, chars)
      end

      -- LSPクライアント情報を取得する関数
      local function lsp_clients()
        local clients = vim.lsp.get_clients({ bufnr = 0 })
        if #clients == 0 then
          return " no lspclients"
        end

        local client_names = vim.tbl_map(function(client)
          return client.name
        end, clients)

        return "LSP:" .. table.concat(client_names, ", ")
      end

      -- diagnosticsの更新を制御するための関数
      local function update_diagnostics()
        vim.diagnostic.get(0) -- 現在のバッファのdiagnosticsを取得
        return true
      end

      require("lualine").setup({
        options = {
          icons_enabled = true,
          theme = "auto",
          component_separators = { left = "|", right = "|" },
          section_separators = { left = "", right = "" },
          disabled_filetypes = {},
          always_divide_middle = true,
          colored = false,
          globalstatus = true,
          refresh = {
            statusline = 2000, -- 2秒ごとに更新（パフォーマンス重視）
            tabline = 2000,
            winbar = 2000
          },
        },
        sections = {
          lualine_a = { "mode" },
          lualine_b = {
            "branch",
            {
              "diff",
              colored = true,
              symbols = { added = " ", modified = " ", removed = " " }
            }
          },
          lualine_c = {
            {
              "filename",
              path = 1,
              file_status = true,
              shorting_target = 40,
              symbols = {
                modified = " [+]",
                readonly = " [RO]",
                unnamed = "Untitled",
              },
            }
          },
          lualine_x = {
            { "searchcount" },
            { selectionCount },
            {
              "diagnostics",
              sources = { "nvim_diagnostic", "nvim_lsp" },
              sections = { "error", "warn", "info", "hint" },
              diagnostics_color = {
                error = "DiagnosticError",
                warn = "DiagnosticWarn",
                info = "DiagnosticInfo",
                hint = "DiagnosticHint",
              },
              symbols = {
                error = "E",
                warn = "W",
                info = "I",
                hint = "H"
              },
              colored = true,
              update_in_insert = false,
              always_visible = false,
            },
            { lsp_clients },
          },
          lualine_y = { "filetype", "encoding" },
          lualine_z = { "location", "progress" },
        },
        inactive_sections = {
          lualine_a = {},
          lualine_b = {},
          lualine_c = { "filename" },
          lualine_x = { "location" },
          lualine_y = {},
          lualine_z = {},
        },
        tabline = {
          lualine_a = {
            {
              "buffers",
              mode = 4,
              icons_enabled = true,
              show_filename_only = true,
              hide_filename_extensions = false,
              show_modified_status = true,
              symbols = {
                modified = ' [+]',
                alternate_file = '',
                directory = '',
              },
            },
          },
          lualine_b = {},
          lualine_c = {},
          lualine_x = {},
          lualine_y = {},
          lualine_z = { "tabs" },
        },
        extensions = {},
      })
      -- diagnosticsの更新を強制するための自動コマンドを設定
      vim.api.nvim_create_autocmd({ "DiagnosticChanged", "BufEnter", "InsertLeave" }, {
        callback = function()
          vim.schedule(function()
            require('lualine').refresh()
          end)
        end
      })
    end,
    doc = "ステータスライン"
  },

}
