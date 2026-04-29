# Workspace Setup

1. root-system worktree を作る。
2. worktree 内で `ai-dlc init-workspace --issue ... --branch ... --repo web=... --repo backend=...`
3. `ai-dlc validate-overlay`
4. `ai-dlc bootstrap`
5. `ai-dlc overlay-status`
6. root 側の差分確認だけを行い、commit は `git -C web` / `git -C backend` で行う。
