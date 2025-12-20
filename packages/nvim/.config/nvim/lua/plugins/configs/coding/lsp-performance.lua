-- LSPパフォーマンス最適化設定
-- これらの設定はプラグインとしてではなく、直接実行する

-- LSPのデバウンス設定（診断更新の遅延）
vim.diagnostic.config({
  update_in_insert = false,  -- インサートモード中は診断を更新しない
  virtual_text = {
    spacing = 4,
    prefix = '●',
  },
  severity_sort = true,
  float = {
    border = 'rounded',
    source = 'always',
  },
})

-- LSPのログレベルを下げる（パフォーマンス向上）
vim.lsp.set_log_level('ERROR')

-- LSPの更新頻度を調整
vim.opt.updatetime = 300  -- CursorHoldイベントの頻度（デフォルト4000ms → 300ms）

-- 空のテーブルを返す（プラグイン定義ではないため）
return {}
