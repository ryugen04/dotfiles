---
name: bolt:start
description: ボルト開始: 今日のゴール設定
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TaskCreate
  - TaskList
  - AskUserQuestion
---

# ボルト開始（/bolt:start）

1日ボルトの開始イベント。今日のゴールを設定する。

---

## 実行手順

### 1. 状態確認

以下を並列で確認:

```bash
# 未完了タスクの確認
git log --oneline -10

# 昨日の申し送り確認
cat .claude/bolt/handover.md 2>/dev/null || echo "申し送りなし"

# バックログ確認
ls -la .claude/scrum/backlog/*.md 2>/dev/null || echo "バックログなし"
```

### 2. 今日の候補タスク提示

収集した情報から今日の候補を3〜5個提示:

```markdown
## 今日の候補タスク

1. [ ] **[高]** 〇〇機能の実装（継続）
   - 昨日の申し送り: △△まで完了

2. [ ] **[中]** △△のリファクタリング
   - Ready状態のPBI

3. [ ] **[低]** ドキュメント更新
   - 後回し可能
```

### 3. ゴール確定

AskUserQuestionで確認:

```
今日のゴールを確定します。

候補から選択するか、別のタスクを指定してください:
- 候補1〜3から選択
- 別のタスクを指定
```

### 4. タスク登録

確定したゴールをTaskCreateで登録:

```
/bolt:start 完了

## 今日のゴール
- [ ] 〇〇機能の実装

予定終了: 17:00
次のアクション: 実装開始
```

---

## 出力先

- 今日のゴール: TaskList（Claude Code内蔵）
- 進捗ログ: `.claude/bolt/YYYY-MM-DD.md`

---

## Tips

- 15分以内に完了させる
- 1日で完了できる粒度のタスクを選ぶ
- 不確実性が高いタスクは `/scrum:spike` で調査してから
