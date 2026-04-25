# ビルドエラー対処の鉄則（絶対遵守）

NO DELETING CODE TO FIX BUILD ERRORS

## 原則

**ビルドエラーが発生した場合、コードを削除・修正して回避することを絶対に禁止する。**

エラーの原因が「上流ブランチにある変更が取り込まれていない」ことである場合、正しい対処は:

```bash
# <upstream> はプロジェクトの主幹ブランチ（develop / main 等）
git pull --rebase origin <upstream>
```

## 禁止行為

| 禁止行為 | なぜ禁止か |
|---------|-----------|
| エラーになる行を削除 | 上流の正当な変更を消してしまう |
| 存在しないフィールド/メソッドを削除 | マージ後にコンパイルエラーになる |
| switch文のcaseを削除 | 実行時エラーの原因になる |
| default句を追加してエラーを握りつぶす | バグを隠蔽する |

## 正しい対処フロー

1. **エラーメッセージを確認**
   - 「Property X does not exist」→ 新フィールドが未取得
   - 「Type X is not assignable」→ 型定義が古い

2. **上流との差分を確認**
   ```bash
   git log origin/<upstream>..HEAD --oneline
   git diff origin/<upstream>...HEAD --stat
   ```

3. **rebaseで取り込む**
   ```bash
   git fetch origin
   git pull --rebase origin <upstream>
   ```

4. **コンフリクトがあれば解決**
   - 両方の変更を正しくマージ
   - 削除ではなく統合

## 合理化対策

| 言い訳 | 反論 |
|--------|------|
| "エラーの原因が分からない" | rebaseを試せ。8割は上流未取り込みが原因 |
| "このコード使われてないはず" | 上流のdiffを確認しろ。他の人が追加した変更かもしれない |
| "テスト通すために一旦消す" | テストが落ちるのは上流同期不足。rebaseが先 |

## 違反時の対応

誤ってコードを削除・修正した場合:

1. **即座に作業を中断**
2. **変更を取り消す**: `git checkout -- <file>` または `git stash`
3. **正しい手順でrebase**
4. **再度ビルド確認**

---

**最終更新**: 2026-04-18（Phase 2 グローバル化で develop→<upstream> 抽象化）
