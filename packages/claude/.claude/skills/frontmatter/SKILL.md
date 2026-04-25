---
name: claude-code-frontmatter
description: Use when creating or updating Claude Code Skills, Subagents, Commands, or Output Styles. Provides official frontmatter reference and migration cautions.
---

# Claude Code Frontmatter Reference (2026-04-18)

Claude Code の frontmatter を仕様ベースで整理したリファレンスです。

## Skills (SKILL.md)

| name | description | 必須・任意 | 取りうる値 | デフォルト | 注意事項 |
|---|---|---|---|---|---|
| `name` | Skill 名（`/name`） | 任意 | 小文字・数字・ハイフン（最大64文字） | ディレクトリ名 | 省略時はディレクトリ名を使用 |
| `description` | Skill の用途説明 | 推奨 | 文字列 | 先頭段落（省略時） | `when_to_use` と合算で 1,536 文字上限 |
| `when_to_use` | 発火条件の補足 | 任意 | 文字列 | なし | `description` に追記される扱い |
| `argument-hint` | 補完時の引数ヒント | 任意 | 文字列（例: `[id] [path]`） | なし | `/` メニューの入力補助 |
| `disable-model-invocation` | Claude 自動呼び出し可否 | 任意 | `true` / `false` | `false` | `true` で人手起動のみ |
| `user-invocable` | ユーザー直接起動可否 | 任意 | `true` / `false` | `true` | `false` で `/` メニュー非表示（Claude 側は利用可） |
| `allowed-tools` | 事前許可するツール | 任意 | スペース区切り文字列 or YAML list | なし | 許可プロンプト抑制用。ツール制限ではない |
| `model` | Skill 実行時モデル | 任意 | モデル名 | セッション継承 | セッション設定を上書き |
| `effort` | Skill 実行時 effort | 任意 | `low` / `medium` / `high` / `xhigh` / `max` | セッション継承 | モデル対応レベルのみ有効 |
| `context` | 実行コンテキスト | 任意 | `fork` | 通常コンテキスト | `fork` で分離サブエージェント実行 |
| `agent` | `context: fork` 時の実行エージェント | 任意 | `Explore` / `Plan` / `general-purpose` / カスタム | `general-purpose` 相当 | `context: fork` とセットで使用 |
| `hooks` | Skill ライフサイクル hook | 任意 | Hook 設定オブジェクト | なし | hooks 形式は hooks 仕様に従う |
| `paths` | 自動適用するパス条件 | 任意 | glob（文字列 or YAML list） | なし | 一致ファイル作業時のみ自動適用 |
| `shell` | Skill 内 `!` 実行シェル | 任意 | `bash` / `powershell` | `bash` | `powershell` は環境要件あり |

## Subagents (`.claude/agents/*.md`)

