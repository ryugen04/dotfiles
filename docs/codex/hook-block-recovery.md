# Hook block recovery

Codex hook、permission、tool block を受けたら、`block-delegation-policy-matrix.md` を正本として recovery に入る。
この文書は手順書であり、allow / block / mandatory action / forbidden recovery の判断は matrix を優先する。

## 標準手順

1. block message、event、tool、command/path、cwd、workspace 有無を読む。
2. `workflow-classify` で通常の workflow 3 軸に加えて `block_type` を分類する。
3. `docs/codex/block-delegation-policy-matrix.md` の root class、phase、block_type matrix に照合する。
4. 許可された経路を 1 つだけ選ぶ。
5. plan / decisions / work-items が不足していれば、対応 subagent に修復させる。
6. 最小再現、関連 validation、実運用 path の順で確認する。
7. block_type、選んだ route、残リスクを報告する。

`needs_assignment` または `route=delegate_phase_owner` の場合、controller は回避探索を続けない。許可される次 action は `inspect_current_phase`、`create_assignment`、`delegate_to_subagent`、`report_delegation_deadlock` だけとする。assignment 作成や owner 起動ができない場合は `bootstrap/delegation deadlock` として停止し、恒久修正 plan を提示する。

## block ledger

hook が `AI-DLC_BLOCK` を返した場合、block event は user-level ledger に自動記録される。これは通常 session を即停止する gate ではない。作業継続が必要な場合でも、finish/git boundary 前に必ず action 化する。

| Step | Command | Purpose |
|---|---|---|
| open blocker 確認 | `ai-dlc block list --json` | 別 session/repo からも user-level blocker を取得する |
| durable artifact へ紐付け | `ai-dlc block record --event-id <id> --ref ai-dlc/decisions/<id>.md` | workflow 内の decision/evidence/plan に記録したことを ledger に反映する |
| 外部修正 task 化 | `ai-dlc block export --event-id <id> --plan /path/to/blocker-plan.md` | 別 session で修正できる plan を生成し、`external_fix_plan` action を記録する |
| 既存 artifact の同期 | `ai-dlc block sync` | `ai-dlc/decisions/**`、`ai-dlc/evidence/**`、`.codex/plans/**` 内の `block_event_id` を action 化する |

| Boundary | Open blocker handling |
|---|---|
| 通常 phase の作業 | matrix で許可された action だけ継続できる |
| `transition ready_to_finish` / `transition done` | action 未登録の blocker があれば拒否する |
| `finish` | action 未登録の blocker があれば拒否する |
| `root-export` / `overlay-cleanup` | action 未登録の blocker があれば拒否する |
| `Stop` at `ready_to_finish` / `done` | action 未登録の blocker があれば final を止める |

## block-diagnose

hook block reason は schema を壊さないため、`permissionDecisionReason` や `reason` に安定形式で入る。

```text
AI-DLC_BLOCK type=... recoverable=... route=... approval=... agent=... actions=... :: reason
```

詳細診断は CLI で確認する。

```bash
ai-dlc block-diagnose \
  --event PreToolUse \
  --tool Bash \
  --command "mkdir -p scratch" \
  --message "Controller-only: mutating Bash is blocked outside AI-DLC; delegate to a subagent."
```

主な出力:

- `block_type`
- `recoverable`
- `suggested_route`
- `suggested_agent`
- `allowed_next_actions`
- `requires_user_approval`
- `reason`

## block_type

- `read_only_false_positive`: read-only 操作が誤って mutating と判定された。retry は command tokens が実際に非破壊である場合だけ許可する。
- `bootstrap_config_gap`: `bootstrap_edit_paths` や `bootstrap_extra_commands` が不足している。
- `needs_assignment`: controller ではなく subagent assignment が必要。feature/source 実装では、委譲を回避するために `bootstrap_edit_paths` を広げない。
- `wrong_next_agent`: 現在 phase と起動 agent が一致していない。
- `missing_workspace`: workspace または control-plane が見つからない。
- `approval_required`: 非破壊だが明示承認が必要。
- `destructive_forbidden`: reset、clean、push、破壊的 rm など。
- `hook_schema_error`: hook payload / output schema の不整合。

## install 承認

`install.sh` の本実行は user home を変更するため、dry-run 以外は既定で block する。

許可する場合は、対象 command が `bootstrap_extra_commands` に登録済みであることを確認し、ユーザー承認後に明示マーカー付きで再実行する。

```bash
AI_DLC_INSTALL_APPROVED=1 ./install.sh codex agents
```

dry-run は承認なしで確認できる。

```bash
./install.sh --dry-run codex agents
```

## 重要な制約

- `needs_assignment` / `delegate_phase_owner` を local workaround に変換しない。
- `bootstrap/delegation deadlock` では、controller が `codex exec`、直接 `apply_patch`、広い escalation、read-only 風の迂回で作業を継続しない。
- PreToolUse は unsupported allow/update field に依存しない。
- PermissionRequest は `hookSpecificOutput.decision.behavior` を使う。
- Stop は plain stdout を出さない。
- PostToolUse は undo として扱わない。
