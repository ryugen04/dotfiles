local key_bindings = require "modules.key_bindings"
local window_management = require "modules.window_manager"

-- Caps LockをHyper Key (ctrl + shift + cmd + option)にマッピング
-- Hammerspoon単体で実装
local capslock_pressed = false
local capslock_used_as_modifier = false

local caps_to_hyper = hs.eventtap.new(
  { hs.eventtap.event.types.flagsChanged, hs.eventtap.event.types.keyDown },
  function(event)
    local keyCode = event:getKeyCode()
    local flags = event:getFlags()
    local eventType = event:getType()

    -- Caps Lockのキーコードは57
    if keyCode == 57 then
      if eventType == hs.eventtap.event.types.flagsChanged then
        if flags.capslock then
          -- Caps Lockが押された
          capslock_pressed = true
          capslock_used_as_modifier = false
        else
          -- Caps Lockが離された
          if not capslock_used_as_modifier then
            -- 単独で押された場合は何もしない（Caps Lock機能を無効化）
          end
          capslock_pressed = false
        end
        return true -- Caps Lockのイベントをブロック
      end
    end

    -- 他のキーが押された時、Caps Lockが押されていればHyper Keyとして扱う
    if capslock_pressed and eventType == hs.eventtap.event.types.keyDown and keyCode ~= 57 then
      capslock_used_as_modifier = true
      local key_char = hs.keycodes.map[keyCode]

      if key_char then
        -- Hyper Key (ctrl + shift + cmd + alt) + 押されたキーを送信
        local modifiers = { "ctrl", "shift", "cmd", "alt" }

        caps_to_hyper:stop()
        hs.eventtap.keyStroke(modifiers, key_char, 0)
        caps_to_hyper:start()

        return true -- 元のイベントをブロック
      end
    end

    return false
  end
)

caps_to_hyper:start()

-- keyBindigsを有効化する
key_bindings.start()

hs.reload = function()
  key_bindings.stop()
  hs.reload()
end
--
-- window_managementのキーバインディングを有効化する
-- hs.hotkey.bind({"option"}, "Left", window_management.moveWindowLeft)
-- hs.hotkey.bind({"option"}, "Right", window_management.moveWindowRight)
-- hs.hotkey.bind({"option"}, "Up", window_management.maximizeWindow)
-- hs.hotkey.bind({"optionn"}, "Down", window_management.minimizeWindow)
-- hs.hotkey.bind({"option", "shift"}, "Left", window_management.moveWindowNextScreen)
-- hs.hotkey.bind({"option", "shift"}, "Right", window_management.moveWindowPrevScreen)