| name | description | 必須・任意 | 取りうる値 | デフォルト | 注意事項 |
|---|---|---|---|---|---|
| `name` | サブエージェント識別子 | 必須 | 小文字・ハイフン | なし | 一意名が必要 |
| `description` | 委譲条件の説明 | 必須 | 文字列 | なし | 自動委譲判定に使われる |
| `tools` | 利用可能ツール allowlist | 任意 | ツール名列挙、`Agent(...)` 記法 | 親を継承 | 省略時は親相当、指定時は制限 |
| `disallowedTools` | 禁止ツール denylist | 任意 | ツール名列挙 | なし | `tools` と併用時は deny 適用後に allow 解決 |
| `model` | 使用モデル | 任意 | `sonnet` / `opus` / `haiku` / `inherit` / 完全モデルID | `inherit` | `--model` 相当の値を指定可能 |
| `permissionMode` | 権限モード | 任意 | `default` / `acceptEdits` / `auto` / `dontAsk` / `bypassPermissions` / `plan` | `default` 相当 | プラグイン提供 agent では無視 |
| `maxTurns` | 最大ターン数 | 任意 | 整数 | 制限なし | 長時間暴走防止に有効 |
| `skills` | 起動時に注入する Skill | 任意 | Skill 名リスト | なし | フルコンテンツ注入（名前公開のみではない） |
| `mcpServers` | 当該 agent 用 MCP | 任意 | サーバー名 or インライン定義 | なし | プラグイン提供 agent では無視 |
| `hooks` | 当該 agent 用 hooks | 任意 | Hook 設定オブジェクト | なし | プラグイン提供 agent では無視 |
| `memory` | 永続メモリ範囲 | 任意 | `user` / `project` / `local` | なし | 学習保持のスコープを指定（根拠: [sub-agents](https://code.claude.com/docs/en/sub-agents)） |
| `background` | 常時バックグラウンド実行 | 任意 | `true` / `false` | `false` | 並行処理向け |
| `effort` | 実行時 effort | 任意 | `low` / `medium` / `high` / `xhigh` / `max` | セッション継承 | モデル対応レベルのみ有効 |
| `isolation` | 分離実行モード | 任意 | `worktree` | 通常 | `worktree` で一時 git worktree 実行 |
| `color` | UI 表示色 | 任意 | `red` / `blue` / `green` / `yellow` / `purple` / `orange` / `pink` / `cyan` | なし | 視認性用途 |
| `initialPrompt` | main agent 起動時の初回 prompt | 任意 | 文字列 | なし | `--agent` / `agent` 設定時に自動投入 |

## Commands (`.claude/commands/*.md`)

`commands` は Skills と同じ仕組みで動作し、同じ frontmatter を使います（legacy 形式として継続サポート）。

| name | description | 必須・任意 | 取りうる値 | デフォルト | 注意事項 |
|---|---|---|---|---|---|
| `description` | コマンドの用途説明 | 推奨 | 文字列 | 先頭段落（省略時） | Skills と同等の解釈 |
| `when_to_use` | 発火条件の補足 | 任意 | 文字列 | なし | Skills と同等。1,536 文字上限に含まれる |
| `argument-hint` | 補完時引数ヒント | 任意 | 文字列 | なし | Skills と同等 |
| `disable-model-invocation` | Claude 自動呼び出し可否 | 任意 | `true` / `false` | `false` | Skills と同等 |
| `user-invocable` | ユーザー直接起動可否 | 任意 | `true` / `false` | `true` | Skills と同等 |
| `allowed-tools` | 事前許可するツール | 任意 | 文字列 or YAML list | なし | Skills と同等（制限ではなく事前許可） |
| `model` | 実行時モデル | 任意 | モデル名 | セッション継承 | Skills と同等 |
| `effort` | 実行時 effort | 任意 | `low` / `medium` / `high` / `xhigh` / `max` | セッション継承 | Skills と同等 |
| `context` | 実行コンテキスト | 任意 | `fork` | 通常 | Skills と同等 |
| `agent` | `context: fork` 時 agent | 任意 | agent 名 | `general-purpose` 相当 | Skills と同等 |
| `hooks` | hooks 設定 | 任意 | Hook 設定オブジェクト | なし | Skills と同等 |
| `paths` | 自動適用パス条件 | 任意 | glob | なし | Skills と同等 |
| `shell` | `!` 実行シェル | 任意 | `bash` / `powershell` | `bash` | Skills と同等 |

## Output Styles (`.claude/output-styles/*.md`)

| name | description | 必須・任意 | 取りうる値 | デフォルト | 注意事項 |
|---|---|---|---|---|---|
| `name` | スタイル名 | 任意 | 文字列 | ファイル名継承 | `/config` に表示 |
| `description` | スタイル説明 | 任意 | 文字列 | なし | `/config` ピッカー表示用 |
| `keep-coding-instructions` | コーディング向け既定指示を維持するか | 任意 | `true` / `false` | `false` | `false` だと coding 指示を抑制 |

## `tools: Agent(name1, name2)` 記法（Subagents）

- `tools` に `Agent(worker, researcher)` と書くと、その agent が spawn できる subagent type を allowlist 制御できます。
- `Agent` 単体は「全 subagent type 許可」、`Agent` 自体を省略すると spawn 不可です。
- これは `claude --agent` で main thread として動く agent の制御に効きます。
- v2.1.63 で `Task` は `Agent` に改名され、`Task(...)` は互換 alias として扱われます。

## 重要なセマンティクス差分

- Skills/Commands の `allowed-tools`:
  - 「その Skill が有効な間、許可確認を省略できるツール」を追加する機能です。
  - ツール使用可能範囲を狭める機能ではありません。
- Subagents の `tools`:
  - サブエージェントが使えるツール自体を制限する allowlist です。
  - 指定しない場合は親から継承します。

## プラグイン提供エージェントの制約

- セキュリティ上の理由で、プラグイン提供 subagent では `hooks` / `mcpServers` / `permissionMode` が適用されません（読み込み時に無視）。

## `description` + `when_to_use` 文字数制限

- Skill listing では、`description` と `when_to_use` の合算が 1,536 文字で切り詰められます。
- 長文にすると発火キーワードが落ちやすいため、先頭に重要語を置くこと。

## 削除済みフィールド（非公式・移行時に除去）

| field | 状態 | 理由 | 代替/補足 |
|---|---|---|---|
| `version` | 削除 | Skills 公式 frontmatter に存在しない | 必要なら本文で改訂履歴管理 |
| `mode` | 削除 | Skills 公式 frontmatter に存在しない | モード制御は settings/運用で実施 |
| `alwaysLoaded` | 削除 | Skills 公式 frontmatter に存在しない独自拡張 | 自動注入は hook（SessionStart など）で実現 |

## `agentTeams.teammateMode` の配置

- `teammateMode` は Skills frontmatter ではなく、`~/.claude.json` のグローバル設定キーです。
- `settings.json` に書くと schema validation error になります。

## Sources
(最終確認日: 2026-04-18)

- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/commands
- https://code.claude.com/docs/en/agent-teams
- https://code.claude.com/docs/en/hooks-guide
- https://code.claude.com/docs/en/output-styles
- https://code.claude.com/docs/en/settings
