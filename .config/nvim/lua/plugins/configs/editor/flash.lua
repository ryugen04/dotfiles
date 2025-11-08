return {
  -- ナビゲーション
  {
    'folke/flash.nvim',
    cond = not env.is_vscode(),
    event = "VeryLazy",
    opts = {
      -- ラベル設定
      labels = "asdfghjklqwertyuiopzxcvbnm",
      -- 検索設定
      search = {
        multi_window = true,
        forward = true,
        wrap = true,
        mode = "exact", -- exact, search, fuzzy
        incremental = false,
      },
      -- ジャンプ設定
      jump = {
        jumplist = true,
        pos = "start",
        history = false,
        register = false,
        nohlsearch = false,
        autojump = false,
      },
      -- ラベル表示設定
      label = {
        uppercase = true,
        exclude = "",
        current = true,
        after = true,
        before = false,
        style = "overlay",
        reuse = "lowercase",
        distance = true,
        min_pattern_length = 0,
        rainbow = {
          enabled = false,
          shade = 5,
        },
      },
      -- ハイライト設定
      highlight = {
        backdrop = true,
        matches = true,
        priority = 5000,
        groups = {
          match = "FlashMatch",
          current = "FlashCurrent",
          backdrop = "FlashBackdrop",
          label = "FlashLabel",
        },
      },
      -- モード設定
      modes = {
        -- 通常の文字検索
        char = {
          enabled = true,
          config = function(opts)
            opts.autohide = opts.autohide or (vim.fn.mode(true):find("no") and vim.v.operator == "y")
            opts.jump_labels = opts.jump_labels and vim.v.count == 0
          end,
          autohide = false,
          jump_labels = false,
          multi_line = true,
          label = { exclude = "hjkliardc" },
          keys = { "f", "F", "t", "T", ";", "," },
          char_actions = function(motion)
            return {
              [";"] = "next",
              [","] = "prev",
              [motion:lower()] = "next",
              [motion:upper()] = "prev",
            }
          end,
          search = { wrap = false },
          highlight = { backdrop = true },
          jump = { register = false },
        },
        -- Treesitterベースの選択
        treesitter = {
          labels = "abcdefghijklmnopqrstuvwxyz",
          jump = { pos = "range" },
          search = { incremental = false },
          label = { before = true, after = true, style = "inline" },
          highlight = {
            backdrop = false,
            matches = false,
          },
        },
        -- リモート操作（Treesitterノード選択）
        treesitter_search = {
          jump = { pos = "range" },
          search = { multi_window = true, wrap = true, incremental = false },
          remote_op = { restore = true },
          label = { before = true, after = true, style = "inline" },
        },
      },
      -- プロンプト設定
      prompt = {
        enabled = true,
        prefix = { { "⚡", "FlashPromptIcon" } },
        win_config = {
          relative = "editor",
          width = 1,
          height = 1,
          row = -1,
          col = 0,
          zindex = 1000,
        },
      },
      -- リモート操作設定
      remote_op = {
        restore = false,
        motion = false,
      },
    },
    keys = {
      -- 基本的なジャンプ（hop.nvimのHopWordに相当）
      {
        "<leader>j",
        mode = { "n", "x", "o" },
        function()
          require("flash").jump()
        end,
        desc = "Flash Jump",
      },
      -- 行ジャンプ（hop.nvimのHopLineに相当）
      {
        "<leader>k",
        mode = { "n", "x", "o" },
        function()
          require("flash").jump({
            search = { mode = "search", max_length = 0 },
            label = { after = { 0, 0 } },
            pattern = "^"
          })
        end,
        desc = "Flash Line",
      },
      -- Treesitterベースの選択
      {
        "S",
        mode = { "n", "o", "x" },
        function()
          require("flash").treesitter()
        end,
        desc = "Flash Treesitter",
      },
      -- リモートFlash（オペレータ待機モード）
      {
        "r",
        mode = "o",
        function()
          require("flash").remote()
        end,
        desc = "Remote Flash",
      },
      -- Treesitter検索
      {
        "R",
        mode = { "o", "x" },
        function()
          require("flash").treesitter_search()
        end,
        desc = "Treesitter Search",
      },
      -- 検索モードでのflash切り替え
      {
        "<c-s>",
        mode = { "c" },
        function()
          require("flash").toggle()
        end,
        desc = "Toggle Flash Search",
      },
    },
    doc = "高速ナビゲーションとTreesitter統合ジャンプ"
  },
}
