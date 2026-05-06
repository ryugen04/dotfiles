---
name: workflow-classify
description: "Internal helper for workflow-start. Classifies user intent into a 3-axis workflow model: origin_mode, execution_intent, and safety_domain, including codex_config_edit priority for Codex config, hooks, skills, subagents, sandbox, approval, and schema work."
metadata:
  short-description: Classify workflow axes
---

# workflow-classify

`workflow-start` の Phase 0 として、ユーザー指示文、現在地、変更対象から workflow axes を判定する。

## Inputs

- 直近のユーザー指示文（UserPromptSubmit prompt または会話初発の意図）
- 現在地: workspace.yaml の有無、project-metadata.yaml の有無
- 変更対象 path または明示された領域
- 観測した hook / permission / tool block の event、message、blocked command/tool
- prompt marker: `AI_DLC_SAFETY_DOMAIN=<value>`
- 将来補助入力: env var `AI_DLC_SAFETY_DOMAIN`

## Output Model

```yaml
workflow:
  origin_mode: new_workspace_from_plan | from_remote_ref | resume_existing_workspace | docs_only_no_workspace
  execution_intent: docs_only | plan_then_stop | docs_then_impl | autonomous_until_git_boundary
  safety_domain: source_change | codex_config_edit | docs_report | git_finish
  block_type: read_only_false_positive | bootstrap_config_gap | needs_assignment | wrong_next_agent | missing_workspace | approval_required | destructive_forbidden | hook_schema_error | none
```

旧 4 モードは `execution_intent` へ分解する。単一の `mode` だけで安全境界を表現しない。
`block_type` は hook / permission / tool block を観測した時だけ `none` 以外にする。

## Safety Domain Priority

1. prompt に `AI_DLC_SAFETY_DOMAIN=codex_config_edit` があれば、必ず `safety_domain=codex_config_edit`。
2. 変更対象 path が Codex runtime/config に関わる場合は `codex_config_edit`。
3. 指示語彙が Codex config/hooks/permissions/sandbox/skills/subagents/frontmatter/schema を扱う場合は `codex_config_edit`。
4. git commit/export/push/cleanup が主目的なら `git_finish`。
5. 実装を伴わない調査・報告だけなら `docs_report`。
6. それ以外は `source_change`。

`-c` は Codex runtime config override であり、AI-DLC 独自 mode の主入力にしない。

## codex_config_edit Path Signals

- `.codex/config.toml`
- `packages/codex/.codex/config.toml`
- `packages/codex/.codex/hooks.json`
- `.codex/AGENTS.md`
- `packages/codex/.codex/AGENTS.md`
- `.codex/agents/**`
- `packages/codex/.codex/agents/**`
- `.agents/skills/**`
- `packages/agents/.agents/skills/**`
- `packages/codex/.codex/ai-dlc/hooks/**`
- `packages/codex/.codex/ai-dlc/lib/aidlc/hooks.py`
- Codex hook/config/schema/permission/sandbox/approval/subagent/skill 関連 docs or validators

## codex_config_edit Text Signals

- codex 設定
- Codex config
- hooks.json
- PreToolUse
- PermissionRequest
- PostToolUse
- UserPromptSubmit
- SessionStart
- Stop
- permission
- sandbox
- approval
- frontmatter
- SKILL.md
- subagent
- agents/*.toml
- profile
- codex_hooks

## Execution Intent Signals

- `pure_docs_signals`: 調査, 調べて, 一覧, まとめて, 仕様確認, 教えて, investigate, what is, how does
- `impl_signals`: 実装, 修正, 直して, PR, commit, ブランチ, fix, implement
- `plan_signals`: 計画, plan, 設計, 提案, 承認後, design
- `autonomous_signals`: 一気通貫, 自走, 止めずに, autonomous, 完了まで, end-to-end

## Block Classification

hook / permission / tool block を観測したら、停止理由を 1 つの `block_type` に分類する。

- `read_only_false_positive`: read-only 調査や status 確認が mutating と誤判定された。
- `bootstrap_config_gap`: bootstrap command、extra command、edit path、profile などの初期設定不足。
- `needs_assignment`: controller が直接作業しようとしており、subagent assignment が必要。
- `wrong_next_agent`: 現在 phase と起動しようとした subagent owner が一致しない。
- `missing_workspace`: task workspace または採用済み worktree が見つからない。
- `approval_required`: 非破壊だが sandbox 外実行または権限昇格の明示承認が必要。
- `destructive_forbidden`: reset、clean、push、worktree remove、破壊的 rm など承認なしでは禁止。
- `hook_schema_error`: hook 出力、payload、schema、許容値の不整合。

分類できない場合は `ASK_USER_ONCE` ではなく、まず `workflow-start` の Block Recovery に戻して許可された観測経路を探す。

## Decision Tree

```text
classify safety_domain first using Safety Domain Priority
if hook / permission / tool block observed:
  classify block_type using Block Classification

if workspace.yaml exists:
  origin_mode = resume_existing_workspace
elif docs_only and no implementation expected:
  origin_mode = docs_only_no_workspace
elif remote ref or PR/branch input is primary:
  origin_mode = from_remote_ref
else:
  origin_mode = new_workspace_from_plan

if impl == 0 and plan == 0 and pure_docs >= 1:
  execution_intent = docs_only
elif impl == 0 and plan >= 1:
  execution_intent = plan_then_stop
elif impl >= 1 and autonomous >= 1:
  execution_intent = autonomous_until_git_boundary
elif impl >= 1:
  execution_intent = docs_then_impl
else:
  ASK_USER_ONCE
```

## codex_config_edit Requirements

- Codex hooks/config/skills/subagents を変更する前に、対応する Codex authoring skills を使う。
- hooks 設計または修正の plan には、実装前に hook event matrix を含める。
- high-risk な hook/config 挙動は、公式 docs、openai/codex source schema、local runtime probe の 3 点で確認する。
