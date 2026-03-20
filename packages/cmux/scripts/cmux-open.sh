#!/usr/bin/env bash
# cmuxブラウザでURLを開く（プリセット対応）

set -euo pipefail

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRESETS_FILE="$SCRIPT_DIR/../presets.yaml"

if [[ $# -lt 1 ]]; then
  echo "Usage: cmux-open <preset|URL|local:path>"
  echo ""
  echo "Examples:"
  echo "  cmux-open https://example.com"
  echo "  cmux-open dashboard"
  echo "  cmux-open local:api/users"
  exit 1
fi

ARG="$1"

# URL解決
resolve_url() {
  local input="$1"

  # URL形式（http:// or https://）
  if [[ "$input" =~ ^https?:// ]]; then
    echo "$input"
    return
  fi

  # local:形式 → localhost展開
  if [[ "$input" =~ ^local: ]]; then
    local path="${input#local:}"
    local port=3000

    # presets.yamlからポート取得（存在すれば）
    if [[ -f "$PRESETS_FILE" ]] && command -v yq &> /dev/null; then
      local custom_port
      custom_port=$(yq '.local.port' "$PRESETS_FILE" 2>/dev/null || true)
      if [[ -n "$custom_port" && "$custom_port" != "null" ]]; then
        port="$custom_port"
      fi
    fi

    echo "http://localhost:${port}/${path}"
    return
  fi

  # プリセット名 → presets.yamlから解決
  if [[ -f "$PRESETS_FILE" ]]; then
    if command -v yq &> /dev/null; then
      local preset_url
      preset_url=$(yq ".presets.${input}" "$PRESETS_FILE" 2>/dev/null || true)
      if [[ -n "$preset_url" && "$preset_url" != "null" ]]; then
        echo "$preset_url"
        return
      fi
    else
      echo "yq not found. Install with: brew install yq" >&2
      exit 1
    fi
  fi

  echo "Unknown preset: $input" >&2
  echo "Available presets:" >&2
  if [[ -f "$PRESETS_FILE" ]] && command -v yq &> /dev/null; then
    yq -r '.presets | keys | .[]' "$PRESETS_FILE" 2>/dev/null | sed 's/^/  - /' >&2
  fi
  exit 1
}

URL=$(resolve_url "$ARG")

# cmuxブラウザで開く
if [[ -x "$CMUX" ]]; then
  "$CMUX" browser open-split "$URL" 2>/dev/null || \
    echo "Open in browser: $URL"
else
  echo "Open in browser: $URL"
fi
