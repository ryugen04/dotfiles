# Block delegation policy matrix

この文書を AI-DLC hook / delegation recovery の正本とする。
hook、skills、tests はこの matrix の投影として扱い、ここにない controller 回避経路を追加しない。

## Root classes

| Root class | Definition | Allow | Block | Mandatory action | Forbidden recovery |
|---|---|---|---|---|---|
| `docs_only_no_workspace` | workspace なし、docs/report のみ | read-only 調査、docs/report 用 subagent 委譲、報告 | source edit、bootstrap 例外拡張、repo worker 起動 | docs/report の範囲だけを完了し、実装が必要なら workflow を再分類する | docs-only を口実に source path を編集する |
| `workspace_less_controller` | workspace なし、`guardrails.subagent_required=true` | read-only、bootstrap 明示 path 編集、narrow assignment create、subagent 起動、deadlock 報告 | source/test/runtime 実装、直接 `apply_patch`、広い escalation、委譲回避の allowlist 拡張 | root class と block type を診断し、matrix の route だけを実行する | `codex exec`、read-only 風の迂回、`bootstrap_edit_paths` の feature path 拡張 |
| `task_workspace_controller` | `workspace.yaml` がある AI-DLC task workspace | phase 判定、transition、assignment、phase owner 起動、read-only、report 統合 | phase owner 代行、tracked file 編集、evidence 代筆、verifier/evaluator 代行 | current phase owner に委譲し、deliverable を受けてから遷移する | phase 飛ばし、raw diff だけで前進する |
| `repairing_controller` | status が `repairing`、または local overlay/runtime 修復中 | repair assignment、overlay/runtime read-only 調査、repair report 統合 | source 実装、repo worker 代行、repair 名目の bootstrap 拡張 | `dlc_repairer` に限定 scope の assignment を作る | repair を理由に source/test path を編集する |
| `git_finish_controller` | status が `ready_to_finish`、または commit/export/push/cleanup が主目的 | read-only 証跡収集、明示承認要求、`dlc_git_operator` 委譲 | commit/push/root-export/cleanup の無承認実行、repo worker 再開 | approval gate を記録し、承認後に git owner へ委譲する | finish 作業を通常 Bash として実行する |

## Phase ownership

| Phase | Owner | Allow | Block | Mandatory action | Forbidden recovery |
|---|---|---|---|---|---|
| `initializing` | `dlc_initializer` | bootstrap readiness assignment、bootstrap evidence 統合 | controller の bootstrap 実作業代行 | initializer assignment を作り report を待つ | controller が `.local` や overlay を直接修復する |
| `planning` | `dlc_plan_writer` | plan/decision assignment、read-only exploration | plan なし source 実装、work item 作成代行 | plan/decision deliverable を受ける | 口頭 plan だけで executing へ進む |
| `plan_ready` | `dlc_scope_manager` | work-items/WIP/boundary assignment | repo worker 先行起動 | WIP と assignment boundary を作る | active item なしで worker を作る |
| `assigning` | `dlc_scope_manager` | assignment 作成・修正 | wrong owner のまま続行 | phase owner と writable scope を確定する | worker を増やして scope 不備を吸収する |
| `executing` | `dlc_repo_worker` | active item ごとの repo worker 起動、report 統合 | controller source edit、複数 active worker の無制御起動 | claimed lease を持つ worker に編集させる | controller が直接 patch する |
| `verifying` | `dlc_verifier` | verifier assignment、evidence 統合 | controller self-verification | verifier evidence を受ける | 実装者 report を evidence として代用する |
| `evaluating` | `dlc_evaluator` | evaluator assignment、verdict 統合 | 実装者自身の承認 | independent verdict を受ける | verifier/evaluator を同一主体で済ませる |
| `handoff_ready` | `dlc_handoff_writer` | handoff assignment、handoff 統合 | controller 手書き handoff で完了扱い | handoff report を受ける | finish 前の handoff 省略 |
| `ready_to_finish` | `dlc_git_operator` | approval gate、git operator 起動 | 無承認 commit/push/export/cleanup | 明示承認後に git owner へ委譲する | finish を通常実装 phase として扱う |

## Block types

