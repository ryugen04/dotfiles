return {
  -- Git
  {
    'kdheepak/lazygit.nvim',
    cond = not env.is_vscode(),
    cmd = { "LazyGit", "LazyGitConfig", "LazyGitCurrentFile", "LazyGitFilter", "LazyGitFilterCurrentFile" },
    keys = {
      { "<leader>gg", "<cmd>LazyGit<cr>", desc = "LazyGit" },
    },
    dependencies = { 'nvim-telescope/telescope.nvim' },
    config = function()
      require('telescope').load_extension('lazygit')
      local group = vim.api.nvim_create_augroup("LazygitMods", { clear = true })
      vim.api.nvim_create_autocmd("TermEnter", {
        pattern = "*",
        group = group,
        callback = function()
          local name = vim.api.nvim_buf_get_name(0)
          if string.find(name, "lazygit") then
            vim.keymap.set("t", "<ESC>",
              function()
                -- Get the terminal job ID for the current buffer
                local bufnr = vim.api.nvim_get_current_buf()
                local chan = vim.b[bufnr].terminal_job_id
                if chan then
                  -- Send the ESC key sequence to the terminal
                  -- "\x1b" is the escape character
                  vim.api.nvim_chan_send(chan, "\x1b")
                end
                --vim.cmd([[call feedkeys("q")]])
              end,
              { buffer = true })
            return
          end
        end,
      })
    end,
    doc = "Git UI"
  },
  {
    'sindrets/diffview.nvim',
    cond = not env.is_vscode(),
    cmd = { "DiffviewOpen", "DiffviewClose", "DiffviewToggleFiles", "DiffviewFocusFiles", "DiffviewRefresh" },
  },
  {
    'APZelos/blamer.nvim',
    cond = not env.is_vscode(),
    event = "VeryLazy",  -- 遅延読み込み
    config = function()
      vim.g.blamer_enabled = 0  -- デフォルトでは無効（`:BlamerToggle`で有効化）
      vim.g.blamer_delay = 500
    end,
  },
}
