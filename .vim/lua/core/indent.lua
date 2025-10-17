-- core/indent.lua
-- 言語ごとのインデント設定

local M = {}

-- 言語ごとのインデントサイズ設定
local indent_settings = {
  -- 4スペース
  python = 4,
  java = 4,
  kotlin = 4,
  c = 4,
  cpp = 4,
  rust = 4,
  go = 4,

  -- 2スペース
  lua = 2,
  javascript = 2,
  typescript = 2,
  javascriptreact = 2,
  typescriptreact = 2,
  html = 2,
  css = 2,
  scss = 2,
  json = 2,
  yaml = 2,
  markdown = 2,
  ruby = 2,
  vim = 2,
  sh = 2,
  bash = 2,
  zsh = 2,

  -- タブ文字を使用
  go = { indent = 'tab', tabstop = 4 },
  make = { indent = 'tab', tabstop = 8 },
}

function M.setup()
  vim.api.nvim_create_autocmd('FileType', {
    pattern = '*',
    callback = function()
      local filetype = vim.bo.filetype
      local setting = indent_settings[filetype]

      if setting then
        if type(setting) == 'number' then
          -- スペースインデント
          vim.bo.tabstop = setting
          vim.bo.shiftwidth = setting
          vim.bo.softtabstop = setting
          vim.bo.expandtab = true
        elseif type(setting) == 'table' then
          -- タブインデント
          if setting.indent == 'tab' then
            vim.bo.tabstop = setting.tabstop
            vim.bo.shiftwidth = setting.tabstop
            vim.bo.softtabstop = 0
            vim.bo.expandtab = false
          end
        end
      end
    end,
    desc = 'Set indent size per filetype'
  })
end

return M
