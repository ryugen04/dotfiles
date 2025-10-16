-- ランタイムパフォーマンス最適化
-- このファイルは追加のパフォーマンス改善設定を提供します

-- インサートモード中のカーソル移動を最適化
vim.api.nvim_create_autocmd("InsertEnter", {
  callback = function()
    -- インサートモード中は相対行番号を無効化（描画コスト削減）
    vim.opt.relativenumber = false
  end,
})

vim.api.nvim_create_autocmd("InsertLeave", {
  callback = function()
    -- ノーマルモードに戻ったら相対行番号を有効化
    vim.opt.relativenumber = true
  end,
})

-- 大規模バッファでの自動最適化
vim.api.nvim_create_autocmd("BufReadPre", {
  callback = function()
    local line_count = vim.fn.line('$')
    if line_count > 10000 then
      -- 10000行以上のファイルで最適化
      vim.opt_local.foldmethod = 'manual'  -- 高度なfoldingを無効化
      vim.opt_local.relativenumber = false  -- 相対行番号を無効化
      vim.opt_local.cursorline = false      -- カーソルラインハイライトを無効化
      vim.notify("大規模ファイル検出: パフォーマンス最適化を適用", vim.log.levels.INFO)
    end
  end,
})

-- GitSigns等のプラグインの更新頻度を調整
vim.opt.updatetime = 300  -- デフォルト4000ms → 300ms（適度なバランス）

return {}
