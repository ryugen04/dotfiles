# 予算管理ルール（絶対遵守）

NO FAST_MODE PERMANENT_ON WITHOUT EXPLICIT BUDGET PLANNING

## 原則

**月固定費 $40 (Claude Pro $20 + ChatGPT Plus $20) を上限とする。新規オプション有効化は必ず予算影響を評価してから行う。**

## 月固定費の目標

| サービス | 費用 |
|---------|------|
| Claude Pro | $20/月 |
| ChatGPT Plus | $20/月 |
| **合計** | **$40/月** |

> この $40 が月次のレッドライン。超過が見込まれる変更は禁止または要ユーザー承認。

## 禁止事項

| 禁止 | 理由 |
|------|------|
| `~/.claude/settings.json` で `"fastMode": true` を **常時 ON** にする | usage credits を別建て消費。月 $100+ になりうる |
| `~/.codex/config.toml` のプロファイル設定で fast モードを永続化するキー全般を **常時 ON** にする | 同様の理由で使用量が跳ね上がる |
| 新オプション追加時に予算影響を評価せず有効化する | 気づかないうちに固定費を超過する |

> 注: `"fastMode": true` は Claude Code 公式の settings.json キー名 (`https://code.claude.com/docs/en/fast-mode` 参照)。`/fast` コマンドの永続化フラグであり、常時 ON にすると usage credits を別建てで消費する。

## 許可事項

| 許可 | 条件 |
|------|------|
| 緊急時に `/fast` を手動 ON | 用件終了後に `/fast off` で戻す。判断はユーザー (人間) のケースバイケース |
| サブスク内 (Claude Pro / ChatGPT Plus) で完結する設定変更 | 追加課金が発生しないことを確認してから適用 |
| フォールバック目的の `codex exec --profile fast` (gpt-5.4-mini) 単発利用 | 軽量タスクや実装失敗時のリカバリ用。月固定費 ($40) を超えない範囲で |

## 合理化対策

| 言い訳 | 反論 |
|--------|------|
| "少し速くなるだけ" | usage credits の別建て消費は累積する。月次で確認しないと気づかない |
| "一時的だから" | 「一時的」な設定が残り続けた事例が多数ある。手動 OFF を確実に実施すること |
| "必要なときだけ" | 常時 ON は「必要なとき以外」も消費する。そのための手動運用ルール |

## Red Flags -- STOP

- `settings.json` を編集する前に `fastMode` や fast モード永続化キーの影響を評価していない
- `/fast` を ON にしたまま複数セッションをまたいでいる
- 新しい課金オプションを承認なしに有効化しようとしている

## 月次確認手順

毎月以下を確認し、月固定費 $40 を超えていないかチェック:

1. Claude usage credits: https://platform.claude.com/settings/organization/billing
2. ChatGPT 使用量: https://platform.openai.com/usage (該当する場合)
3. Cursor billing (解約後は履歴のみ): https://cursor.com/account

超過時は `~/.claude/rules/budget-management.md` の禁止事項に違反していないか見直す。

## 関連リンク

- Claude Code Fast Mode: https://code.claude.com/docs/en/fast-mode
- Anthropic Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Cursor 料金体系 (参考、解約済み): https://cursor.com/pricing

## 関連

- モデル選択ガイド: `~/.claude/rules/delegation.md`
- パッケージインストール禁止: `~/.claude/rules/no-install-without-approval.md`

---

**最終更新**: 2026-06-12
**背景**: Cursor 解約後の月固定費 $40 ラインを守るため。`fastMode: true` 常時 ON は usage credits 別建て消費で月 $100+ になりうることが判明し、禁止を明文化。
