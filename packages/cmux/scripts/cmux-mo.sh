#!/usr/bin/env bash
# Markdown を cmux のネイティブ markdown ビューアで表示する。
#
# 振る舞い:
#   - 現在のワークスペースにフォーカス外のペインがあれば、そのペインに
#     新規タブ（surface）として markdown プレビューを追加する
#     → 3 ペイン以上に増殖しない
#   - フォーカス外ペインが無ければ、右に新規分割を作って表示する
#
# 旧実装（mo + port 6275 + browser open-split）は廃止。
# cmux 本体に markdown ビューア（ライブリロード付き）が追加されたため、
# 外部サーバーを立ち上げる必要はなくなった。

set -euo pipefail

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"

if [[ $# -lt 1 ]]; then
  echo "Usage: cmux-mo <markdown-file>" >&2
  exit 1
fi

FILE="$1"

# 相対パスを絶対パスに変換
if [[ ! "$FILE" = /* ]]; then
  FILE="$(pwd)/$FILE"
fi

if [[ ! -f "$FILE" ]]; then
  echo "File not found: $FILE" >&2
  exit 1
fi

if [[ ! -x "$CMUX" ]]; then
  echo "cmux CLI not found at $CMUX" >&2
  exit 1
fi

# list-panes 出力例:
#   * pane:35  [1 surface]  [focused]
#     pane:36  [1 surface]
#
# フォーカス印（[focused]）が付いていない最初のペイン参照を拾う。
TARGET_PANE="$(
  "$CMUX" list-panes 2>/dev/null | awk '
    /\[focused\]/ { next }
    {
      for (i = 1; i <= NF; i++) {
        if ($i ~ /^pane:[0-9]+$/) { print $i; exit }
      }
    }
  '
)"

if [[ -n "$TARGET_PANE" ]]; then
  # 既存ペインに新規タブとして開く（分割しない）
  "$CMUX" open "$FILE" --pane "$TARGET_PANE"
  echo "OK opened=$FILE pane=$TARGET_PANE placement=tab"
else
  # フォーカス外ペインが無いので、右に分割して markdown ビューアを置く
  "$CMUX" markdown "$FILE" --direction right
  echo "OK opened=$FILE placement=split"
fi
