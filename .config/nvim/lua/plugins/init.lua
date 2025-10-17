local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- lazyの設定
local opts = {
  install = {
    colorscheme = { "nightfox" },
  },
  ui = {
    border = "rounded",
  },
  performance = {
    rtp = {
      disabled_plugins = {
        "gzip",
        "matchit",
        "matchparen",
        "netrwPlugin",
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },
  change_detection = {
    notify = false,
  },
}

-- lazyのセットアップ
require("lazy").setup({
  spec = {
    { import = "plugins.configs.ui" },
    { import = "plugins.configs.coding" },
    { import = "plugins.configs.editor" },
    { import = "plugins.configs.lang" },
    { import = "plugins.configs.tools" },
  }
}, opts)
