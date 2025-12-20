return {
  -- 基本編集機能
  {
    'andymass/vim-matchup',
    event = 'CursorMoved',
    config = function()
    
  -- オフスクリーンのマッチング表示設定
  vim.g.matchup_matchparen_offscreen = {
    method = 'popup',
    fullwidth = true,     -- ポップアップを全幅で表示
    highlight = 'Normal', -- ポップアップのハイライト
    border = 'rounded'    -- ポップアップのボーダースタイル
  }

  -- マッチングの動作設定
  vim.g.matchup_matching_keytags = {
    '(:)',      -- 括弧
    '{:}',      -- 中括弧
    '[:]',      -- 角括弧
    '<:>',      -- 山括弧
    'start:end' -- start/end
  }

  -- 移動時の挙動設定
  vim.g.matchup_motion_enabled = true    -- モーション機能を有効化
  vim.g.matchup_text_obj_enabled = true  -- テキストオブジェクトを有効化
  vim.g.matchup_surround_enabled = true  -- サラウンド機能を有効化
  vim.g.matchup_transmute_enabled = true -- 対応する括弧の変換を有効化

  -- パフォーマンス設定
  vim.g.matchup_delim_noskips = 2              -- コメント内でのマッチングを制御
  vim.g.matchup_matchparen_deferred = 1        -- 遅延ロードを有効化
  vim.g.matchup_matchparen_timeout = 300       -- タイムアウト時間（ミリ秒）
  vim.g.matchup_matchparen_insert_timeout = 60 -- 挿入モードでのタイムアウト時間

  -- 表示設定
  vim.g.matchup_matchparen_hi_surround_always = 1   -- サラウンドのハイライトを常に表示
  vim.g.matchup_matchparen_deferred_show_delay = 50 -- ハイライト表示の遅延時間

  -- 特定のファイルタイプでの無効化
  vim.g.matchup_matchparen_nomode = "i"    -- 挿入モードでは無効
  vim.g.matchup_matchparen_fallback = true -- フォールバックを有効化
    end,
    doc = "対応する括弧等のジャンプ"
  },
}
