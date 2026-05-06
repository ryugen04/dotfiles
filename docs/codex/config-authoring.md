# Codex config / hooks / skills / subagents の整備

Codex 自体の設定を変更する時は、通常の source change ではなく `codex_config_edit` として扱う。

## 変更前に使う skills

- `.codex/config.toml`: `codex-config-authoring`
- hooks / hook schema / dispatcher: `codex-hooks-authoring`
- `.codex/rules/*.rules`: `codex-rules-authoring`
- `AGENTS.md`: `codex-agents-md-authoring`
- skills: `codex-skill-authoring`
- subagents: `codex-subagents-authoring`
- runtime 挙動確認: `codex-runtime-probing`

## Mandatory planning

非自明な調査、設計、実装、config/hooks/skills 変更では、作業前に `.codex/plans/YYYYMMDDHH-{planname}.md` を作成または更新する。

plan には最低限これを含める。

- original request
- workflow axes
- target root
- allowed / forbidden paths
- phases / checkpoints
- subagents
- outputs
- test plan
- approval gates
- rollback / status
- hooks を扱う場合は hook event matrix と validation plan

`.codex/plans/**` は local workflow state なので、通常は commit しない。

## guardrails

project-local `.codex/config.toml` の `[guardrails]` は controller-only 境界を定義する。

- `subagent_required = true`: controller の直接編集を制限する。
- `bootstrap_edit_paths`: controller-only bootstrap 中でも編集を許可する path。
- `bootstrap_extra_commands`: controller-only bootstrap 中でも実行を許可する正確一致コマンド。

`bootstrap_extra_commands` は広くしすぎない。`python3` のような汎用 prefix ではなく、必要な検証コマンドを正確一致で置く。

## rules

`.codex/rules/*.rules` は sandbox escalation command policy だけに使う。

- read-only は狭く allow する。
- destructive な操作は prompt または forbidden にする。
- commit、push、root-export、cleanup は明示承認ゲート。

## 検証

変更後は次を確認する。

```bash
python3 -m py_compile packages/codex/.codex/ai-dlc/lib/aidlc/hooks.py
python3 -m py_compile packages/codex/.codex/ai-dlc/lib/aidlc/cli.py
python3 -m py_compile packages/codex/.codex/ai-dlc/lib/aidlc/workspace.py
python3 -m unittest tests.test_aidlc
git diff --check
```

hook の高リスク変更では、公式 docs、Codex source schema、local runtime probe の 3 点を確認する。
