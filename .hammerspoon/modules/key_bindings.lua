local key_bindings = {}
local logger = hs.logger.new("key_bindings.lua", "debug")

local console_apps = {
  ["Terminal"] = false,
  ["iTerm2"] = true,
  ["WezTerm"] = true,
  ["kitty"] = true,
}

-- Slackで除外するキー（slack_bindings.luaで処理）
local slack_excluded_keys = {
  ["j"] = true,
  ["k"] = true,
  ["h"] = true,
  ["l"] = true,
  ["f"] = true,
  ["s"] = true,
  ["t"] = true, -- Cmd+Shift+T用
}

-- Ctrl/Cmdキーの入れ替えを行う
-- コンソールアプリ：c, v のみ入れ替え
-- 他のアプリ：全てのキーで入れ替え
local function swapCmdCtrl(event)
  local flags = event:getFlags()
  local key_code = event:getKeyCode()
  local key_char = hs.keycodes.map[key_code]

  local front_app = hs.application.frontmostApplication()
  local app_name = front_app:name()
  local is_console_app = console_apps[app_name]

  -- Slackの場合：除外キーはslack_bindings.luaで処理するのでスキップ
  -- Ctrl→Cmd変換もCmd→Ctrl変換も両方スキップ
  if app_name == "Slack" and slack_excluded_keys[key_char] then
    return false
  end

  -- コンソールアプリの場合：c, v のみ入れ替え対象
  if is_console_app then
    if key_char ~= "c" and key_char ~= "v" then
      return false  -- c, v 以外はそのまま通す
    end
  end

  -- Ctrl+キー → Cmd+キー に変換
  if flags["ctrl"] and not flags["cmd"] then
    local modifier_keys = { "cmd" }

    if flags["shift"] then
      table.insert(modifier_keys, "shift")
    end
    if flags["alt"] then
      table.insert(modifier_keys, "alt")
    end

    -- eventtapを一時停止してからキーストロークを発行
    key_bindings.eventtap:stop()
    hs.eventtap.keyStroke(modifier_keys, key_char, 0)
    key_bindings.eventtap:start()

    return true  -- 元のイベントをブロック
  end

  -- Cmd+キー → Ctrl+キー に変換
  if flags["cmd"] and not flags["ctrl"] then
    local modifier_keys = { "ctrl" }

    if flags["shift"] then
      table.insert(modifier_keys, "shift")
    end
    if flags["alt"] then
      table.insert(modifier_keys, "alt")
    end

    -- eventtapを一時停止してからキーストロークを発行
    key_bindings.eventtap:stop()
    hs.eventtap.keyStroke(modifier_keys, key_char, 0)
    key_bindings.eventtap:start()

    return true  -- 元のイベントをブロック
  end

  return false  -- それ以外は元のイベントをそのまま通す
end

function key_bindings.start()
  key_bindings.eventtap = hs.eventtap.new({ hs.eventtap.event.types.keyDown }, swapCmdCtrl)
  key_bindings.eventtap:start()
end

function key_bindings.stop()
  if key_bindings.eventtap then
    key_bindings.eventtap:stop()
    key_bindings.eventtap = nil
  end
end

return key_bindings
