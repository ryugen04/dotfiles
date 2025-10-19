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

          -- Kotlin: detektはGradleプロジェクトで管理
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

        -- Kotlin: detektはGradleプロジェクトで管理
      }

      -- 自動実行の設定
      vim.api.nvim_create_autocmd({ "BufWritePost", "BufEnter", "InsertLeave" }, {
        callback = function()
          require("lint").try_lint()
        end,
      })
    end,
  },
}
