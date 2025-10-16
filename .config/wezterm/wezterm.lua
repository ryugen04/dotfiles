local wezterm = require 'wezterm';

-- commonディレクトリへのパスを追加
local config_dir = wezterm.config_dir or os.getenv("HOME") .. "/.config/wezterm"
package.path = package.path .. ";" .. config_dir .. "/../?.lua;" .. config_dir .. "/../?/init.lua"

local common_mod = require('common.mod')

-- OSに応じたmodifier keyを設定
local mod = common_mod.get_mod_wezterm(wezterm)

local opacity_toggle = {
  is_transparent = true,
  transparent = 0.6,
  opaque = 1.0,
}
return {
  default_prog = { "/bin/bash", "-l" },
  font = wezterm.font("Cica"),
  use_ime = true,
  xim_im_name = 'fcitx5',
  font_size = 14.0,
  default_cursor_style = 'SteadyBlock',
  color_scheme = "nightfox", -- find your favorite theme, https://wezfurlong.org/wezterm/colorschemes/index.html
  hide_tab_bar_if_only_one_tab = false,
  adjust_window_size_when_changing_font_size = false,
  audible_bell = "Disabled",
  disable_default_key_bindings = true,
  enable_tab_bar = true,
  enable_kitty_keyboard = true,
  window_background_opacity = 0.6,
  -- leader keyの設定: mod + a
  leader = {
    key = 'a',
    mods = mod,
    timeout_milliseconds = 1000,
  },
  -- defaultだとvimを開いたときなどに余白が生じる
  window_padding = {
    left = 0,
    right = 0,
    top = 0,
    bottom = 0
  },
  check_for_updates = false,
  mouse_bindings = {
    -- 右クリックでクリップボードから貼り付け
    {
      event = { Down = { streak = 1, button = 'Right' } },
      mods = 'NONE',
      action = wezterm.action.PasteFrom 'Clipboard',
    },
  },
  -- keymap
  keys = {
    -- leader + aで実際のCtrl-a/Cmd-aを送信
    {
      key = 'a',
      mods = 'LEADER |' .. mod ,
      action = wezterm.action.SendKey { key = 'a', mods = mod }
    },
    -- 新規タブ作成: leader + t
    {
      key = 't',
      mods = 'LEADER',
      action = wezterm.action.SpawnCommandInNewTab {
        domain = 'CurrentPaneDomain'
      },
    },
    -- タブを閉じる: leader + w
    {
      key = 'w',
      mods = 'LEADER',
      action = wezterm.action.CloseCurrentTab {
        confirm = false
      },
    },
    -- ペインを閉じる: leader + q
    {
      key = 'q',
      mods = 'LEADER',
      action = wezterm.action.CloseCurrentPane {
        confirm = false
      }
    },
    -- 縦分割: leader + -
    {
      key = '-',
      mods = 'LEADER',
      action = wezterm.action.SplitVertical {
        domain = 'CurrentPaneDomain'
      }
    },
    -- 横分割: leader + |
    {
      key = '/',
      mods = 'LEADER',
      action = wezterm.action.SplitHorizontal {
        domain = 'CurrentPaneDomain'
      }
    },
    -- ペイン選択: leader + s
    {
      key = 's',
      mods = 'LEADER',
      action = wezterm.action.PaneSelect {
        mode = 'Activate'
      }
    },
    -- 前のタブ: leader + [
    {
      key = '[',
      mods = 'LEADER',
      action = wezterm.action.ActivateTabRelative(-1)
    },
    -- 次のタブ: leader + ]
    {
      key = ']',
      mods = 'LEADER',
      action = wezterm.action.ActivateTabRelative(1)
    },
    -- タブ名変更: leader + r
    {
      key = 'r',
      mods = 'LEADER',
      action = wezterm.action.PromptInputLine {
        description = "Enter new name for tab",
        action = wezterm.action_callback(function(window, pane, line)
          if line then
            window:active_tab():set_title(line)
          end
        end),
      }
    },
    -- コピー: leader + v
    {
      key = 'v',
      mods = 'LEADER',
      action = wezterm.action_callback(function(window, pane)
        local word = window:get_selection_escapes_for_pane(pane)
        window:copy_to_clipboard(word)
      end)
    },
    {
      key = 'v',
      mods = mod .. '|SHIFT',
      action = wezterm.action.PasteFrom 'Clipboard'
    },
    -- 透明度切り替え: leader + g
    {
      key = 'g',
      mods = 'LEADER',
      action = wezterm.action_callback(function(window, pane)
        local overrides = window:get_config_overrides() or {}
        if opacity_toggle.is_transparent then
          -- Switch to opaque
          overrides.window_background_opacity = opacity_toggle.opaque
          opacity_toggle.is_transparent = false
        else
          -- Switch to transparent
          overrides.window_background_opacity = opacity_toggle.transparent
          opacity_toggle.is_transparent = true
        end
        window:set_config_overrides(overrides)
      end)
    },
    -- ペイン移動: leader + hjkl (vim風)
    {
      key = 'h',
      mods = 'LEADER',
      action = wezterm.action.ActivatePaneDirection('Left')
    },
    {
      key = 'j',
      mods = 'LEADER',
      action = wezterm.action.ActivatePaneDirection('Down')
    },
    {
      key = 'k',
      mods = 'LEADER',
      action = wezterm.action.ActivatePaneDirection('Up')
    },
    {
      key = 'l',
      mods = 'LEADER',
      action = wezterm.action.ActivatePaneDirection('Right')
    },
    -- Shift + Enter で改行
    {
      key = 'Enter',
      mods = 'SHIFT',
      action = wezterm.action.SendString("\n")
    }
  },
  colors = {
    cursor_bg = '#52ad70',
    tab_bar = {
      -- The color of the strip that goes along the top of the window
      --
      -- (does not apply when fancy tab bar is in use)
      inactive_tab_edge = '#575757',
      -- The active tab is the one that has focus in the window
      active_tab = {
        -- The color of the background area for the tab
        bg_color = '#3b7070',
        -- The color of the text for the tab
        fg_color = '#dcffff',

        -- Specify whether you want "Half", "Normal" or "Bold" intensity for the
        -- label shown for this tab.
        -- The default is "Normal"
        intensity = 'Normal',

        -- Specify whether you want "None", "Single" or "Double" underline for
        -- label shown for this tab.
        -- The default is "None"
        underline = 'None',

        -- Specify whether you want the text to be italic (true) or not (false)
        -- for this tab.  The default is false.
        italic = false,

        -- Specify whether you want the text to be rendered with strikethrough (true)
        -- or not for this tab.  The default is false.
        strikethrough = false,
      },

      -- Inactive tabs are the tabs that do not have focus
      inactive_tab = {
        bg_color = '#5c5c5c',
        fg_color = '#3a3939',

        -- The same options that were listed under the `active_tab` section above
        -- can also be used for `inactive_tab`.
      },

      -- You can configure some alternate styling when the mouse pointer
      -- moves over inactive tabs
      inactive_tab_hover = {
        bg_color = '#3b3052',
        fg_color = '#909090',
        italic = true,
        -- The same options that were listed under the `active_tab` section above
        -- can also be used for `inactive_tab_hover`.
      },

      -- The new tab button that let you create new tabs
      new_tab = {
        bg_color = '#808080',
        fg_color = '#4d4d4d',

        -- The same options that were listed under the `active_tab` section above
        -- can also be used for `new_tab`.
      },

      -- You can configure some alternate styling when the mouse pointer
      -- moves over the new tab button
      new_tab_hover = {
        bg_color = '#3b3052',
        fg_color = '#909090',
        italic = true,
        -- The same options that were listed under the `active_tab` section above
        -- can also be used for `new_tab_hover`.
      },
    },
  },
}
