# Claude Harness (Common Contract)

このディレクトリはプロジェクト非依存の Claude 実行契約を定義する。

## Interfaces

- `claude-plan-review`
- `claude-code-review`
- `claude-analysis`

上記 wrapper は固定プロンプトを `claude -p` に渡す。

## Hard Auth Guard

wrapper 実行前に `claude-guard-auth` を実行する。

- `ANTHROPIC_API_KEY` がセットされていたら失敗
- `claude auth status --json` の `authMethod` が `api_key` なら失敗

## ai-dlc Contract

- artifact phase: `plan`, `research`, `review`, `execution`, `learnings`
- 依存関係:
  - `plan` が無い状態で `implementation` に進まない
  - `review` が無い状態で `implementation` に進まない
  - 終了前に `execution` と `learnings` を残す
- 命名:
  - `plan-id`: `YYYYMMDD-topic-slug`
  - `artifact`: `<plan-id>-<phase>.md`

## Trial -> Permanent Loop

1. 失敗イベントを `learnings` に記録する
2. 再発条件を明記する
3. 再発防止の恒久化先（hook/rule/template/docs）を決める
4. 次セッションへ持ち越す条件を明記し、未解消は close しない
