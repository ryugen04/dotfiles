-- Luaバイトコードキャッシュを有効化（起動時間を約30%短縮）
vim.loader.enable()

-- 基本設定の初期化
local function init_base()
  vim.opt.fileencoding = 'utf-8'
  vim.g.mapleader = "\\"
  -- vim.g.maplocalleader = " "
  -- タイムアウト設定を大幅に調整
  vim.opt.timeout = true
  vim.opt.timeoutlen = 500 -- キーマッピングのタイムアウト時間
  vim.opt.ttimeoutlen = 0  -- キーコードのタイムアウト時間をゼロに

  -- インサートモードでのキー入力処理を高速化
  vim.opt.updatetime = 300 -- スワップファイル書き込みとCursorHoldイベント発火の時間

  -- 不要なプロバイダーとプラグインを無効化（起動時間短縮）
  local disabled = {
    -- プロバイダーの無効化
    loaded_python_provider = 0,
    loaded_perl_provider = 0,
    loaded_ruby_provider = 0,
    loaded_node_provider = 0,
    -- 不要な標準プラグインの無効化
    loaded_matchparen = 1,
    loaded_rrhelper = 1,
    loaded_vimball = 1,
    loaded_vimballPlugin = 1,
    loaded_getscript = 1,
    loaded_getscriptPlugin = 1,
    loaded_logipat = 1,
    loaded_2html_plugin = 1,
  }

  for key, val in pairs(disabled) do
    vim.g[key] = val
  end

  -- Python3のパス設定（必要な場合のみ）
  vim.g.python3_host_prog = '/usr/bin/python3'
end

-- 環境依存の設定初期化（最適化版）
local function init_env_specific()
  local deno_path = vim.fn.getenv('DENO_PATH')
  if deno_path ~= vim.NIL and deno_path ~= '' then
    vim.g["denops#deno"] = deno_path
  end
end

-- プロジェクト固有設定の読み込み（非同期化）
local function load_local_config()
  vim.defer_fn(function()
    local local_vimrc = vim.fn.getcwd() .. '/.nvim.lua'
    if vim.fn.filereadable(local_vimrc) == 1 then
      dofile(local_vimrc)
    end
  end, 0) -- 次のイベントループで実行
end

-- 初期化の実行
init_base()
init_env_specific()

-- core モジュールの読み込み
require('core.env')
require('core.options')
require('core.keys')
require('core.commands')

-- プラグイン関連の初期化
require("plugins")

-- ローカル設定の読み込み
load_local_config()
