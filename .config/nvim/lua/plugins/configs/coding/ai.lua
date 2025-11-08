local env = require("core.env")

return {
  {
    "yetone/avante.nvim",
    cond = not env.is_vscode(),
    event = "VeryLazy",
    lazy = false,
    version = false, -- リポジトリの最新版を使用
    doc = "AI powered code assistant with Claude integration",
    dependencies = {
      "nvim-treesitter/nvim-treesitter",
      "stevearc/dressing.nvim",
      "nvim-lua/plenary.nvim",
      "MunifTanjim/nui.nvim",
      -- 画像サポート用
      {
        "3rd/image.nvim",
        opts = {
          backend = "kitty", -- Kitty terminal を使用
          integrations = {
            markdown = {
              enabled = true,
              clear_in_insert_mode = false,
              download_remote_images = true,
              only_render_image_at_cursor = false,
            },
          },
        },
      },
      {
        -- コピロットサポート（オプション）
        "zbirenbaum/copilot.lua",
        cmd = "Copilot",
        event = "InsertEnter",
        opts = {
          suggestion = { enabled = false },
          panel = { enabled = false },
        },
      },
    },
    opts = {
      -- AI プロバイダー設定
      provider = "claude", -- Claude (Anthropic) を使用
      auto_suggestions_provider = "claude",
      claude = {
        endpoint = "https://api.anthropic.com",
        model = "claude-sonnet-4-20250514",
        temperature = 0,
        max_tokens = 4096,
      },
      -- 動作設定
      behaviour = {
        auto_suggestions = true, -- 自動提案を有効化
        auto_set_highlight_group = true,
        auto_set_keymaps = true,
        auto_apply_diff_after_generation = false,
        support_paste_from_clipboard = true,
      },
      -- UI 設定
      mappings = {
        --- @class AvanteConflictMappings
        diff = {
          ours = "co",
          theirs = "ct",
          all_theirs = "ca",
          both = "cb",
          cursor = "cc",
          next = "]x",
          prev = "[x",
        },
        suggestion = {
          accept = "<M-l>",
          next = "<M-]>",
          prev = "<M-[>",
          dismiss = "<C-]>",
        },
        jump = {
          next = "]]",
          prev = "[[",
        },
        submit = {
          normal = "<CR>",
          insert = "<C-s>",
        },
        sidebar = {
          apply_all = "A",
          apply_cursor = "a",
          switch_windows = "<Tab>",
          reverse_switch_windows = "<S-Tab>",
        },
      },
      hints = { enabled = true },
      windows = {
        ---@type "right" | "left" | "top" | "bottom"
        position = "right", -- サイドバーを右側に表示
        wrap = true,        -- テキストの折り返しを有効化
        width = 30,         -- サイドバーの幅（パーセンテージ）
        sidebar_header = {
          align = "center", -- left, center, right for title
          rounded = true,
        },
      },
      highlights = {
        diff = {
          current = "DiffText",
          incoming = "DiffAdd",
        },
      },
      --- @class AvanteConflictUserConfig
      diff = {
        autojump = true,
        ---@type string | fun(): any
        list_opener = "copen",
      },
    },
    -- ビルドスクリプト（プラグインのインストール後に実行）
    build = "make",
    config = function(_, opts)
      require("avante").setup(opts)
    end,
  },
}
