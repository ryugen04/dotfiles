return {
  -- 基本編集機能
  {
    'numToStr/Comment.nvim',
    cond = not env.is_vscode(),
    config = function()
    
  local comment = require('Comment')
  comment.setup()
    end,
    doc = "コメントアウト"
  },
}
