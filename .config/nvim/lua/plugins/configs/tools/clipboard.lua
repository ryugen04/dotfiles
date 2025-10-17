return {
  {
    "michaelrommel/nvim-silicon",
    cond = not is_vscode,
    lazy = true,
    cmd = "Silicon",
    main = "nvim-silicon",
    opts = {
      -- Configuration here, or leave empty to use defaults
      line_offset = function(args)
        return args.line1
      end,
      to_clipboard = true,
      font = 'Cica',
      background = '#fff0',
      pad_horiz = 50,
      pad_vert = 40,
    }
  },
}
