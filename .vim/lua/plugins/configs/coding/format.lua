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
        },

        -- 保存時自動フォーマット
        format_on_save = {
          timeout_ms = 500,
          lsp_format = "fallback",  -- conform.nvimのフォーマッターがない場合、LSPを使用
        },

        -- フォーマッター固有の設定
        formatters = {
          shfmt = {
            prepend_args = { "-i", "2" },  -- インデント2スペース
          },
        },
      })

      -- 手動フォーマット用のキーマップ
      vim.keymap.set({ "n", "v" }, "<leader>mp", function()
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
      }

      -- 自動実行の設定
      vim.api.nvim_create_autocmd({ "BufWritePost", "BufEnter", "InsertLeave" }, {
        callback = function()
          require("lint").try_lint()
        end,
      })

      -- 手動実行用のキーマップ
      vim.keymap.set("n", "<leader>l", function()
        require("lint").try_lint()
      end, { desc = "Trigger linting" })
    end,
  },
}
