# Workspace Setup

このページは workspace bootstrap だけを扱う。user-level 配置と root-system 初期化は `project-setup.md` を参照。

1. root-system worktree を作る。
2. worktree 内で `ai-dlc init-workspace --issue ... --branch ... --repo web=... --repo backend=...`
3. `ai-dlc validate-overlay`
4. `ai-dlc bootstrap`
5. `ai-dlc overlay-status`
6. root 側の差分確認だけを行い、commit は `git -C web` / `git -C backend` で行う。

`init-workspace` 前提:

- root-system と child repo は git repo であること
- root-system と child repo に初回 commit があること
- canonical repo URL を `origin` remote か `--root-canonical-url` / `--repo-url` で解決できること

前提が足りない場合、`init-workspace` は次アクション付きで不足項目を案内する。
