return {
  -- ナビゲーション
  {
    'hadronized/hop.nvim',
    config = function()
    
  local hop = require("hop")
  hop.setup {
    multi_windows = true,
  }
    end,
    doc = "クイックジャンプ"
  },
}
