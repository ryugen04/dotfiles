---
name: workflow-classify
description: Internal helper for workflow-start. Classifies user intent into docs-only-pure, docs-only-with-future-impl, docs-then-impl, autonomous-impl modes.
metadata:
  short-description: Classify intent into 4 modes
---

# workflow-classify

`workflow-start` の Phase 0 として、ユーザー指示文と現在地から作業モードを判定する。

## Inputs

- 直近のユーザー指示文（UserPromptSubmit prompt または会話初発の意図）
- 現在地: workspace.yaml の有無、project-metadata.yaml の有無

## Signals

- `pure_docs_signals`: 調査, 調べて, 一覧, まとめて, 仕様確認, 教えて, investigate, what is, how does
- `impl_signals`: 実装, 修正, 直して, PR, commit, ブランチ, fix, implement
- `plan_signals`: 計画, plan, 設計, 提案, 承認後, design
- `autonomous_signals`: 一気通貫, 自走, 止めずに, autonomous, 完了まで, end-to-end

## Decision Tree

```text
if workspace.yaml exists:
  if autonomous_signals >= 1: return autonomous-impl
  return docs-then-impl

# workspace なし
if impl == 0 and plan == 0 and pure_docs >= 1: return docs-only-pure
if impl >= 1 and autonomous >= 1:                return autonomous-impl
if impl >= 1 and plan >= 1:                      return docs-then-impl
if impl >= 1 and plan == 0 and autonomous == 0:  return docs-then-impl  # 安全側
if impl == 0 and plan >= 1:                      return docs-only-with-future-impl
return ASK_USER_ONCE
```
