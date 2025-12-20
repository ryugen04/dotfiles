-- OSに応じたmodifier keyを提供する共通モジュール
-- Linux: CTRL, macOS: CMD

local M = {}

-- wezterm専用: wezterm.target_tripleを使用してmodifier keyを決定
function M.get_mod_wezterm(wezterm)
  if wezterm.target_triple == 'x86_64-apple-darwin' or
     wezterm.target_triple == 'aarch64-apple-darwin' then
    return 'CMD'
  end
  return 'CTRL'
end

-- 汎用: uname コマンドでOSを判定してmodifier keyを決定
function M.get_mod()
  local handle = io.popen("uname -s 2>/dev/null")
  if handle then
    local result = handle:read("*a")
    handle:close()
    if result:match("Darwin") then
      return "CMD"
    end
  end
  -- デフォルトはCTRL (Linux)
  return "CTRL"
end

return M
