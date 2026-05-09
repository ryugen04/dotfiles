# AI-DLC context と Codex user-local fallback

Codex は現在地に応じて AI-DLC の state を次の優先順位で扱う。

1. `workspace.yaml` がある場合: 既存 AI-DLC task workspace を使う。
2. `ai-dlc/project-metadata.yaml` または `sango.yaml` がある場合: project-local root-system / control-plane を使い、`worktrees/**/workspace.yaml` を探索する。
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
- `discoverable_workspaces`: root-system から発見できる task workspace 一覧
- `recommendation`: 次に取るべき方針

root-system では `discoverable_workspaces` に `worktrees/<issue-id>` 配下の workspace が並ぶ。

## root-system から task workspace を指定する

session の cwd を移さなくても、明示 target で task workspace を指定できる。

```bash
ai-dlc context --workspace LIN-123
ai-dlc status --workspace LIN-123
ai-dlc assignment create --workspace LIN-123 --role dlc_plan_writer
```

path を直接使いたい場合は `--workspace-root` も使える。

```bash
ai-dlc status --workspace-root worktrees/LIN-123
```

優先順位は次の通り。

- explicit `--workspace` / `--workspace-root`
- tool が指定した `workdir` / `cwd`
- session の cwd

workspace を明示しない mutating 操作は、root-system では引き続き block 対象。

## 既定の task workspace 配置

新しい task workspace は原則として root-system 配下に置く。

```text
<root-system>/worktrees/<issue-id>/
```

例:

```text
root-system/
  worktrees/
    LIN-123/
      workspace.yaml
      web/
      backend/
```

既存の外部 workspace を直ちに移動する必要はない。まずは `--workspace-root` で明示指定し、必要なら別途 adoption/migration を行う。

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
