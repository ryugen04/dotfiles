-- conform.nvim + nvim-lint: 最新のフォーマット・リント管理
-- none-ls.nvimはアーカイブされたため、こちらに移行
return {
  -- コードフォーマット
  {
    'stevearc/conform.nvim',
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      require("conform").setup({
        formatters_by_ft = {
          -- Lua
          lua = { "stylua" },

          -- Python
          python = { "isort", "black" },

          -- Go
          go = { "goimports", "gofmt" },

          -- Rust
          rust = { "rustfmt", lsp_format = "fallback" },

          -- JavaScript/TypeScript
          javascript = { "prettierd", "prettier", stop_after_first = true },
          typescript = { "prettierd", "prettier", stop_after_first = true },
          javascriptreact = { "prettierd", "prettier", stop_after_first = true },
          typescriptreact = { "prettierd", "prettier", stop_after_first = true },

          -- JSON/YAML
          json = { "jq" },
          yaml = { "yamlfmt" },

          -- Markdown
          markdown = { "prettier" },

          -- Bash
          bash = { "shfmt" },
          sh = { "shfmt" },

          -- C/C++
          c = { "clang-format", lsp_format = "fallback" },
          cpp = { "clang-format", lsp_format = "fallback" },

          -- HTML/CSS
          html = { "prettier" },
          css = { "prettier" },

          -- Kotlin: LSPフォーマットを使用（またはGradleのktlintFormatを使用）
          -- kotlin = { "ktlint" },
        },

        -- 保存時自動フォーマット
        format_on_save = function(buf)
          -- `:w!`で保存したときはフォーマットをスキップ
          if vim.v.cmdbang == 1 then
            return nil
          end
          return
          {
            timeout_ms = 500,
            lsp_format = "fallback", -- conform.nvimのフォーマッターがない場合、LSPを使用
          }
        end,


        -- フォーマッター固有の設定
        formatters = {
          shfmt = {
            prepend_args = { "-i", "2" }, -- インデント2スペース
          },
        },
      })

      -- 手動フォーマット用のキーマップ
      vim.keymap.set({ "n", "v" }, "<leader>lf", function()
        require("conform").format({
          lsp_fallback = true,
          timeout_ms = 500,
        })
      end, { desc = "Format file or range" })
    end,
  },

  -- リント
  {
    "mfussenegger/nvim-lint",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      require('lint').linters_by_ft = {
        -- Python
        python = { 'pylint', 'mypy' },

        -- JavaScript/TypeScript
        javascript = { 'eslint_d' },
        typescript = { 'eslint_d' },
        javascriptreact = { 'eslint_d' },
        typescriptreact = { 'eslint_d' },

        -- Markdown
        markdown = { 'markdownlint' },

        -- Bash
        bash = { 'shellcheck' },
        sh = { 'shellcheck' },

        -- Docker
        dockerfile = { 'hadolint' },

        -- Kotlin: detekt（静的解析のみ、ktlintはGradle経由で使用）
        kotlin = { 'detekt' },
      }

      -- Detektカスタムリンター
      -- detekt CLI + カスタムパーサー
      local lint = require('lint')

      lint.linters.detekt = {
        cmd = 'detekt',
        stdin = false,
        args = {
          '--input',
          function() return vim.fn.expand('%:p') end,
          '--build-upon-default-config',
        },
        stream = 'both',
        ignore_exitcode = true,
        parser = function(output, bufnr)
          local diagnostics = {}
          local current_file = vim.api.nvim_buf_get_name(bufnr)

          -- Detekt出力形式: /path/to/file.kt:10:5: [RuleId] Description
          -- または: file.kt:10:5: [RuleId] Description
          for line in output:gmatch('[^\r\n]+') do
            -- パターン1: フルパス
            local file, lnum, col, rule_id, message =
              line:match('^(.+%.kt):(%d+):(%d+):%s*%[([^%]]+)%]%s*(.+)$')

            if file and lnum and col and rule_id and message then
              -- ファイル名が一致するかチェック
              local matches = false
              if file == current_file then
                matches = true
              elseif vim.endswith(file, vim.fn.expand('%:t')) then
                matches = true
              elseif vim.endswith(current_file, file) then
                matches = true
              end

              if matches then
                -- severityの判定（detektはデフォルトで警告レベル）
                local severity = vim.diagnostic.severity.WARN
                if message:match('^error:') or message:match('^CRITICAL') then
                  severity = vim.diagnostic.severity.ERROR
                elseif message:match('^info:') then
                  severity = vim.diagnostic.severity.INFO
                end

                table.insert(diagnostics, {
                  lnum = tonumber(lnum) - 1,
                  col = tonumber(col) - 1,
                  end_lnum = tonumber(lnum) - 1,
                  end_col = tonumber(col),
                  severity = severity,
                  source = 'detekt',
                  message = message,
                  code = rule_id,
                })
              end
            end
          end

          return diagnostics
        end,
      }

      -- 自動実行の設定
      -- Detektは重いため、Kotlinファイルでは保存時のみ実行
      vim.api.nvim_create_autocmd({ "BufWritePost", "BufEnter", "InsertLeave" }, {
        callback = function()
          local ft = vim.bo.filetype
          if ft == 'kotlin' then
            -- Kotlinファイルでは保存時のみDetektを実行
            if vim.v.event and vim.v.event.trigger == 'BufWritePost' then
              require("lint").try_lint()
            end
            -- InsertLeaveではDetektをスキップ（重いため）
          else
            require("lint").try_lint()
          end
        end,
      })
    end,
  },
}
