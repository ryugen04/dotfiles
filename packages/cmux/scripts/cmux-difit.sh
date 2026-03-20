#!/usr/bin/env bash
# Git diffをcmuxブラウザで表示
# 参考: https://gist.github.com/azu/cef84c98aeef832d43dfb640c7e321f5

set -euo pipefail

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIFIT="${SCRIPT_DIR}/../node_modules/.bin/difit"
PORT=4966

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

# 既存のdifitプロセスを停止
pkill -f "difit.*$PORT" 2>/dev/null || true
sleep 0.2

# difitサーバー起動（バックグラウンド、ブラウザ自動起動を抑制）
# --pr モードの場合は --include-untracked は不要
if [[ "${DIFIT_ARGS[0]}" == "--pr" ]]; then
  "$DIFIT" "${DIFIT_ARGS[@]}" --port "$PORT" --no-open --keep-alive &
else
  "$DIFIT" "${DIFIT_ARGS[@]}" --port "$PORT" --no-open --keep-alive --include-untracked &
fi
DIFIT_PID=$!

# サーバー準備待ち
for i in {1..30}; do
  if curl -s "http://localhost:${PORT}" > /dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

# cmuxブラウザで開く
if [[ -x "$CMUX" ]]; then
  "$CMUX" browser open-split "http://localhost:${PORT}/" 2>/dev/null || \
    echo "Open in browser: http://localhost:${PORT}"
else
  echo "Open in browser: http://localhost:${PORT}"
fi

# サーバーを維持
wait $DIFIT_PID
