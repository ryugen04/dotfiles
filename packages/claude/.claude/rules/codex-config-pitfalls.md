# Codex CLI 設定の落とし穴と対処

NO INSTALL SH CODEX RE-RUN WITHOUT UNDERSTANDING MANAGED BLOCK BEHAVIOR
NO LEGACY [profiles.X] TABLE WITH CODEX CLI >= 0.138
NO ASSUMING ALL CODEX MODELS WORK WITH CHATGPT SIGN-IN

## 原則

**Codex CLI と dotfiles の `install.sh codex` を扱う際、以下3つの落とし穴に常に注意する。事前確認なしに `install.sh codex` を実行してはならない。**

## トピック1: `install.sh codex` で managed block 内の自動生成データが消失（2026-06-12 検出）

### 状況

`install.sh codex` を実行したところ、`~/.codex/config.toml` の managed block (`# >>> dotfiles codex managed >>>` ... `# <<<`) 内にあった以下のセクションが **すべて消失** した:

- `[mcp_servers.linear]`, `[mcp_servers.notion]` (MCP サーバー定義)
- `[projects."<path>"]` (project trust 設定、4件)
- `[hooks.state.*]` (hooks のチェックサム、20件以上)

### 原因

- `install.sh codex` の `update_managed_block` 関数は **`config.toml.template` を managed block に丸ごと上書き** する設計
- template には `[tui]`, `[features]`, `[profiles.*]` のみ含まれる
- ただし **Codex CLI 自身**が動作中に `[mcp_servers.*]`, `[projects.*]`, `[hooks.state.*]` を managed block の内側に書き込む
- → 次回 `install.sh codex` で template に無い これらのセクションが消える

### 解決策

1. **machine-local 設定は managed block の外側に置く**
   - `~/.codex/config.toml` の `# <<< dotfiles codex managed <<<` 以降に `[mcp_servers.*]`, `[projects.*]` を記述
   - 外側なら template 再生成で消えない
2. **install.sh に timestamp 付き backup 機能を追加** (2026-06-12 実装)
   - `~/.codex/config.toml.bak.YYYYMMDD-HHMMSS` が自動生成される
   - 万一消えても backup から復旧可能

### 禁止事項（再発防止）

- **`~/.codex/config.toml` の managed block の内側に手動で `[mcp_servers.*]` / `[projects.*]` を書かない** (Codex 自動生成も含めて、これらは外側に逃がす)
- **`install.sh codex` を事前バックアップなしに実行しない** (現在は自動 backup されるが、念のため `~/.codex/config.toml.bak.*` の存在を確認)
- **template に個人設定 (MCP URL 等) を含めて push しない** (機密漏洩リスク)

### 正しい手順

```bash
# 1. 事前確認 (backup ファイルの存在)
ls -la ~/.codex/config.toml.bak.* 2>/dev/null

# 2. dry-run で影響範囲確認
./install.sh -n codex

# 3. 本番実行 (自動 backup される)
./install.sh codex

# 4. 復旧が必要な場合
# managed block 内の消失セクションを backup から抽出し、managed block 外に追記
cat ~/.codex/config.toml.bak.<latest-timestamp>
```

## トピック2: Codex CLI >= 0.138 で `[profiles.X]` テーブル形式が legacy（2026-06-12 検出）

### 状況

`codex exec --profile implement` 実行時にエラー:
```
Error loading config.toml: --profile `implement` cannot be used while
<home>/.codex/config.toml contains legacy `profile = "implement"`
or `[profiles.implement]` config; move those settings into
<home>/.codex/implement.config.toml and remove the legacy
profile selector/table.
```

### 原因

Codex CLI 0.138 以降、`[profiles.X]` テーブル形式 (主 `config.toml` に nested) は廃止。新形式は **個別ファイル** (`~/.codex/<profile-name>.config.toml`、top-level keys、nesting なし)。

公式 docs: https://developers.openai.com/codex/config-advanced

### 解決策

1. **個別ファイル方式に移行**: `packages/codex/.codex/profiles/<name>.config.toml` を作成し、`install.sh` で `~/.codex/<name>.config.toml` に symlink
2. **main `config.toml.template` から `[profiles.X]` を削除**
3. **profile ファイルは top-level keys のみ**:
   ```toml
   # ~/.codex/implement.config.toml の中身 (nesting なし)
   model = "gpt-5.5"
   approval_policy = "never"
   sandbox_mode = "workspace-write"
   ```

### 禁止事項（再発防止）

- **`config.toml.template` に `[profiles.X]` テーブルを追加しない** (Codex CLI 0.138 以降で legacy エラー)
- **profile ファイル内で `[profiles.X]` のように nesting しない** (top-level keys のみ)

### 正しい手順

新しい profile を追加する場合:

```bash
# 1. packages/codex/.codex/profiles/<name>.config.toml を作成 (top-level keys)
# 2. install.sh codex を実行 (symlink される)
# 3. 動作確認
codex exec --profile <name> "echo test" --sandbox read-only
```

## トピック3: ChatGPT サブスクで使える Codex モデルは限定（2026-06-12 検出）

### 状況

`codex exec --profile implement` (model = gpt-5.3-codex 指定) 実行時:
```
The 'gpt-5.3-codex' model is not supported when using Codex with a ChatGPT account.
```

### 原因

ChatGPT サブスク (Plus/Pro) で Codex CLI を使う場合、利用可能モデルは:

- **gpt-5.5** (heavy implementation)
- **gpt-5.4** (medium)
- **gpt-5.4-mini** (fast/subagent)
- **gpt-5.3-codex-spark** (ChatGPT Pro only、near-instant)

**deprecated for ChatGPT sign-in**:
- `gpt-5.3-codex`
- `gpt-5.1-codex-mini`
- `gpt-5.2` 系

公式 docs: https://developers.openai.com/codex/models

### 解決策

profile ファイルのモデルを ChatGPT 対応モデルに統一:

| Profile | Model | 用途 |
|---|---|---|
| `fast` | `gpt-5.4-mini` | 軽量タスク、subagent |
| `implement` | `gpt-5.5` | 中〜大タスク |
| `review` | `gpt-5.5` (read-only) | レビュー |

### 禁止事項（再発防止）

- **`gpt-5.3-codex` / `gpt-5.1-codex-mini` / `gpt-5.2*` を profile ファイルや `codex exec -m` に指定しない** (ChatGPT sign-in 環境でエラー)
- **直接 OpenAI API キー契約に切り替えるまではこれらのモデルを使えない**

### 正しい手順

新しいモデルが必要になったら:

1. 公式 docs (https://developers.openai.com/codex/models) で ChatGPT 対応モデルを確認
2. profile ファイルまたは `-m` オプションに使用
3. `codex exec --profile <name> "echo test" --sandbox read-only` で疎通確認

## 関連リンク

- Codex Config Advanced: https://developers.openai.com/codex/config-advanced
- Codex Models: https://developers.openai.com/codex/models
- 関連プラン: `~/.claude/plans/20260612-workflow-cursor-decommission-codex-claude-only.md`
- 予算管理: `~/.claude/rules/budget-management.md`

---

**最終更新**: 2026-06-12
**背景**: Cursor 解約 + Codex/Claude 二強体制への移行中に発生した3つの設定障害を永続化。`install.sh codex` を扱う際の必読資料。
