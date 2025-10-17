local env = require('core.env')

local function setup()
  -- キーマップのユーティリティ関数
  local function map(mode, lhs, rhs, opts)
    opts = opts or {}
    opts.silent = opts.silent ~= false
    vim.keymap.set(mode, lhs, rhs, opts)
  end

  -- ESC mappings
  map('i', 'jj', '<esc>')
  map('i', 'っj', '<esc>') -- 日本語入力対応

  -- 編集操作
  map('i', '<c-o>', '<left><c-o>')

  -- ウィンドウ操作
  map('n', '<c-h>', '<cmd>wincmd h<cr>')
  map('n', '<c-j>', '<cmd>wincmd j<cr>')
  map('n', '<c-k>', '<cmd>wincmd k<cr>')
  map('n', '<c-l>', '<cmd>wincmd l<cr>')

  -- コマンドライン
  map('n', ';', ':')

  -- ターミナル操作
  map('t', '<c-q>', '<c-\\><c-n><cmd>quit<cr>')
  map('t', '<esc>', '<c-\\><c-n>')

  -- パス関連
  map('n', '<c-p>', function()
    local path = vim.fn.expand('%:p')
    vim.fn.setreg('*', path)
    vim.fn.setreg('+', path)
    vim.notify('Copied: ' .. path)
  end)

  -- ファイル操作
  map('n', '%', function()
    vim.cmd.source('%')
    vim.notify('Source % done.')
  end)

  -- copy/paste
  map('i', '<leader>v', '<C-r>+')

  -- バッファ操作
  map('n', '<S-l>', function() vim.cmd.bnext() end)
  map('n', '<S-h>', function() vim.cmd.bprevious() end)

  -- インデント時の選択維持
  map('v', '<', function()
    vim.cmd('normal! <')
    vim.cmd('normal! gv')
  end)
  map('v', '>', function() 
    vim.cmd('normal! >')
    vim.cmd('normal! gv')
  end)

  -- 行移動
  map('v', 'J', function()
    vim.cmd.move('">+1"')
    vim.cmd.normal('gv=gv')
  end)
  map('v', 'K', function()
    vim.cmd.move('"<-2"')
    vim.cmd.normal('gv=gv')
  end)

  -- 検索
  map('n', '<ESC>', function() vim.cmd.nohlsearch() end)
  map('n', 'n', 'nzzzv')
  map('n', 'N', 'Nzzzv')

  -- 便利な操作
  map('n', 'J', function()
    vim.cmd.normal('mzJ`z')
  end)

  -- ターミナルモード
  map('t', '<C-h>', '<C-\\><C-N><cmd>wincmd h<cr>')
  map('t', '<C-j>', '<C-\\><C-N><cmd>wincmd j<cr>')
  map('t', '<C-k>', '<C-\\><C-N><cmd>wincmd k<cr>')
  map('t', '<C-l>', '<C-\\><C-N><cmd>wincmd l<cr>')
  map('t', '<ESC>', '<C-\\><C-n>')

  -- 環境固有のマッピング
  if env.is_vscode() then
    -- VSCode Neovim固有のキーマップ
    map('n', '<leader>f', function() vim.fn.VSCodeNotify("workbench.action.quickOpen") end)
    map('n', '<leader>e', function() vim.fn.VSCodeNotify("workbench.action.toggleSidebarVisibility") end)
  end

  -- OS固有のマッピング
  if env.is_mac() then
    map('n', '<D-s>', function() vim.cmd.write() end)
  end

  -- 無効化するキーマップ
  map('n', 'Q', '<nop>')
  map('n', '<Space>', '<nop>')
end

setup()

return {
  setup = setup
}
