# Troubleshooting

## `./install.sh codex agents` が `~/.codex` conflict で止まる

- `~/.codex/AGENTS.md`、`~/.codex/config.toml`、`~/.codex/hooks.json` が実体ファイルか確認する。
- これらが symlink でない場合、退避してから `./install.sh codex agents` を再実行する。
- project-local 用の `.codex/` は repo 内に残し、home 側 `~/.codex/` だけを配布物へ切り替える。

## root diff に child repo が出ない

- `ai-dlc validate-overlay` を実行する。
- `web/.git` と `backend/.git` が戻っているか確認する。
- `git status --short` と `git -C web status --short` の両方で差分が見えるか確認する。

## gitlink 160000 になった

- root で `git ls-files -s -- web backend` を確認する。
- `ai-dlc overlay-init` を再実行する。

## `web/.git` または `backend/.git` が消えた

- `ai-dlc validate-overlay` を実行する。
- `ai-dlc overlay-init` を再実行して `.git` pointer を復元する。
- `.local/overlay/gitfiles/` に退避された gitfile が残っていないか確認する。

## child repo commit ができない

- child branch が workspace branch と一致しているか確認する。
- pre-commit で secret guard に引っかかっていないか確認する。
- root controller からではなく、`git -C web` / `git -C backend` で commit しているか確認する。
- repo worker が必要な場合は assignment claim と repo lock を確認する。

## テスト用 repo の git commit が agent socket error で失敗する

- テストでは global Git 署名設定を引き継がないようにする。
- `GIT_CONFIG_GLOBAL=/dev/null` と `GIT_CONFIG_NOSYSTEM=1` で隔離する。
- それでも必要なら repo-local で `git config commit.gpgsign false` を入れる。

## root push が拒否される

- 仕様どおり。`ai-dlc root-export` を使う。

## Orca で Discard して child repo の差分を消した

- root-system SCM は diff 閲覧専用として扱う。
- child repo の restore は `git -C web restore ...` または `git -C backend restore ...` でやり直す。
- 再発防止には `ai-dlc git-shim install` で root 側 restore/clean を抑止する。

## `.local/gitdirs` が壊れた

- `ai-dlc overlay-cleanup` で現状を確認する。
- 問題が継続する場合は `ai-dlc overlay-init` を再実行して bare controller/worktree を作り直す。

## branch がずれた

- root と child repo の現在 branch を `ai-dlc overlay-status` で確認する。
- child repo branch が workspace branch と一致しない場合は正しい branch に戻してから commit する。
