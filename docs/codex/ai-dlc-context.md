# AI-DLC context と Codex user-local fallback

Codex は現在地に応じて AI-DLC の state を次の優先順位で扱う。

1. `workspace.yaml` がある場合: 既存 AI-DLC task workspace を使う。
2. `ai-dlc/project-metadata.yaml` または `sango.yaml` がある場合: project-local root-system / control-plane を使う。
3. どちらもない場合: project-local AI-DLC 設定を推奨しつつ、Codex user-local fallback を使える。

## context の確認

```bash
ai-dlc context
```

出力は JSON で、主に次を見る。

- `mode`: `task_workspace` / `project_root` / `user_local_available` / `none`
- `control_plane_scope`: `project` / `user_local` / `none`
- `root`: 実際に使う control-plane root
- `user_local_root`: fallback 作成先
- `recommendation`: 次に取るべき方針

## Codex user-local fallback

project-local AI-DLC がない場所でも、Codex はユーザー単位の fallback state を作れる。

```bash
ai-dlc ensure-context
```

作成先:

```text
~/.codex/ai-dlc/user-workspaces/<stable-project-id>/
```

作成される主なディレクトリ:

- `plans/`
- `decisions/`
- `docs/`
- `evidence/`
- `handoff/`
- `quality/`
- `logs/`
- `context.yaml`

## 運用ルール

- project-local AI-DLC がある場合は必ずそちらを優先する。
- user-local fallback は git に commit しない。
- チームや repo に残すべき workflow は、あとで明示的に project-local AI-DLC へ移す。
- hook は project-local AI-DLC がないだけでは read-only 作業を止めない。
