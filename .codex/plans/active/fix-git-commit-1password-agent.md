---
status: in_progress
---

## Context
`git commit` の SSH 署名を 1Password SSH agent で正しく動かしたい。前回追加した repo 管理の `.gitconfig` は方針に合わないため取り除き、1Password agent と手元設定の整合を取る。

## 完了基準
- 1Password agent が提示する鍵を確認できている。
- repo 管理の `packages/git/.gitconfig` は削除されている。
- このリポジトリで署名付きコミットが通る設定、または不足している外部要因が明確になっている。

## Phase Checklist
- [x] active state を復旧する
- [x] 1Password agent の公開鍵を確認する
- [x] 不要な repo 変更を除去する
- [x] Git 署名設定を 1Password に合わせる
- [x] 動作確認して結果を共有する

## Agent Assignment
- Main agent が調査、設定修正、検証を担当する。
- サブエージェントは使わない。

## Review Loop
- 調査結果から最小修正を選ぶ。
- 修正後に dry-run と署名確認で検証する。
