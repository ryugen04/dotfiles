---
name: bolt:end
description: ボルト終了: 振り返りと翌日申し送り
allowed-tools:
  - Read
  - Write
  - Glob
  - Bash
  - TaskList
  - TaskUpdate
---

# ボルト終了（/bolt:end）

1日ボルトの終了イベント。振り返りと翌日への申し送りを作成。

---

## 実行手順

### 1. 今日の成果収集

```bash
# 今日のコミット一覧
git log --oneline --since="00:00" --format="%h %s (%cr)"

# 変更ファイル統計
git diff --stat $(git log --since="00:00" --format="%H" | tail -1)^..HEAD 2>/dev/null || echo "コミットなし"

# 未コミット変更
git status --short
```

### 2. タスク完了確認

TaskListで残タスクを確認し、完了したものはTaskUpdateで更新。

### 3. 差分サマリ生成

```markdown
## 本日の成果（YYYY-MM-DD）

### 完了タスク
- [x] タスク1
- [x] タスク2

### 未完了（翌日継続）
- [ ] タスク3（理由: 〇〇で想定以上の時間）

### コミット一覧
| Hash | メッセージ | 時刻 |
|------|----------|------|
| abc1234 | feat: 〇〇を追加 | 10:30 |
| def5678 | fix: △△を修正 | 14:15 |

### 変更統計
- ファイル数: X files
- 追加行: +XXX
- 削除行: -YYY
```

### 4. 振り返り（Keep/Problem/Try）

```markdown
### 振り返り

**Keep（継続）**
- 〇〇のアプローチは効果的だった

**Problem（問題）**
- △△で予想外の時間がかかった

**Try（改善）**
- 次回は□□を試す
```

### 5. 翌日申し送り作成

`.claude/bolt/handover.md` に書き出し:

```markdown
# 申し送り（YYYY-MM-DD → YYYY-MM-DD）

## 継続タスク
- [ ] タスク3
  - 現状: 〇〇まで完了
  - 残り: △△の実装

## 注意事項
- □□に関しては〇〇を確認してから着手

## 参照情報
- 関連PR: #123
- 参考ドキュメント: docs/foo.md
```

### 6. 日次ログ保存

`.claude/bolt/YYYY-MM-DD.md` に本日の成果を保存。

---

## 出力先

- 申し送り: `.claude/bolt/handover.md`（上書き）
- 日次ログ: `.claude/bolt/YYYY-MM-DD.md`（追記）

---

## Tips

- 15分以内に完了させる
- 未完了タスクは「なぜ」を記録（次回の見積もり精度向上）
- 申し送りは翌日の自分へのメッセージ
