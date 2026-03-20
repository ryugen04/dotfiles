return {
  dir = vim.fn.expand('~/dev/projects/cmux-navigator.nvim'),
  name = 'cmux-navigator',
  lazy = false,
  cond = function()
    return require('core.env').is_cmux()
  end,
  config = function()
    require('cmux-navigator').setup()
  end,
}
