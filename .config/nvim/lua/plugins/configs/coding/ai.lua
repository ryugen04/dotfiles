return {
  {
    "coder/claudecode.nvim",
    dependencies = { "folke/snacks.nvim" },
    config = function()
      -- snacks.nvimのinputスタイルをカスタマイズ
      require("snacks").setup({
        input = {
          keys = {
            -- Enterキーで改行を挿入（insertモードのみ）
            i_cr = { "<cr>", function()
              local pos = vim.api.nvim_win_get_cursor(0)
              vim.api.nvim_buf_set_lines(0, pos[1]-1, pos[1]-1, false, {""})
              vim.api.nvim_win_set_cursor(0, {pos[1]+1, 0})
            end, mode = "i" },
            -- Ctrl+Enterで送信
            i_ctrl_cr = { "<c-cr>", "confirm", mode = "i" },
            n_ctrl_cr = { "<c-cr>", "confirm", mode = "n" },
            -- Escapeキーで中断
            i_esc = { "<esc>", "cancel", mode = "i" },
            n_esc = { "<esc>", "cancel", mode = "n" },
          },
        },
      })
      
      -- claudecode.nvimのセットアップ
      require("claudecode").setup()
    end,
    keys = {
      { "<leader>a",  nil,                              desc = "AI/Claude Code" },
      { "<leader>ac", "<cmd>ClaudeCode<cr>",            desc = "Toggle Claude" },
      { "<leader>af", "<cmd>ClaudeCodeFocus<cr>",       desc = "Focus Claude" },
      { "<leader>ar", "<cmd>ClaudeCode --resume<cr>",   desc = "Resume Claude" },
      { "<leader>aC", "<cmd>ClaudeCode --continue<cr>", desc = "Continue Claude" },
      { "<leader>ab", "<cmd>ClaudeCodeAdd %<cr>",       desc = "Add current buffer" },
      { "<leader>as", "<cmd>ClaudeCodeSend<cr>",        mode = "v",                 desc = "Send to Claude" },
      {
        "<leader>as",
        "<cmd>ClaudeCodeTreeAdd<cr>",
        desc = "Add file",
        ft = { "NvimTree", "neo-tree", "oil" },
      },
      -- Diff management
      { "<leader>aa", "<cmd>ClaudeCodeDiffAccept<cr>", desc = "Accept diff" },
      { "<leader>ad", "<cmd>ClaudeCodeDiffDeny<cr>",   desc = "Deny diff" },
    },
  }
}
