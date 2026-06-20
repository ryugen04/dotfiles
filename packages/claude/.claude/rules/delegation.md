# 責務分担・コンテキスト分離ルール（常時適用）

## 責務分担

```
┌──────────────────────────────────────────────────┐
│              Claude Code（メイン）               │
│            = オーケストレーター                  │
│       対話 / 判断 / Plan策定 / 軽微な修正        │
└─────────────────┬────────────────────────────────┘
                  │ Task →
        ┌─────────┼──────────┬─────────────┐
        ▼         ▼          ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Codex    │ │ Web      │ │ 専門     │ │ codex-   │
│ CLI      │ │ Search   │ │ Agent    │ │ reviewer │
│ (第一選択)│ │ /Fetch   │ │ 検証等   │ │ レビュー │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### Claude Code（メイン）= オーケストレーター

| やること | やらないこと |
|---------|------------|
| ユーザーとの対話 | 大量ファイル読み込み |
| タスク分解・委託 | 大規模コーディング（3ファイル以上） |
| Plan策定・軽微な修正（1-2ファイル） | 大規模調査 |
| 結果の統合・報告 | 画面操作 |
| 知見の永続化 | |

### Codex CLI = 実装+調査担当（第一選択）

| 用途 | 呼び出し |
|------|---------|
| 実装（CRUD、テスト、リファクタリング） | `Task → codex-implementer` |
| 大規模コード調査・依存関係追跡 | `Task → codex-implementer` |

### codex-reviewer = レビュー担当（読み取り専用）

| 用途 | 呼び出し |
|------|---------|
| コードレビュー（並列起動の片側） | `Task → codex-reviewer` または `/codex:review` |
| Plan / ドキュメントの技術的正確性確認 | `Task → codex-reviewer` |

- `codex exec --profile review` (gpt-5.5, read-only) を使う
- 書き込み不可なので Plan ファイルや調査ドキュメントの誤編集リスクなし
- 詳細は `~/.claude/rules/document-review.md` 参照

## モデル選択ガイド

タスク規模に応じて Codex プロファイルとモデルを選択する。

| タスク規模 | プロファイル / モデル | 用途例 |
|-----------|---------------------|--------|
| 軽量タスク | `codex exec --profile fast` (gpt-5.4-mini) | CRUD、テスト追加、リネーム |
| 中〜大タスク | `codex exec --profile implement` (gpt-5.5) | ロジック実装、設計変更 |
| レビュー | `codex exec --profile review` (gpt-5.5, read-only) | コードレビュー、調査 |

### Subagent モデル選択 (Claude)

- subagent の YAML frontmatter に `model: haiku` を指定 (軽量タスク向け)
- `effort: low` の機械的注入は要調査 (現在は未対応)

> `/fast` モードの取り扱いは `~/.claude/rules/budget-management.md` を参照。

## コンテキスト分離（絶対原則）

**メインコンテキストを汚染しない。すべてサブエージェントで実行する。**

### メインでの直接操作

| 操作 | 許可 | 理由 |
|------|------|------|
| Glob/Grep（ピンポイント） | 許可 | 軽量、特定ファイル検索 |
| Read（単一ファイル） | 許可 | 軽量、内容確認 |
| Read（大量・長文） | **非推奨** | Codex CLIに委託 |
| Write/Edit | **非推奨** | Codex CLIに委託 |
| Bash（ビルド等） | **非推奨** | サブエージェントに委託 |
| Playwright MCP | **禁止** | `ui-verifier`に委託 |

### 委託時の品質基準

- 省略禁止: 「他にも...」「など」で逃げない
- 私見禁止: 推測・提案は書かない、事実のみ
- 具体性: 必ず引用元（ファイル:行番号 or URL）を付ける
- 出力先: 非自明な作業・cross-agent作業は `.careflow/cases/<case_id>/results/` と `evidence/` を正本にする。`.claude/work/` は一時メモのみ
- 委託ヘッダ: `~/.claude/rules/careflow-workspace.md` の `PLAN_FILE` / `ORDER_FILE` / `EXPECTED_RESULT_PATH` 固定ヘッダを説明文より前に置く

### Careflow 委託ルール

| 委託先 | 必須入力 | 必須出力 |
|---|---|---|
| Codex CLI | PLAN_FILE, ORDER_FILE, EXPECTED_RESULT_PATH | RESULT file, evidence |
| Claude subagent | ORDER_FILE as subplan | RESULT file or review/evidence |
| Reviewer | PLAN/ORDER plus target diff | review result under `.careflow` |

chat要約だけで委託しない。ORDERがない場合は委託前に作成する。

## Git 操作

### 許可条件

| 操作 | 許可 | 条件 |
|------|------|------|
| `git status/diff/log/add` | 常時許可 | - |
| `git commit` | 常時許可 | 1行メッセージ、Co-Authored-By禁止 |
| `git push/merge/rebase/checkout/reset` | **禁止** | ユーザー明示指示必須 |

**push は絶対禁止。ユーザーが「pushして」と言うまで実行しない。**

### git -C の使用（必須）

マルチリポジトリ環境では `git -C /path/to/repo` を使用。

---

**最終更新**: 2026-06-17
