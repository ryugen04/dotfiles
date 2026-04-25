#!/usr/bin/env bash
# PostToolUse hook: planファイル作成・更新時に右ペインで自動表示
# - .claude/plans/*.md → cmux markdown open (ライブリロードビューア)
# - .claude/work/**/*.md → cmux-nvim-right (nvimで編集可能)

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"

# cmux未起動なら何もしない
"$CMUX" ping &>/dev/null || exit 0

# hookのinputからファイルパスを取得
# PostToolUse hook の tool_input は JSON
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Write tool
    if 'file_path' in data.get('tool_input', {}):
        print(data['tool_input']['file_path'])
    # Edit tool
    elif 'file_path' in data.get('tool_input', {}):
        print(data['tool_input']['file_path'])
    else:
        print('')
except:
    print('')
" 2>/dev/null)

[[ -z "$FILE_PATH" ]] && exit 0

# planファイルの場合: cmux markdown viewer (ライブリロード)
if [[ "$FILE_PATH" == */.claude/plans/*.md ]]; then
  # 同一ファイルのmarkdown surfaceが既に開いていれば新規作成しない（重複防止）。
  # caller のワークスペース内のみを対象にし、title（basename）で一致判定する。
  CALLER_WS=$("$CMUX" identify 2>/dev/null \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('caller',{}).get('workspace_ref',''))" 2>/dev/null)
  BASENAME=$(basename "$FILE_PATH")
  TREE_JSON=$("$CMUX" rpc system.tree 2>/dev/null || true)
  EXISTING=""
  if [[ -n "$TREE_JSON" ]]; then
    EXISTING=$(CMUX_WS="$CALLER_WS" CMUX_NAME="$BASENAME" python3 -c "
import sys, json, os
try:
    data = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)
target_ws = os.environ.get('CMUX_WS','')
target_name = os.environ.get('CMUX_NAME','')
for w in data.get('windows', []):
    for ws in w.get('workspaces', []):
        if target_ws and ws.get('ref') != target_ws:
            continue
        for p in ws.get('panes', []):
            for s in p.get('surfaces', []):
                if s.get('type') == 'markdown' and s.get('title') == target_name:
                    print(s.get('ref',''))
                    sys.exit(0)
" <<<"$TREE_JSON" 2>/dev/null || true)
  fi
  if [[ -n "$EXISTING" ]]; then
    exit 0
  fi
  "$CMUX" markdown open "$FILE_PATH" &>/dev/null &
  exit 0
fi

# workディレクトリのMDの場合: 右ペインのnvimで開く
if [[ "$FILE_PATH" == */.claude/work/*.md ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  NVIM_RIGHT="$SCRIPT_DIR/../../../cmux/scripts/cmux-nvim-right.sh"
  if [[ -x "$NVIM_RIGHT" ]]; then
    "$NVIM_RIGHT" "$FILE_PATH" &>/dev/null &
  fi
  exit 0
fi

exit 0
