# GitHub Ruleset Templates

新規リポジトリで「管理者以外はブランチを作成・更新・削除できない」状態にするための GitHub repository ruleset テンプレートです。

## admin-only-branches.json

`admin-only-branches.json` は全ブランチを対象にします。

- `creation`: 管理者以外のブランチ作成を禁止
- `update`: 管理者以外の push と PR merge によるブランチ更新を禁止
- `deletion`: 管理者以外のブランチ削除を禁止
- `non_fast_forward`: 管理者以外の force push を禁止
- `bypass_actors`: repository admin role だけを常時バイパス可能にする

適用例:

```bash
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  /repos/OWNER/REPO/rulesets \
  --input .github/rulesets/admin-only-branches.json
```

この ruleset は Issues の作成権限には影響しません。

注意点:

- GitHub は public repository への pull request 作成自体を ruleset だけでは完全には禁止できません。このテンプレートは PR が開かれても、管理者以外が対象ブランチを更新できない状態にします。
- Issue 起票を許可しつつコード変更を拒む場合は、repository access を `Read` または `Triage` に留め、`Write`/`Maintain` を付与しない運用と併用してください。
- `actor_id: 5` は GitHub ruleset bypass actor の repository admin role を指します。適用後、GitHub UI の Rulesets 画面でバイパス対象が `Repository admin` と表示されることを確認してください。
