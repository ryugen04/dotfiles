local env = require("core.env")

return {
  -- Claude Code IDE統合
  {
    "coder/claudecode.nvim",
    cond = not env.is_vscode(),
    dependencies = { "folke/snacks.nvim" },
    config = function()
      require("claudecode").setup({
        terminal = {
          provider = "snacks",
          snacks_win_opts = {
            position = "right",
            width = 0.30,
            height = 1.0,
          },
        },
      })

      -- diffviewウィンドウ均等化関数
      local function equalize_diff_windows()
        vim.defer_fn(function()
          local wins = vim.api.nvim_tabpage_list_wins(0)
          local diff_wins = {}
          for _, win in ipairs(wins) do
            local buf = vim.api.nvim_win_get_buf(win)
            -- diffモードのウィンドウを検出
            if vim.wo[win].diff then
              table.insert(diff_wins, win)
            end
          end
          -- diffウィンドウが2つあれば均等化
          if #diff_wins == 2 then
            local total_width = 0
            for _, win in ipairs(diff_wins) do
              total_width = total_width + vim.api.nvim_win_get_width(win)
            end
            local equal_width = math.floor(total_width / 2)
            for _, win in ipairs(diff_wins) do
              vim.api.nvim_win_set_width(win, equal_width)
            end
          end
        end, 200)
      end

      -- ターミナルが開いた時にdiffviewを均等化
      vim.api.nvim_create_autocmd("TermOpen", {
        pattern = "*",
        callback = function()
          local bufname = vim.api.nvim_buf_get_name(0)
          if bufname:match("claude") then
            vim.g.claude_code_was_open = true
            equalize_diff_windows()
          end
        end,
      })

      -- WinNewでも検出（snacks.nvimのウィンドウ作成時）
      vim.api.nvim_create_autocmd("WinNew", {
        callback = function()
          vim.defer_fn(function()
            local buf = vim.api.nvim_get_current_buf()
            local bufname = vim.api.nvim_buf_get_name(buf)
            if bufname:match("claude") or bufname:match("snacks_terminal") then
              vim.g.claude_code_was_open = true
              equalize_diff_windows()
            end
          end, 100)
        end,
      })
    end,
    keys = {
      { "<leader>a", nil, desc = "AI/Claude Code" },
      { "<leader>ac", "<cmd>ClaudeCode<cr>", desc = "Toggle Claude" },
      { "<leader>af", "<cmd>ClaudeCodeFocus<cr>", desc = "Focus Claude" },
      { "<leader>ar", "<cmd>ClaudeCode --resume<cr>", desc = "Resume Claude" },
      { "<leader>aC", "<cmd>ClaudeCode --continue<cr>", desc = "Continue Claude" },
      { "<leader>am", "<cmd>ClaudeCodeSelectModel<cr>", desc = "Select Claude model" },
      { "<leader>ab", "<cmd>ClaudeCodeAdd %<cr>", desc = "Add current buffer" },
      { "<leader>as", "<cmd>ClaudeCodeSend<cr>", mode = "v", desc = "Send to Claude" },
      {
        "<leader>as",
        "<cmd>ClaudeCodeTreeAdd<cr>",
        desc = "Add file",
        ft = { "NvimTree", "neo-tree", "oil", "minifiles" },
      },
      -- Diff管理
      { "<leader>aa", "<cmd>ClaudeCodeDiffAccept<cr>", desc = "Accept diff" },
      { "<leader>ad", "<cmd>ClaudeCodeDiffDeny<cr>", desc = "Deny diff" },
    },
  },
  -- {
  --   "yetone/avante.nvim",
  --   cond = not env.is_vscode(),
  --   event = "VeryLazy",
  --   lazy = false,
  --   version = false, -- リポジトリの最新版を使用
  --   doc = "AI powered code assistant with Claude integration",
  --   dependencies = {
  --     "nvim-treesitter/nvim-treesitter",
  --     "stevearc/dressing.nvim",
  --     "nvim-lua/plenary.nvim",
  --     "MunifTanjim/nui.nvim",
  --     -- 画像サポート用
  --     {
  --       "3rd/image.nvim",
  --       opts = {
  --         backend = "kitty", -- Kitty terminal を使用
  --         integrations = {
  --           markdown = {
  --             enabled = true,
  --             clear_in_insert_mode = false,
  --             download_remote_images = true,
  --             only_render_image_at_cursor = false,
  --           },
  --         },
  --       },
  --     },
  --     {
  --       -- コピロットサポート（オプション）
  --       "zbirenbaum/copilot.lua",
  --       cmd = "Copilot",
  --       event = "InsertEnter",
  --       opts = {
  --         suggestion = { enabled = false },
  --         panel = { enabled = false },
  --       },
  --     },
  --   },
  --   opts = {
  --     -- AI プロバイダー設定
  --     provider = "claude", -- Claude (Anthropic) を使用
  --     auto_suggestions_provider = "claude",
  --     claude = {
  --       endpoint = "https://api.anthropic.com",
  --       model = "claude-sonnet-4-20250514",
  --       temperature = 0,
  --       max_tokens = 4096,
  --     },
  --     -- 動作設定
  --     behaviour = {
  --       auto_suggestions = true, -- 自動提案を有効化
  --       auto_set_highlight_group = true,
  --       auto_set_keymaps = true,
  --       auto_apply_diff_after_generation = false,
  --       support_paste_from_clipboard = true,
  --     },
  --     -- UI 設定
  --     mappings = {
  --       --- @class AvanteConflictMappings
  --       diff = {
  --         ours = "co",
  --         theirs = "ct",
  --         all_theirs = "ca",
  --         both = "cb",
  --         cursor = "cc",
  --         next = "]x",
  --         prev = "[x",
  --       },
  --       suggestion = {
  --         accept = "<M-l>",
  --         next = "<M-]>",
  --         prev = "<M-[>",
  --         dismiss = "<C-]>",
  --       },
  --       jump = {
  --         next = "]]",
  --         prev = "[[",
  --       },
  --       submit = {
  --         normal = "<CR>",
  --         insert = "<C-s>",
  --       },
  --       sidebar = {
  --         apply_all = "A",
  --         apply_cursor = "a",
  --         switch_windows = "<Tab>",
  --         reverse_switch_windows = "<S-Tab>",
  --       },
  --     },
  --     hints = { enabled = true },
  --     windows = {
  --       ---@type "right" | "left" | "top" | "bottom"
  --       position = "right", -- サイドバーを右側に表示
  --       wrap = true,        -- テキストの折り返しを有効化
  --       width = 30,         -- サイドバーの幅（パーセンテージ）
  --       sidebar_header = {
  --         align = "center", -- left, center, right for title
  --         rounded = true,
  --       },
  --     },
  --     highlights = {
  --       diff = {
  --         current = "DiffText",
  --         incoming = "DiffAdd",
  --       },
  --     },
  --     --- @class AvanteConflictUserConfig
  --     diff = {
  --       autojump = true,
  --       ---@type string | fun(): any
  --       list_opener = "copen",
  --     },
  --   },
  --   -- ビルドスクリプト（プラグインのインストール後に実行）
  --   build = "make",
  --   config = function(_, opts)
  --     require("avante").setup(opts)
  --   end,
  -- },
}
