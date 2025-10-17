return {
  -- 基本編集機能
  {
    'monaqa/dial.nvim',
    config = function()
    
  local augend = require("dial.augend")
  require("dial.config").augends:register_group {
    default = {
      augend.integer.alias.decimal,
      augend.integer.alias.hex,
      augend.date.alias["%Y/%m/%d"],
      augend.date.alias["%Y-%m-%d"],
      augend.date.alias["%Y年%-m月%-d日"],
      augend.date.alias["%Y年%-m月%-d日(%ja)"],
      augend.constant.alias.ja_weekday,
      augend.constant.alias.ja_weekday_full,
      augend.constant.alias.bool,
      augend.semver.alias.semver,
    },
    typescript = {
      augend.integer.alias.decimal,
      augend.integer.alias.hex,
      augend.constant.new { elements = { "let", "const" } },
    },
    visual = {
      augend.integer.alias.decimal,
      augend.integer.alias.hex,
      augend.date.alias["%Y/%m/%d"],
      augend.constant.alias.alpha,
      augend.constant.alias.alpha,
    },
  }
    end,
    doc = "数値やテキストのインクリメント"
  },
}
