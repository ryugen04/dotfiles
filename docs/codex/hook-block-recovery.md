# Hook block recovery

Codex hook、permission、tool block を受けたら、そこで止まらずに block recovery に入る。

## 標準手順

1. block message、event、tool、command/path、cwd、workspace 有無を読む。
2. `workflow-classify` で通常の workflow 3 軸に加えて `block_type` を分類する。
3. 許可された経路を探す。
4. 必要なら phase owner subagent に委譲する。
5. plan / decisions / work-items が不足していれば、対応 subagent に修復させる。
6. 最小再現、関連 validation、実運用 path の順で確認する。
7. block_type、選んだ route、残リスクを報告する。

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

- `read_only_false_positive`: read-only 操作が誤って mutating と判定された。
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

- PreToolUse は unsupported allow/update field に依存しない。
- PermissionRequest は `hookSpecificOutput.decision.behavior` を使う。
- Stop は plain stdout を出さない。
- PostToolUse は undo として扱わない。
