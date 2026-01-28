---
name: coding-rules
description: Project-specific coding rules and guidelines. Auto-loaded during code review.
---

# コーディングルール

プロジェクト固有のコーディング規約とベストプラクティス。

## ルールカテゴリ

### 言語固有 (`languages/`)

- `typescript.md` - TypeScript規約
- `kotlin.md` - Kotlin規約

### ライブラリ固有 (`libraries/`)

- `react.md` - Reactコンポーネント規約
- `apollo-client.md` - Apollo Client使用ガイド
- `mobx.md` - MobX状態管理規約
- `graphql.md` - GraphQLスキーマ・リゾルバ規約
- `kotlin-exposed.md` - Kotlin Exposed ORM規約

### その他

- `testing.md` - テスト規約

## 自動適用

これらのルールはコードレビュー時に自動で参照される:

- `/code:review-*` コマンド実行時
- `rules-checker` エージェント起動時

## ルール追加方法

1. 適切なサブディレクトリにMarkdownファイルを作成
2. 以下の形式で記述:

```markdown
# {ルール名}

## 禁止事項
- ...

## 推奨事項
- ...

## 例
```typescript
// BAD
...

// GOOD
...
```
```
