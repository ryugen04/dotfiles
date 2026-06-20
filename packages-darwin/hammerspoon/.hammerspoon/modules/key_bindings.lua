local key_bindings = {}
local logger = hs.logger.new("key_bindings.lua", "debug")
local pasteboard = require("hs.pasteboard")

local console_apps = {
  ["Terminal"] = false,
  ["iTerm2"] = true,
  ["WezTerm"] = true,
  ["kitty"] = true,
  ["cmux"] = true,
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

-- 全アプリでCtrl↔Cmdスワップから除外するキー
-- Ctrl+Spaceは入力切替としてどのアプリでも統一
local swap_excluded_keys = {
  ["space"] = true,
}

local console_app_bundle_ids = {
  ["net.kovidgoyal.kitty"] = true,
}

local image_pasteboard_types = {
  ["com.apple.icns"] = true,
  ["com.apple.pict"] = true,
  ["com.apple.tiff"] = true,
  ["public.bmp"] = true,
  ["public.gif"] = true,
  ["public.heic"] = true,
  ["public.heif"] = true,
  ["public.image"] = true,
  ["public.jpeg"] = true,
  ["public.png"] = true,
  ["public.svg-image"] = true,
  ["public.tiff"] = true,
}

local function isKitty(app_name, bundle_id)
  return app_name == "kitty" or console_app_bundle_ids[bundle_id] == true
end

local function clipboardHasImage()
  if not pasteboard or not pasteboard.contentTypes then
    return false
  end

  local ok, types = pcall(pasteboard.contentTypes)
  if not ok or type(types) ~= "table" then
    return false
  end

  for _, pasteboard_type in ipairs(types) do
    local normalized = string.lower(tostring(pasteboard_type))
    if image_pasteboard_types[normalized] or normalized:find("image", 1, true) then
      return true
    end
  end

  return false
end

local function handleKittyPaste(key_char, flags)
  if key_char ~= "v" or not flags["cmd"] or flags["ctrl"] or flags["alt"] then
    return false
  end

  if flags["shift"] then
    return false
  end

  if not clipboardHasImage() then
    return false
  end

  -- kitty maps Cmd+Shift+V to send Ctrl-V to the terminal child.
  -- Use that path for image clipboards so TUIs such as Claude Code can handle image paste,
  -- while text/VoiceInk clipboards continue through normal Cmd+V paste.
  key_bindings.eventtap:stop()
  hs.eventtap.keyStroke({ "cmd", "shift" }, "v", 0)
  key_bindings.eventtap:start()

  return true
end

-- Ctrl/Cmdキーの入れ替えを行う
-- コンソールアプリ：c, v のみ入れ替え
-- 他のアプリ：全てのキーで入れ替え
local function swapCmdCtrl(event)
  local flags = event:getFlags()
  local key_code = event:getKeyCode()
  local key_char = hs.keycodes.map[key_code]

  local front_app = hs.application.frontmostApplication()
  local app_name = front_app and front_app:name() or ""
  local bundle_id = front_app and front_app:bundleID() or ""
  local is_console_app = console_apps[app_name] or console_app_bundle_ids[bundle_id] == true

  if not key_char then
    return false
  end

  if isKitty(app_name, bundle_id) and handleKittyPaste(key_char, flags) then
    return true
  end

  -- 全アプリ共通：スワップ除外キーはそのまま通す
  if swap_excluded_keys[key_char] then
    return false
  end

  -- Slackの場合：除外キーはslack_bindings.luaで処理するのでスキップ
  -- Ctrl→Cmd変換もCmd→Ctrl変換も両方スキップ
  if app_name == "Slack" and slack_excluded_keys[key_char] then
    return false
  end

  -- コンソールアプリの場合：c, v のみ入れ替え対象
  if is_console_app then
    -- if key_char ~= "c" and key_char ~= "v" then
    --   return false  -- c, v 以外はそのまま通す
    -- end
    return false
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
  -- ただしCmd+Vはペースト（VoiceInk等の音声入力）のためそのまま通す
  if flags["cmd"] and not flags["ctrl"] then
    if key_char == "v" then
      return false  -- Cmd+V はmacOSペーストとしてそのまま通す
    end

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
