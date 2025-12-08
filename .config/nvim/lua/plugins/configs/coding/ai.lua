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
          -- フローティングウィンドウで開く（octo.nvimのレイアウトと干渉しない）
          snacks_win_opts = {
            position = "float",
            width = 0.85,
            height = 0.85,
          },
        },
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
