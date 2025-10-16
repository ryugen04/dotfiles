-- yaziのキーバインディングをOSに応じて設定するモジュール
local common_mod = require('common.mod')

local M = {}

-- modifier keyを取得
M.mod = common_mod.get_mod()

-- modifier keyの文字列表現を取得
function M.get_mod_key()
  if M.mod == "CMD" then
    return "Cmd"  -- yaziではCmd表記
  else
    return "Ctrl"  -- yaziではCtrl表記
  end
end

-- キーコンビネーションを生成
function M.key(key, with_mod)
  if with_mod then
    return "<" .. M.get_mod_key() .. "-" .. key .. ">"
  else
    return key
  end
end

return M
