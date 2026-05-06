# Codex Base Policy

## Language

- 対話は日本語。
- 変数名と識別子は英語。
- コメントは必要最小限の日本語。

## Instruction Scope

- `AGENTS.md` は常時ロードされる全体方針だけを書く。
- 長い手順、分類表、調査手順は skills に置く。
- sandbox 外コマンド policy は `.codex/rules/*.rules` に置く。
- 強制したい実行時制約は hooks で扱う。

## Mandatory Planning

非自明な調査、設計、実装、config/hooks/skills 変更では、作業前に `.codex/plans/YYYYMMDDHH-{planname}.md` を作成または更新する。

plan には最低限、original request、workflow axes、target root、allowed/forbidden paths、phases/checkpoints、subagents、outputs、test plan、approval gates、rollback/status を含める。hooks を扱う場合は hook event matrix と validation plan も含める。

大きい plan は 1 ファイルに圧縮しない。parent plan に child plan paths を明記し、各 child plan は parent plan path を記載する。`.codex/plans/**` は local working state として git 対象外でもよいが、durable なルールは skills、schemas、hooks、validators、tests に反映する。

## Workflow Classification

着手前に `workflow-classify` で 3 軸を判定する。

- `origin_mode`: `new_workspace_from_plan` / `from_remote_ref` / `resume_existing_workspace` / `docs_only_no_workspace`
- `execution_intent`: `docs_only` / `plan_then_stop` / `docs_then_impl` / `autonomous_until_git_boundary`
- `safety_domain`: `source_change` / `codex_config_edit` / `docs_report` / `git_finish`

`AI_DLC_SAFETY_DOMAIN=codex_config_edit`、または Codex config/hooks/skills/subagents/schema/sandbox/approval を扱う作業では `codex_config_edit` を優先する。`-c` は Codex runtime override であり workflow mode ではない。

## Block Recovery

hook / permission / tool block を観測した時は最初の block で停止せず、`workflow-start` の Block Recovery と `workflow-classify` の block 分類に従って、許可された代替経路、subagent 委譲、plan/repair、検証、報告へ進む。

## Safety

- `git reset --hard`、`git clean`、`git push`、`git worktree remove`、破壊的 `rm` は明示承認なしで実行しない。
- user または他者の既存変更を revert しない。
- secrets、tokens、credentials を出力・保存しない。
- commit、push、root-export、cleanup は明示承認ゲートとする。

## Verification

hooks/config/skills/schema を変更する時は、active version、読み込まれる config layer、schema、runtime path を確認してから修正する。エラー文字列がある場合は実装、設定、実バイナリまたは一次情報で受け手の期待形を確認する。

修正後は、最小再現コマンド、関連テスト、実運用パスの 3 点で確認する。確認できない項目は final report に残す。

## AI-DLC Workspaces

`workspace.yaml` がある場所は AI-DLC task workspace として扱う。root-system は control-plane であり、通常の実装 repo として扱わない。`literal_worktree_overlay` では child repo の変更を root から commit しない。
