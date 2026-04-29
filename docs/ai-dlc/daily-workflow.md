# Daily Workflow

1. `$workflow-start`
2. root controller は状態確認と assignment 作成だけを行う。
3. child repo の実装は lease を持つ subagent が行う。
4. diff は root-system 側で確認し、commit は `git -C web` / `git -C backend` で行う。
5. 終了前に `workflow-review` と `workflow-finish` を実施する。