| Block type / route | Allow | Block | Mandatory action | Forbidden recovery |
|---|---|---|---|---|
| `needs_assignment` | `inspect_current_phase`、`create_assignment`、`delegate_to_subagent`、`report_delegation_deadlock` | source edit、mutating Bash、direct patch、broad escalation | 正しい phase owner の assignment を作る。作れない場合は `bootstrap/delegation deadlock` として停止する | `codex exec`、read-only 風迂回、bootstrap allowlist 拡張 |
| `delegate_phase_owner` | expected owner 確認、assignment 修正、owner 起動、deadlock 報告 | 間違った role の継続、controller 代行 | current phase と owner を一致させて委譲する | phase 飛ばし、worker の ad-hoc 起動 |
| `read_only_false_positive` | 実際に非破壊な同一コマンド retry、read-only allowlist 追加、回帰テスト追加 | mutating command の retry | command tokens を確認し、read-only なら allowlist と test を同時に更新する | 「調査目的」を理由に mutating command を通す |
| `bootstrap_config_gap` | bootstrap 明示 path の最小修正、dry-run、guardrail 診断 | source/test path の bootstrap 化 | gap が bootstrap/self-repair か feature 実装かを分ける | feature 実装を進めるために `bootstrap_edit_paths` を広げる |
| `wrong_next_agent` | expected agent 起動、assignment 修正、decision 記録 | wrong role の作業継続 | owner mismatch を修正してから再開する | user approval だけで mismatch を無視する |
| `missing_workspace` | workspace 探索、sango/root-system read-only 確認、bootstrap workflow | source 実装開始 | task workspace を作成または採用する | workspace なしで AI-DLC phase を推測する |
| `approval_required` | 非破壊 command の承認要求、approval gate 記録 | 承認なし実行 | user approval を明示的に取得する | 別 command 名で approval を避ける |
| `destructive_forbidden` | read-only 証跡、代替案、明示承認要求 | `git reset --hard`、`git clean`、`git push`、`git worktree remove`、破壊的 `rm` | 停止して user decision を待つ | repair/bootstrap 名目で実行する |
| `hook_schema_error` | docs/source/runtime probe、最小再現、schema 修正 | 推測 field 追加、plain stdout 依存 | `codex-hooks-authoring` 手順で wire format を確認する | unsupported hook output に依存する |

## Block ledger and finish boundaries

AI-DLC block は user-level ledger に append-only で記録する。記録は「セッション中の作業を止める」ためではなく、finish/git boundary で未処理 blocker を見逃さないために使う。

| Event / Boundary | Ledger write | Continue allowed | Hard block condition | Mandatory action |
|---|---|---|---|---|
| `PreToolUse` の `AI-DLC_BLOCK` | `~/.codex/ai-dlc/block-ledger/events.jsonl` に記録 | yes。matrix で許可された route のみ継続 | none | `ai-dlc block list` で確認し、必要なら `record/export/sync` で action 化する |
| `PermissionRequest` deny | 同上 | yes。承認なしで同一 write を続けない | none | 承認要求、delegation、repair plan のいずれかを action 化する |
| `Stop` 通常 phase | phase obligation は従来通り。open blocker 単体では止めない | yes | phase owner deliverable 不足など既存 Stop gate | phase owner report または break-glass decision |
| `Stop` when `ready_to_finish` / `done` | `open_blockers` 自体は再記録しない | no | action 未登録の block event がある | `durable_record`、`external_fix_plan`、`repair_task_created`、`resolved`、`deferred_by_user` のいずれかを記録する |
| `transition ready_to_finish` / `transition done` | no | no | action 未登録の block event がある | blocker の durable record または async repair task を作る |
| `finish` | no | no | action 未登録の block event がある | finish 前に `ai-dlc block record` または `ai-dlc block sync` を実行する |
| `root-export` / `overlay-cleanup` | no | no | action 未登録の block event がある | git finish / cleanup 前に blocker action を記録する |

| Ledger item | Location | Scope | Secret handling | Async repair use |
|---|---|---|---|---|
| block event | `~/.codex/ai-dlc/block-ledger/events.jsonl` | `workspace:<id>:<path-hash>` or `project:<id>` | command/reason は token-like 文字列を redact | 別 session/repo が `ai-dlc block list --json` で取得する |
| block action | `~/.codex/ai-dlc/block-ledger/actions.jsonl` | `block_event_id` に紐付く | reason は redact | `external_fix_plan` や `repair_task_created` で非同期作業へ渡す |
| durable reference | `ai-dlc/decisions/**`、`ai-dlc/evidence/**`、`.codex/plans/**`、URL、絶対 path | workspace または外部 task | secrets を含めない | `ai-dlc block sync` が既存 artifact 内の `block_event_id` を action 化する |

