---
description: 'dotfilesプロジェクト固有のコーディングルール'
applyTo: '**/*'
---

# Dotfiles Project Rules

## Tech Stack
- Shell: Bash 5.x / Zsh 5.9
- Package Manager: GNU Stow
- Secrets: 1Password CLI

## File Structure
```
packages/
├── {tool}/           # stowパッケージ
│   └── .{tool}/      # ホーム配下の設定
└── shell/            # シェル共通設定
```

## Naming Conventions
- パッケージ名: lowercase-with-hyphens
- 環境変数: UPPER_SNAKE_CASE
- 関数名: snake_case

## Code Style Examples

### ✅ Good
```bash
#!/usr/bin/env bash
set -euo pipefail

readonly CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}"
```

### ❌ Bad
```bash
#!/bin/bash
CONFIG_DIR="/Users/username/.config"  # ハードコード禁止
```

## Security Rules
- 🚫 トークン直接記載禁止
- ✅ 1Password CLI使用: `op://vault/item/field`
