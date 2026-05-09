# Codex 運用ガイド

このディレクトリは dotfiles で管理する Codex CLI、hooks、skills、subagents、AI-DLC 連携の使い方をまとめる。

AI-DLC の workspace / overlay そのものは `docs/ai-dlc/` を参照する。ここでは Codex セッションから見た日常運用、設定編集、hook block からの復旧、user-local fallback を扱う。

## Documents

- `interactive-profiles.md`: 対話セッションと profile の使い分け。
- `ai-dlc-context.md`: AI-DLC 設定済みディレクトリと Codex user-local fallback。
- `block-delegation-policy-matrix.md`: hook block 時の allow / block / mandatory action / forbidden recovery の正本。
- `hook-block-recovery.md`: hook / permission / tool block 時の復旧手順。
- `config-authoring.md`: Codex config / hooks / skills / subagents の整備ルール。

## 基本方針

- 対話は日本語で行う。
- Codex 設定、hooks、skills、subagents を触る作業は `codex_config_edit` として扱う。
- 非自明な作業は plan を作る。ただし `.codex/plans/**` は local workflow state であり、通常は commit しない。
- project-local AI-DLC がある場所では既存 workspace / root-system を優先する。
- project-local AI-DLC がない場所では、Codex user-local fallback を使える。
