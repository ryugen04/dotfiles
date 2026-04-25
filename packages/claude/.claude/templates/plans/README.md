# Plan Templates

これらのテンプレートを `.claude/plans/YYYYMMDD-{genre}-{name}.md` にコピーして使う。

## コピー後の必須置換

テンプレートには以下のプレースホルダーがあり、**コピー後に必ず実値に書き換える**こと。放置すると `plan_frontmatter_validator.sh` で block される。

| プレースホルダー | 置換例 |
|---|---|
| `YYYY-MM-DD` (created/updated) | `2026-04-18` |
| `<genre>` | `coding` / `bugfix` / `spike` / `refactoring` / `review` / `ui-verification` / `po-work` |
| `{username}/{name}` (branch) | `alice/feature-x` |
| `<絶対パス or 相対パス>` (output_targets.path) | 実パス |
| Phase Dashboard の `<>` プレースホルダー | 実値 |

## テンプレート選択指針

| 用途 | テンプレート |
|---|---|
| 新機能実装 | `coding.md` |
| バグ修正 | `bugfix.md` |
| 技術調査 | `spike.md` |
| リファクタリング | `refactoring.md` |
| コードレビュー | `review.md` |
| UI 検証 | `ui-verification.md` |
| PO 作業 (Notion/Linear 更新) | `po-work.md` |
| ベース (ジャンル未定) | `_base.md` |
