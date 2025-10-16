require("full-border"):setup()
require("git"):setup()

-- OSに応じたmodifier keyの設定
local keybindings = require("keybindings")

-- 使用例:
-- keybindings.mod で "CTRL" または "CMD" を取得
-- keybindings.key("c", true) で "<Ctrl-c>" または "<Cmd-c>" を取得