| CLI | Purpose | Required flags | Notes |
|---|---|---|---|
| `ai-dlc block list` | open block events を見る | none | `--all` で action 済みも表示、`--json` で machine-readable |
| `ai-dlc block actions` | action ledger を見る | none | `--json` available |
| `ai-dlc block record` | event に action/ref を紐付ける | `--event-id`, `--ref` | `--type` は `durable_record` が既定 |
| `ai-dlc block export` | 外部修正用 plan を作る | `--event-id`, `--plan` | 生成と同時に `external_fix_plan` action を記録 |
| `ai-dlc block sync` | durable artifact 内の event id を action 化する | none | decisions/evidence/plans を scan |

## Read-only command policy

| Command family | Allow | Block | Notes |
|---|---|---|---|
| git state | `git status`, `git diff`, `git log`, `git show`, `git branch`, `git ls-files`, `git rev-parse` | `git checkout`, `git switch`, `git merge`, `git reset`, `git clean`, `git push` | state observation only |
| git remote | `git remote -v`, `git remote get-url origin` | `git remote add`, `git remote set-url`, `git remote remove` | `remote get-url` is read-only only for literal query forms |
| git worktree | `git worktree list` | `git worktree add`, `git worktree remove`, `git worktree prune` | `add` is mutating even when used for bootstrap |
| shell inspection | safe forms of `ls`, `pwd`, `cat`, `find`, `rg`, `sed`, `head`, `tail`, `wc`, `sort`, `uniq`, `cut`, `nl` | redirects, pipes, subshells, `sed -i`, `find -delete`, exec forms | shell fragments are denied by default |
| GitHub CLI | read-only `view`, `list`, `status`, `diff`, `checks`, selected `api` reads | `create`, `merge`, `comment`, `review`, `close`, `checkout`, `release create` | write-like gh commands require owner flow |
| AI-DLC CLI | `doctor`, `status`, `inspect`, `context`, `validate`, `validate-overlay`, `overlay-status`, `deadlock-check`, help | source mutation outside owner flow | assignment create is allowed only through role-specific validation |

## Workspace-less assignments

| Role | Purpose | Required flags | Writable scope | Block |
|---|---|---|---|---|
| `dlc_initializer` | bootstrap readiness | `--role`, at least one `--writable` | `ai-dlc/bootstrap/**`, `ai-dlc/overlay/**`, `../.local/**`, explicit `.codex/config.toml`, explicit `.gitignore` | source/test path, broad glob, `.git/**`, unrelated `.codex/**` |
| `dlc_repairer` | local repair | `--role`, at least one `--writable` | `ai-dlc/bootstrap/**`, `ai-dlc/overlay/**`, `ai-dlc/decisions/**`, `../.local/**`, explicit `.codex/config.toml`, explicit `.gitignore` | source/test path, broad glob, `.git/**`, unrelated `.codex/**` |
| `dlc_repo_worker` | source implementation | `--role`, `--repo`, `--work-item`, at least one narrow `--writable` | explicit source files or narrow source directories | `.codex/**`, `.git/**`, `ai-dlc/**`, `workspace.yaml`, broad glob |
| other roles | workspace-less unsupported | none | none | assignment create is rejected |

## Bootstrap explicit paths

| Path | Allow purpose | Not allowed purpose |
|---|---|---|
| `.codex/config.toml` | guardrail/bootstrap self-repair only | feature implementation enablement |
| `.gitignore` | local workflow artifact ignore rules | unrelated ignore churn |
| `.codex/rules/**` | sandbox command policy | source implementation |
| `.agents/skills/**/SKILL.md` | workflow guidance | product/source feature work |
| `.agents/skills/**/references/*.md` | skill reference guidance | product/source feature work |
| `docs/codex/**` | Codex operation docs | unrelated docs |
| `ai-dlc/**` | control-plane working state | application source work |

## Deadlock policy

| Deadlock condition | Mandatory action | Final report must include |
|---|---|---|
| `needs_assignment` returned but assignment create is blocked | Stop as `bootstrap/delegation deadlock` | blocked command, missing role/scope support, permanent fix plan |
| `delegate_phase_owner` returned but owner cannot be started | Stop as `bootstrap/delegation deadlock` | expected owner, phase, failed route |
| assignment exists but cannot be claimed | Stop or repair through `dlc_repairer` if repair assignment can be created | assignment id, claim error, repair boundary |
| read-only command is blocked but is not in matrix | Classify as `read_only_false_positive` only after token review | exact command, allowlist diff, regression test |

The controller does not continue by widening permissions after a deadlock condition. The next action is a durable policy repair or an explicit user-level break-glass decision.
