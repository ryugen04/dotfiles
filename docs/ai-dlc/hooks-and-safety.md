# Hooks And Safety

- Codex hooks は `~/.codex/hooks.json` から `dispatcher.py` を呼ぶ。
- `dispatcher.py` は AI-DLC workspace 外では no-op で `allow` を返す。
- repo worker の書き込みは claimed lease と writable path 範囲が必要。
- repo worker の書き込み前提は overlay valid / bootstrap ready / plan.status / active work item / repo lock の bootstrap gate で確認する。
- root pre-commit は `web/**` と `backend/**` の commit を baseline 以外で拒否する。
- root pre-push は overlay branch push を拒否する。
- child pre-commit は workspace branch 一致と secret / env 混入を確認する。
- optional git shim は root-system での restore / clean 系事故を減らす。
- `ai-dlc git-shim install --destination ~/.local/bin/ai-dlc-git-shim` で shim を配置し、必要なら PATH 先頭へ追加して root-system の `git restore` / `git clean` を抑止する。
