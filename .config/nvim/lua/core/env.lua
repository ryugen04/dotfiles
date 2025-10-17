local M = {}

-- OS/環境判定関数
function M.is_windows()
  return vim.fn.has('win32') == 1 or vim.fn.has('win64') == 1
end

function M.is_mac()
  return vim.fn.has('macunix') == 1
end

function M.is_linux()
  return vim.fn.has('unix') == 1 and not M.is_mac() and not M.is_wsl()
end

function M.is_wsl()
  local output = vim.fn.systemlist "uname -r"
  return not not string.find(output[1] or "", "WSL")
end

-- エディタ環境の判定
function M.is_vscode()
  return vim.g.vscode ~= nil
end

function M.is_gui()
  return vim.fn.has('gui_running') == 1
end

function M.is_terminal()
  return not M.is_gui() and not M.is_vscode()
end

-- 機能サポートの判定
function M.has_python()
  return vim.fn.has('python3') == 1
end

function M.has_node()
  return vim.fn.executable('node') == 1
end

function M.has_deno()
  return vim.fn.executable('deno') == 1
end

-- システムパスの取得
function M.get_separator()
  if M.is_windows() then
    return '\\'
  end
  return '/'
end

function M.get_config_path()
  return vim.fn.stdpath('config')
end

function M.get_data_path()
  return vim.fn.stdpath('data')
end

function M.get_cache_path()
  return vim.fn.stdpath('cache')
end

-- 環境変数の取得（存在確認付き）
function M.get_env(name)
  local value = vim.fn.getenv(name)
  if value and value ~= "" then
    return value
  end
  return nil
end

-- 条件に応じた設定値の選択
function M.select_by_os(opts)
  if M.is_windows() and opts.windows then
    return opts.windows
  elseif M.is_mac() and opts.mac then
    return opts.mac
  elseif M.is_wsl() and opts.wsl then
    return opts.wsl
  elseif M.is_linux() and opts.linux then
    return opts.linux
  end
  return opts.default
end

-- グローバルに利用可能にする
_G.env = M

return M
