---
name: bolt:status
description: 進捗確認: 現在の状況と残タスク
allowed-tools:
  - Read
  - Glob
  - Bash
  - TaskList
  - TaskGet
---

# 進捗確認（/bolt:status）

現在のボルト進捗を確認する。

---

## 実行手順

### 1. タスク状況確認

```
TaskList を実行して現在のタスク一覧を取得
```

### 2. Git状況確認

```bash
# 今日のコミット
git log --oneline --since="00:00" --format="%h %s"

# 未コミット変更
git status --short
```

### 3. 進捗サマリ表示

```markdown
## ボルト進捗（HH:MM 時点）

### 完了タスク
- [x] タスク1
- [x] タスク2

### 進行中
- [ ] タスク3（現在作業中）

### 残タスク
- [ ] タスク4
- [ ] タスク5

### 今日のコミット
- abc1234 feat: 〇〇を追加
- def5678 fix: △△を修正

### 未コミット変更
- M src/foo.ts
- A src/bar.ts

---

残り時間: X時間
ペース: 順調 / 要注意 / 遅延
```

---

## 判断基準

| 状態 | 条件 |
|------|------|
| 順調 | 50%以上完了 & 残り時間に余裕 |
| 要注意 | 30-50%完了 or 予想外の障害発生 |
| 遅延 | 30%未満 & 残り時間少 |

---

## Tips

- 1時間ごとに確認推奨
- 遅延時は `/bolt:end` でゴール調整を検討
