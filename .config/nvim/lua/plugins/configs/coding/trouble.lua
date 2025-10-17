local env = require('core.env')

return {
  {
    "folke/trouble.nvim",
    cond = not env.is_vscode(),
    dependencies = { "nvim-tree/nvim-web-devicons" },
    cmd = { "TroubleToggle", "Trouble" },
    config = function()
      require("trouble").setup({
        position = "bottom",
        height = 10,
        width = 50,
        icons = true,
        mode = "workspace_diagnostics",
        severity = nil,
        fold_open = "",
        fold_closed = "",
        group = true,
        padding = true,
        cycle_results = true,
        action_keys = {
          close = "q",
          cancel = "<esc>",
          refresh = "r",
          jump = "<cr>",
          toggle_fold = { "zA", "za" },
          previous = "k",
          next = "j"
        },
        auto_jump = {},
        signs = {
          error = "",
          warning = "",
          hint = "",
          information = "",
          other = "",
        },
        icons = {
          ---@type trouble.Indent.symbols
          indent        = {
            top         = "│ ",
            middle      = "├╴",
            last        = "└╴",
            -- last          = "-╴",
            -- last       = "╰╴", -- rounded
            fold_open   = " ",
            fold_closed = " ",
            ws          = "  ",
          },
          folder_closed = " ",
          folder_open   = " ",
          kinds         = {
            Array         = " ",
            Boolean       = "󰨙 ",
            Class         = " ",
            Constant      = "󰏿 ",
            Constructor   = " ",
            Enum          = " ",
            EnumMember    = " ",
            Event         = " ",
            Field         = " ",
            File          = " ",
            Function      = "󰊕 ",
            Interface     = " ",
            Key           = " ",
            Method        = "󰊕 ",
            Module        = " ",
            Namespace     = "󰦮 ",
            Null          = " ",
            Number        = "󰎠 ",
            Object        = " ",
            Operator      = " ",
            Package       = " ",
            Property      = " ",
            String        = " ",
            Struct        = "󰆼 ",
            TypeParameter = " ",
            Variable      = "󰀫 ",
          },
        },
        use_diagnostic_signs = true
      })

      -- -- キーマッピング
      -- vim.keymap.set("n", "<leader>xx", function() require("trouble").toggle() end,
      --   { desc = "Toggle Trouble" })
      -- vim.keymap.set("n", "<leader>xw", function() require("trouble").toggle("workspace_diagnostics") end,
      --   { desc = "Workspace Diagnostics" })
      -- vim.keymap.set("n", "<leader>xd", function() require("trouble").toggle("document_diagnostics") end,
      --   { desc = "Document Diagnostics" })
      -- vim.keymap.set("n", "<leader>xq", function() require("trouble").toggle("quickfix") end,
      --   { desc = "Quickfix List" })
      -- vim.keymap.set("n", "<leader>xl", function() require("trouble").toggle("loclist") end,
      --   { desc = "Location List" })

      -- TelescopeとTroubleの統合
      local trouble = require("trouble.sources.telescope")
      local telescope = require("telescope")
      telescope.setup({
        defaults = {
          mappings = {
            i = { ["<c-t>"] = trouble.open_with_trouble },
            n = { ["<c-t>"] = trouble.open_with_trouble },
          },
        },
      })
    end,
  },
}
