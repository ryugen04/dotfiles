# Literal Worktree Overlay

- `web/` や `backend/` を root-system 配下の literal git worktree として配置する。
- root Git は baseline commit で child repo の tree を通常ファイルとして一度だけ記録する。
- 以後の差分は Orca / Codex から root 配下の実ファイル diff として見える。
- root overlay branch は local-only とし、push しない。
- `Discard` や `git restore` は root では使わず、child repo 側で実施する。
