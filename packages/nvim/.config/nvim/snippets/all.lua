local ls = require('luasnip')
local s = ls.snippet
local t = ls.text_node
local i = ls.insert_node
local fmt = require("luasnip.extras.fmt").fmt

return {
  -- 例: 現在の日付を挿入
  s('date', {
    t(os.date('%Y-%m-%d'))
  }),

  -- 例: TODOコメント
  s('todo', {
    t('TODO: '),
    i(1, 'task description')
  }),

  -- Given-When-Thenテストコメント
  s('/*',
    fmt(
      [[
/**
 * given: {}
 */

/**
 * when: {}
 */

/**
 * then: {}
 */
      ]],
      { i(1, ""), i(2, ""), i(3, "") }
    )
  ),
}
