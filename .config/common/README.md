# 共通設定モジュール

dotfile全体で使用できる共通の設定モジュール

## mod.lua

OSに応じたmodifier keyを提供するモジュール

- **Linux**: `CTRL`
- **macOS**: `CMD`

### 使用方法

#### wezterm (Lua)

```lua
local wezterm = require 'wezterm'
local common_mod = require('common.mod')

local mod = common_mod.get_mod_wezterm(wezterm)

-- キーバインドで使用
keys = {
  {
    key = 't',
    mods = mod .. '|SHIFT',
    action = wezterm.action.SpawnCommandInNewTab { domain = 'CurrentPaneDomain' }
  }
}
```

#### yazi (Lua)

```lua
local keybindings = require("keybindings")

-- modifier keyを取得
local mod = keybindings.mod  -- "CTRL" または "CMD"

-- キーコンビネーションを生成
local key_with_mod = keybindings.key("c", true)  -- "<Ctrl-c>" または "<Cmd-c>"
local key_without_mod = keybindings.key("h", false)  -- "h"
```

#### lazygit (YAML + シェルスクリプト)

lazygitはYAML形式のため、テンプレートから設定を生成する方式を採用

1. `config.yml.template` にテンプレートを記述
2. `{{MOD_KEY}}` でmodifier keyのプレースホルダーを使用
3. `./generate_config.sh` を実行して `config.yml` を生成

```yaml
# config.yml.template
customCommands:
  - key: "{{MOD_KEY}}-c"
    context: "files"
    description: 'commit files with format'
```

```bash
# 設定ファイル生成
cd ~/.config/lazygit
./generate_config.sh
```

#### 他のLua設定

```lua
local common_mod = require('common.mod')
local mod = common_mod.get_mod()  -- "CTRL" または "CMD"
```

## ディレクトリ構成

```
.config/
├── common/
│   ├── mod.lua              # 共通のmodifier key設定
│   └── README.md            # このファイル
├── wezterm/
│   └── wezterm.lua
├── yazi/
│   ├── init.lua
│   └── keybindings.lua      # yaziのキーバインド設定
└── lazygit/
    ├── config.yml
    ├── config.yml.template
    └── generate_config.sh
```
