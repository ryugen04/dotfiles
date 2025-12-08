local slack_bindings = {}
local logger = hs.logger.new("slack_bindings", "debug")

-- Slack専用のキーバインディング
-- Ctrl+j → 下のスレッド (↓)
-- Ctrl+k → 上のスレッド (↑)
-- Ctrl+h → 前のチャンネル (Option+↑)
-- Ctrl+l → 次のチャンネル (Option+↓)
-- Ctrl+f → チャンネル検索 (Cmd+K)
-- Ctrl+s → スレッドへ移動 (Cmd+Shift+T)

local slack_key_map = {
  ["j"] = { mods = {}, key = "down" },
  ["k"] = { mods = {}, key = "up" },
  ["h"] = { mods = { "alt" }, key = "up" },
  ["l"] = { mods = { "alt" }, key = "down" },
  ["f"] = { mods = { "cmd" }, key = "k" },
  ["s"] = { mods = { "cmd", "shift" }, key = "t" },
}

local function isSlack()
  local front_app = hs.application.frontmostApplication()
  return front_app and front_app:name() == "Slack"
end

local function handleSlackBindings(event)
  if not isSlack() then
    return false
  end

  local flags = event:getFlags()
  local key_code = event:getKeyCode()
  local key_char = hs.keycodes.map[key_code]

  -- Ctrl単独で押されている場合のみ処理
  if flags["ctrl"] and not flags["cmd"] and not flags["alt"] and not flags["shift"] then
    local mapping = slack_key_map[key_char]
    if mapping then
      logger.d("Slack binding triggered: Ctrl+" .. key_char .. " -> " .. mapping.key)
      slack_bindings.eventtap:stop()
      hs.eventtap.keyStroke(mapping.mods, mapping.key, 0)
      slack_bindings.eventtap:start()
      return true
    else
      logger.d("No mapping found for: " .. (key_char or "nil"))
    end
  end

  return false
end

function slack_bindings.start()
  slack_bindings.eventtap = hs.eventtap.new({ hs.eventtap.event.types.keyDown }, handleSlackBindings)
  slack_bindings.eventtap:start()
end

function slack_bindings.stop()
  if slack_bindings.eventtap then
    slack_bindings.eventtap:stop()
    slack_bindings.eventtap = nil
  end
end

return slack_bindings
