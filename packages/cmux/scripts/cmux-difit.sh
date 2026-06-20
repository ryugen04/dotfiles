#!/usr/bin/env bash
# Git diffをcmuxブラウザで表示
# 参考: https://gist.github.com/azu/cef84c98aeef832d43dfb640c7e321f5

set -euo pipefail

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIFIT="${SCRIPT_DIR}/../node_modules/.bin/difit"
PORT=4966
BRIDGE_PORT=$((PORT + 1))

# difitが見つからない場合はグローバルを試す
if [[ ! -x "$DIFIT" ]]; then
  DIFIT="$(which difit 2>/dev/null || true)"
  if [[ -z "$DIFIT" ]]; then
    echo "difit not found. Install with: npm install -g difit"
    exit 1
  fi
fi

# 作業ディレクトリはClaude Codeの現在のディレクトリを使用
targetDir="$(pwd)"

# gitリポジトリ確認
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Not a git repository: $targetDir"
  exit 1
fi

# ブランチ検出
currentBranch=$(git rev-parse --abbrev-ref HEAD)
defaultBranch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "develop")
remoteDefaultBranch="origin/${defaultBranch}"

# リモートを最新化
git fetch origin "$defaultBranch" --quiet 2>/dev/null || true

# diff範囲を決定
# PRが存在する場合は --pr モードを優先（ローカル比較より確実）
if [[ "$currentBranch" == "$defaultBranch" ]]; then
  # デフォルトブランチの場合はHEADのみ
  DIFIT_ARGS=("HEAD")
  echo "Showing diff: HEAD"
else
  # PRを検索（gh CLIが必要）
  PR_URL=""
  if command -v gh &> /dev/null; then
    PR_URL=$(gh pr list --head "$currentBranch" --json url --jq '.[0].url' 2>/dev/null || true)
  fi

  if [[ -n "$PR_URL" ]]; then
    # PRが存在する場合は --pr モードを使用
    DIFIT_ARGS=("--pr" "$PR_URL")
    echo "Showing PR: $PR_URL"
  else
    # PRがない場合はローカル比較にフォールバック
    mergeBase=$(git merge-base "$remoteDefaultBranch" HEAD 2>/dev/null || echo "HEAD~1")
    DIFIT_ARGS=("$mergeBase" "HEAD")
    echo "Showing diff: $mergeBase..HEAD (vs $remoteDefaultBranch)"
  fi
fi

# 既存のdifitプロセスと bridgeプロセスを停止
pkill -f "difit.*$PORT" 2>/dev/null || true
pkill -f "cmux-difit-bridge.*$BRIDGE_PORT" 2>/dev/null || true
sleep 0.2

# difitサーバー起動（バックグラウンド、ブラウザ自動起動を抑制）
# --pr モードの場合は --include-untracked は不要
if [[ "${DIFIT_ARGS[0]}" == "--pr" ]]; then
  "$DIFIT" "${DIFIT_ARGS[@]}" --port "$PORT" --no-open --keep-alive &
else
  "$DIFIT" "${DIFIT_ARGS[@]}" --port "$PORT" --no-open --keep-alive --include-untracked &
fi
DIFIT_PID=$!

# difitサーバー準備待ち
for i in {1..30}; do
  if curl -s "http://localhost:${PORT}" > /dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

# bridgeサーバー起動（difit起動後）
node "${SCRIPT_DIR}/cmux-difit-bridge.mjs" --difit-port "$PORT" --bridge-port "$BRIDGE_PORT" &
BRIDGE_PID=$!

# bridge準備待ち
for i in {1..20}; do
  if curl -s "http://localhost:${BRIDGE_PORT}" > /dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

# クリーンアップ関数
cleanup() {
  kill "$BRIDGE_PID" 2>/dev/null || true
  kill "$DIFIT_PID" 2>/dev/null || true
}
trap cleanup EXIT

# cmuxブラウザで開く
# - 既にフォーカス外のペインがあり、そこにブラウザサーフェスがあれば navigate（増殖しない）
# - フォーカス外ペインがあるがブラウザ無しなら、そのペインに新規ブラウザタブを追加
# - フォーカス外ペインが無ければ右に新規分割
DIFIT_URL="http://localhost:${BRIDGE_PORT}/"
if [[ -x "$CMUX" ]]; then
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

  opened=""
  if [[ -n "$TARGET_PANE" ]]; then
    # ターゲットペインの中にブラウザサーフェスがあるか探す
    BROWSER_SURFACE="$(
      "$CMUX" list-pane-surfaces --pane "$TARGET_PANE" 2>/dev/null \
        | awk '{ for (i = 1; i <= NF; i++) if ($i ~ /^surface:[0-9]+$/) print $i }' \
        | while read -r s; do
            if "$CMUX" browser identify --surface "$s" > /dev/null 2>&1; then
              echo "$s"
              break
            fi
          done
    )"

    if [[ -n "$BROWSER_SURFACE" ]]; then
      if "$CMUX" browser navigate "$DIFIT_URL" --surface "$BROWSER_SURFACE" > /dev/null 2>&1; then
        echo "OK url=$DIFIT_URL surface=$BROWSER_SURFACE placement=navigate"
        opened=1
      fi
    fi

    if [[ -z "$opened" ]]; then
      if "$CMUX" new-surface --type browser --pane "$TARGET_PANE" --url "$DIFIT_URL" > /dev/null 2>&1; then
        echo "OK url=$DIFIT_URL pane=$TARGET_PANE placement=tab"
        opened=1
      fi
    fi
  fi

  if [[ -z "$opened" ]]; then
    "$CMUX" browser open-split "$DIFIT_URL" 2>/dev/null || \
      echo "Open in browser: $DIFIT_URL"
  fi
else
  echo "Open in browser: $DIFIT_URL"
fi

# サーバーを維持
wait $DIFIT_PID 2>/dev/null || true
wait $BRIDGE_PID 2>/dev/null || true
