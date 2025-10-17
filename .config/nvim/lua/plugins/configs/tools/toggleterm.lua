return {
  -- ターミナル
  {
    'akinsho/toggleterm.nvim',
    cond = not env.is_vscode(),
    config = function()
      require("toggleterm").setup({
        open_mapping = [[<leader>ft]],
        size = 100,
        hide_numbers = true,
        shade_filetypes = {},
        shade_terminals = true,
        shading_factor = 2,
        start_in_insert = true,
        insert_mappings = true,
        persist_size = true,
        direction = 'float',
        close_on_exit = true,
      }
      )
    end,
    doc = "ターミナル"
  },
}
