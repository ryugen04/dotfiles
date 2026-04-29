# AI-DLC Literal Worktree Overlay Implementation Plan v0.3

Date: 2026-04-29

This document is the implementation plan for a root-system based AI-DLC workflow that:

1. opens `root-system` as the primary Orca/Codex workspace;
2. embeds `web`, `backend`, and other subprojects as literal Git worktrees under `root-system/`;
3. makes those subproject changes appear in the `root-system` diff as ordinary nested source files such as `web/src/foo.ts` and `backend/src/bar.ts`;
4. still allows each subproject to commit normally as its own Git repository;
5. prevents subproject changes from being accidentally committed or pushed from `root-system`;
6. enforces a subagent-first AI-DLC workflow where the root-system session acts as a controller, not as a worker.

This version intentionally removes the previous `changeview/*.patch` projection approach. There must be no patch artifact double-write. The IDE must see real source files with their original file extensions and syntax.

---

## 0. External assumptions

This plan relies on current Codex capabilities:

- Codex Skills are directories containing `SKILL.md` plus optional `scripts/`, `references/`, and assets. They can be explicitly invoked with `$skill-name` and are appropriate for repeatable workflows.
- Codex custom agents can be defined under user or project configuration, with required fields such as `name`, `description`, and `developer_instructions`. Subagents inherit unspecified config from the parent session, and `agents.max_depth` defaults to `1`, which prevents recursive fan-out unless explicitly raised.
- Codex hooks can run on events such as `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, and `Stop`. Hooks should be implemented as one dispatcher per event group because multiple matching command hooks may run concurrently.
- User-level Codex config lives in `~/.codex/config.toml`; project-scoped overrides can live in `.codex/config.toml` and are loaded only for trusted projects.
- `AGENTS.md` should remain a thin routing layer. Reusable workflow behavior belongs in Skills, hooks, agents, and the `ai-dlc` CLI.

References:

- Codex Skills: https://developers.openai.com/codex/skills
- Codex Subagents: https://developers.openai.com/codex/subagents
- Codex Hooks: https://developers.openai.com/codex/hooks
- Codex Config Reference: https://developers.openai.com/codex/config-reference
- Codex AGENTS.md guide: https://developers.openai.com/codex/guides/agents-md
- Codex Plugins: https://developers.openai.com/codex/plugins/build
- Git worktree: https://git-scm.com/docs/git-worktree
- Git submodules behavior: https://git-scm.com/book/en/v2/Git-Tools-Submodules

---

## 1. Core architecture

### 1.1 Workspace layout

Orca opens `root-system/`.

```txt
workspaces/LIN-123/
  root-system/
    workspace.yaml
    AGENTS.md
    .codex/
      config.toml

    ai-dlc/
      bootstrap/
        LIN-123.yaml
      plans/
        LIN-123.md
      work-items/
        LIN-123.yaml
      decisions/
        LIN-123.md
      evidence/
        LIN-123.yaml
      handoff/
        LIN-123.md
      quality/
        LIN-123.md
      executions/              # ignored
      scratch/                 # ignored
      overlay/
        LIN-123.yaml            # overlay metadata, safe to keep in root-system

    web/                        # literal Git worktree of web repo
      .git                      # gitdir pointer for web repo
      src/...
      package.json

    backend/                    # literal Git worktree of backend repo
      .git                      # gitdir pointer for backend repo
      src/...
      package.json

  .local/
    gitdirs/
      web.git/                  # preferred per-workspace Git controller
      backend.git/
    ai-dlc/
      assignments/
      leases/
      locks/
      reports/
      logs/
      traces/
      state.json
    env/
      web.env
      backend.env
    tmp/
    db/
```

### 1.2 The overlay trick

The same physical file is visible to two Git indexes.

Example:

```txt
root-system/web/src/reservation/form.tsx
```

Root-system Git sees it as:

```txt
web/src/reservation/form.tsx
```

Web Git sees it as:

```txt
src/reservation/form.tsx
```

A single source edit therefore appears in both places:

```bash
git status --short
#  M web/src/reservation/form.tsx

 git -C web status --short
#  M src/reservation/form.tsx
```

This is the desired behavior. The IDE sees real source files, not patch artifacts.

### 1.3 No `changeview`

The following are permanently removed from the design:

```txt
ai-dlc/changeview/**
ai-dlc diff-sync
dlc_changeview_writer
patch/stat/status/manifest projection files
```

The root-system diff is produced by Git itself because root-system tracks embedded source files as normal files in a local-only overlay baseline commit.

---

## 2. Non-negotiable controller/subagent principle

### 2.1 Prime directive

The root-system Codex session is a controller. It must not perform substantive work directly.

The controller may:

```txt
- read workspace state
- run read-only inspection commands
- run ai-dlc controller commands
- create assignments
- spawn subagents
- validate subagent reports
- decide AI-DLC transitions
- summarize final state
```

The controller must not directly:

```txt
- edit source files
- edit plan body manually
- edit work-items manually
- edit evidence manually
- run implementation tests manually
- debug servers manually
- repair local env manually
- commit, merge, push, reset, clean, or remove worktrees
- use apply_patch/Edit/Write except through explicitly allowed ai-dlc controller operations
```

All substantive work goes through structured subagent assignments.

### 2.2 Why this is enforced structurally

This is not only an instruction. It is enforced through:

```txt
- user-level AGENTS.md controller rule
- $workflow-* skills
- custom subagent definitions
- ai-dlc assignment and lease files
- Codex PreToolUse and PostToolUse hooks
- Codex PermissionRequest hooks
- Codex Stop hooks
- Git hooks
- ai-dlc validators
```

The expected default behavior of `$workflow-start` is not “do the task.” It is:

```txt
inspect -> assign -> spawn subagents -> collect reports -> validate -> transition
```

---

## 3. dotfiles implementation

### 3.1 Dotfiles tree

```txt
dotfiles/
  codex/
    config.toml
    AGENTS.md
    hooks.json

    agents/
      dlc-initializer.toml
      dlc-explorer.toml
      dlc-plan-writer.toml
      dlc-scope-manager.toml
      dlc-repo-worker.toml
      dlc-verifier.toml
      dlc-evaluator.toml
      dlc-handoff-writer.toml
      dlc-repairer.toml
      dlc-git-operator.toml

    ai-dlc/
      bin/
        ai-dlc
      hooks/
        dispatcher.py
      git-hooks/
        root-pre-commit
        root-pre-push
        child-pre-commit
        child-pre-push
        commit-msg
      schemas/
        workspace.v1.schema.json
        bootstrap.v1.schema.json
        plan.v2.schema.json
        work-items.v1.schema.json
        evidence.v1.schema.json
        assignment.v1.schema.json
        lease.v1.schema.json
        overlay.v1.schema.json

  agents/
    skills/
      workflow-start/
        SKILL.md
      workflow-bootstrap/
        SKILL.md
      workflow-review/
        SKILL.md
      workflow-repair/
        SKILL.md
      workflow-finish/
        SKILL.md
```

Symlinks:

```bash
~/.codex/config.toml  -> ~/dotfiles/codex/config.toml
~/.codex/AGENTS.md    -> ~/dotfiles/codex/AGENTS.md
~/.codex/hooks.json   -> ~/dotfiles/codex/hooks.json
~/.codex/agents       -> ~/dotfiles/codex/agents
~/.codex/ai-dlc       -> ~/dotfiles/codex/ai-dlc
~/.agents/skills      -> ~/dotfiles/agents/skills
```

### 3.2 User-level `~/.codex/config.toml`

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"

project_doc_fallback_filenames = [
  "AGENTS.md",
  "TEAM_GUIDE.md",
  ".agents.md"
]
project_doc_max_bytes = 65536

[features]
codex_hooks = true

[agents]
max_threads = 4
max_depth = 1
job_max_runtime_seconds = 1800
```

`max_depth = 1` is intentional. The root controller may spawn direct subagents, but subagents must not recursively spawn more subagents.

### 3.3 User-level `~/.codex/AGENTS.md`

```md
# Global AI-DLC rules

## Controller rule

When the current directory contains `workspace.yaml` with `layout.mode: literal_worktree_overlay`, treat the current Codex session as an AI-DLC root-system controller.

The controller must not directly:

- edit files
- implement code
- run tests
- debug servers
- repair env files
- generate artifacts by hand
- commit, merge, push, reset, clean, or remove worktrees

The controller may:

- inspect workspace state
- run `ai-dlc inspect`, `ai-dlc validate`, `ai-dlc assignment *`, and `ai-dlc transition`
- spawn AI-DLC subagents
- validate reports
- summarize final state

All substantive work requires a subagent assignment and a valid lease.

## Overlay rule

Embedded paths such as `web/**` and `backend/**` may appear as root-system diffs. These are real child-repo files. Do not commit them from root-system. Commit them only from their child repositories.
```

---

## 4. Project installation

### 4.1 `ai-dlc install`

Installs dotfiles-level AI-DLC machinery.

```bash
ai-dlc install
```

Responsibilities:

```txt
- verify ~/.codex/config.toml exists
- enable codex_hooks if missing
- install or verify ~/.codex/hooks.json
- install or verify ~/.codex/agents
- install or verify ~/.agents/skills
- put ai-dlc CLI on PATH
- verify Python dependencies for validator/dispatcher
- run ai-dlc self-test
```

### 4.2 `ai-dlc init-project`

Run once inside the root-system main repository.

```bash
ai-dlc init-project \
  --root-system . \
  --repo web=~/dev/repos/web \
  --repo backend=~/dev/repos/backend
```

Creates or updates:

```txt
root-system/
  AGENTS.md                  # thin only
  .codex/config.toml          # workspace boundary only
  ai-dlc/.gitkeep
  .gitignore
```

Thin `root-system/AGENTS.md`:

```md
# root-system AGENTS.md

This repository is an AI-DLC control-plane workspace.

Facts are declared in `workspace.yaml`.
Plans are stored in `ai-dlc/plans`.
Machine-readable work items are stored in `ai-dlc/work-items`.
Verification evidence is stored in `ai-dlc/evidence`.
Runtime logs, leases, locks, and reports are outside this repository under `../.local`.

The root-system session should act as a controller.
Substantive work should be delegated to AI-DLC subagents.
```

### 4.3 Root-system project `.codex/config.toml`

```toml
project_root_markers = [
  "workspace.yaml",
  ".git"
]

[sandbox_workspace_write]
writable_roots = [
  "../.local"
]
network_access = false
```

If using the alternative variant that writes Git metadata back to canonical repo `.git/worktrees`, add those Git common dirs to `writable_roots`. The preferred variant stores per-workspace Git controllers under `../.local/gitdirs`, so only `../.local` is needed.

---

## 5. Workspace initialization with literal worktree overlay

### 5.1 `ai-dlc init-workspace`

Executed after Orca creates the root-system worktree.

```bash
cd workspaces/LIN-123/root-system

ai-dlc init-workspace \
  --issue LIN-123 \
  --branch LIN-123-reservation-validation \
  --repo web=~/dev/repos/web \
  --repo backend=~/dev/repos/backend \
  --base-ref origin/main
```

Responsibilities:

```txt
1. create workspace.yaml
2. create ../.local
3. create per-workspace bare Git controllers under ../.local/gitdirs
4. add literal Git worktrees at ./web and ./backend
5. collect child repo tracked file lists
6. temporarily hide child .git pointers
7. baseline-track child repo files in root-system Git as normal files
8. create local-only root-system overlay baseline commit
9. restore child .git pointers
10. install Git hooks
11. create AI-DLC state files
12. validate overlay
```

### 5.2 Preferred child worktree creation

Create per-workspace Git controllers in `.local`.

```bash
mkdir -p ../.local/gitdirs

git clone --bare ~/dev/repos/web ../.local/gitdirs/web.git
git --git-dir=../.local/gitdirs/web.git fetch origin

git --git-dir=../.local/gitdirs/web.git \
  worktree add -B LIN-123-reservation-validation web origin/main
```

Same for `backend`.

This is still a real Git worktree. The reason to use a per-workspace bare controller is sandbox containment: commits from `web/` write to `../.local/gitdirs/web.git`, which is already in `writable_roots`.

### 5.3 Baseline tracking procedure

Do not `git add web backend` blindly. Add only files tracked by each child repo.

Recommended algorithm:

```bash
mkdir -p ../.local/overlay

git -C web ls-files -z > ../.local/overlay/web.tracked.z
git -C backend ls-files -z > ../.local/overlay/backend.tracked.z

mv web/.git ../.local/overlay/web.gitfile
mv backend/.git ../.local/overlay/backend.gitfile

python3 - <<'PY'
from pathlib import Path
import subprocess

for repo in ["web", "backend"]:
    data = Path(f"../.local/overlay/{repo}.tracked.z").read_bytes()
    paths = [p.decode() for p in data.split(b"\0") if p]
    for p in paths:
        subprocess.run(["git", "add", "-f", "--", f"{repo}/{p}"], check=True)
PY

AI_DLC_ALLOW_OVERLAY_BASELINE=1 \
  git commit -m "AI-DLC overlay baseline: LIN-123"

mv ../.local/overlay/web.gitfile web/.git
mv ../.local/overlay/backend.gitfile backend/.git
```

Why this matters:

```txt
- root-system tracks child repo files as normal files
- child repo .git pointers are not added
- untracked/generated child files are not added
- child .gitignore semantics are respected through child `git ls-files`
```

### 5.4 Overlay metadata

```yaml
# ai-dlc/overlay/LIN-123.yaml
schema: ai-dlc.overlay.v1
workspace_id: LIN-123
mode: literal_worktree_overlay
baseline_commit: "<sha>"
embedded_repos:
  web:
    path: web
    git_controller: ../.local/gitdirs/web.git
    branch: LIN-123-reservation-validation
    baseline_tracked_file_count: 1234
  backend:
    path: backend
    git_controller: ../.local/gitdirs/backend.git
    branch: LIN-123-reservation-validation
    baseline_tracked_file_count: 987
root_commit_policy:
  embedded_paths_commit_allowed_only_for_baseline: true
  root_push_forbidden: true
```

---

## 6. Workspace manifest

```yaml
schema: ai-dlc.workspace.v1

id: LIN-123
title: reservation validation fix
branch: LIN-123-reservation-validation

layout:
  mode: literal_worktree_overlay
  root_diff_hack: true

repos:
  root-system:
    path: .
    branch: LIN-123-reservation-validation
    role: control-plane

  web:
    path: web
    branch: LIN-123-reservation-validation
    role: frontend
    overlay:
      embedded: true
      parent_tracked: true
      git_controller: ../.local/gitdirs/web.git

  backend:
    path: backend
    branch: LIN-123-reservation-validation
    role: backend
    overlay:
      embedded: true
      parent_tracked: true
      git_controller: ../.local/gitdirs/backend.git

paths:
  local: ../.local
  bootstrap: ai-dlc/bootstrap/LIN-123.yaml
  plan: ai-dlc/plans/LIN-123.md
  work_items: ai-dlc/work-items/LIN-123.yaml
  decisions: ai-dlc/decisions/LIN-123.md
  evidence: ai-dlc/evidence/LIN-123.yaml
  handoff: ai-dlc/handoff/LIN-123.md
  overlay: ai-dlc/overlay/LIN-123.yaml

controller:
  no_direct_edits: true
  substantive_work_requires_subagent: true

workflow:
  wip_limit: 1
  subagent_required: true
```

### 6.1 Required identity, routing, and external metadata

The workspace manifest is not only a local layout file. It is the source of truth for:

```txt
- issue identity
- tracker/Linear linkage
- root workspace location
- canonical source repo locations
- target worktrees under root-system
- base branch and issue branch mapping
- root-export destination
- subagent routing and ownership
```

Minimum required metadata:

```yaml
schema: ai-dlc.workspace.v1

id: LIN-123
title: reservation validation fix
issue:
  tracker: linear
  id: LIN-123
  url: https://linear.app/acme/issue/LIN-123

workspace:
  root: /abs/path/workspaces/LIN-123
  root_system_path: /abs/path/workspaces/LIN-123/root-system
  local_path: /abs/path/workspaces/LIN-123/.local

branch:
  issue: LIN-123-reservation-validation
  base_ref: origin/main
  by_repo:
    root-system: origin/main
    web: origin/main
    backend: origin/main
  root_export:
    target_repo: root-system
    target_remote: origin
    target_ref: main
    export_mode: root_only

repos:
  root-system:
    path: .
    role: control-plane
    canonical_repo_path: /abs/path/repos/root-system
    canonical_repo_url: git@github.com:acme/root-system.git
    default_branch: main
    issue_branch: LIN-123-reservation-validation
    base_ref: origin/main
    base_sha: "<sha>"
    head_sha: "<sha>"

  web:
    path: web
    role: frontend
    canonical_repo_path: /abs/path/repos/web
    canonical_repo_url: git@github.com:acme/web.git
    default_branch: main
    issue_branch: LIN-123-reservation-validation
    base_ref: origin/main
    base_sha: "<sha>"
    head_sha: "<sha>"
    overlay:
      embedded: true
      parent_tracked: true
      git_controller: ../.local/gitdirs/web.git
      tracked_output_prefixes:
        - web/src/**
        - web/tests/**

  backend:
    path: backend
    role: backend
    canonical_repo_path: /abs/path/repos/backend
    canonical_repo_url: git@github.com:acme/backend.git
    default_branch: main
    issue_branch: LIN-123-reservation-validation
    base_ref: origin/main
    base_sha: "<sha>"
    head_sha: "<sha>"
    overlay:
      embedded: true
      parent_tracked: true
      git_controller: ../.local/gitdirs/backend.git
      tracked_output_prefixes:
        - backend/src/**
        - backend/tests/**
```

Rules:

```txt
- `issue.id` and `issue.url` must be present when the task is tied to Linear or another tracker.
- `workspace.root`, `workspace.root_system_path`, and `workspace.local_path` must be absolute paths.
- Each repo entry must include both canonical repo location and embedded worktree location.
- `branch.base_ref` is the source of truth for overlay initialization.
- `branch.root_export_target` is the source of truth for root-export and finish flows.
- All generated plan, handoff, work-items, evidence, assignments, and reports must refer back to these identifiers.
```

### 6.2 Output locations and ownership contract

The system must explicitly declare which files are generated where, and which agent class owns each file family.

```txt
root-system/
  workspace.yaml                          controller-owned manifest
  ai-dlc/bootstrap/<issue>.yaml           initializer/verifier
  ai-dlc/plans/<issue>.md                 plan_writer
  ai-dlc/work-items/<issue>.yaml          scope_manager
  ai-dlc/decisions/<issue>.md             plan_writer
  ai-dlc/evidence/<issue>.yaml            verifier/evaluator
  ai-dlc/handoff/<issue>.md               handoff_writer/evaluator
  ai-dlc/overlay/<issue>.yaml             initializer/repairer
  ai-dlc/quality/<issue>.md               evaluator
  docs/**                                 plan_writer or handoff_writer when explicitly assigned

../.local/ai-dlc/
  assignments/<id>.yaml                   controller/scope_manager
  leases/<session>.json                   claimed subagent runtime
  locks/*.lock                            runtime lock manager
  reports/<assignment>.json               worker/verifier/evaluator reports
  logs/*.log                              verifier/runtime logs
  traces/*.json                           optional execution traces
```

Rules:

```txt
- root-system tracked outputs must be reviewable and exportable.
- ../.local outputs are runtime state and must not be root-exported.
- Every generated file family must have one primary writer role and one validation path.
- A template is not complete unless its owner role and downstream readers are specified.
- `ai-dlc/quality/<issue>.md` is the only canonical quality artifact.
```

---

## 7. AI-DLC state model

### 7.1 Plan states

```txt
intake
  -> initializing
  -> planning
  -> plan_ready
  -> assigning
  -> executing
  -> verifying
  -> evaluating
  -> handoff_ready
  -> ready_to_finish
  -> done
```

Exception states:

```txt
any -> needs_decision
any -> repairing
any -> blocked
any -> abandoned

repairing -> previous_state
repairing -> blocked

evaluating -> executing
evaluating -> verifying
evaluating -> needs_decision
```

Forbidden transitions:

```txt
planning -> executing
executing -> ready_to_finish
verifying -> ready_to_finish
any -> done without workflow-finish
```

### 7.2 Work item states

```txt
not_started
  -> active
  -> blocked
  -> passing
  -> cancelled
```

Rules:

```txt
- WIP limit is 1.
- Only one active work item is allowed.
- A repo worker cannot mark an item passing.
- Only `ai-dlc verify-gate` may mark an item passing.
- Verification evidence is required before passing.
```

### 7.3 Plan file

```md
---
schema: ai-dlc.plan.v2
id: LIN-123
status: executing
workspace_ref: workspace.yaml
bootstrap_ref: ai-dlc/bootstrap/LIN-123.yaml
work_items_ref: ai-dlc/work-items/LIN-123.yaml
evidence_ref: ai-dlc/evidence/LIN-123.yaml
handoff_ref: ai-dlc/handoff/LIN-123.md
overlay_ref: ai-dlc/overlay/LIN-123.yaml

controller:
  no_direct_edits: true
  substantive_work_requires_subagent: true

current:
  active_item: WI-001
  next_action_type: delegate
  next_agent: dlc_repo_worker
  next_action: "Assign backend worker to implement 422 validation for WI-001."
  stop_condition: "WI-001 has verification evidence or is blocked with a structured blocker."

deadlock_policy:
  max_same_failure_attempts: 2
  max_repair_attempts: 1
  stop_hook_max_continuations_per_turn: 1
---

# LIN-123: Reservation validation fix

## Goal

Invalid reservation input should fail consistently across backend and web.

## Sprint contract

### Scope

- Backend reservation validation
- Backend 422 response
- Web API error mapping
- Web user-facing error display

### Exclusions

- No DB schema migration
- No global error middleware refactor
- No unrelated design/copy changes

## Acceptance criteria

- Backend returns HTTP 422 with `INVALID_RESERVATION`
- Web displays the mapped error message
- Existing valid reservation flow still passes
- Required static, unit, integration, and E2E verification pass

## Work items

See `ai-dlc/work-items/LIN-123.yaml`.

## Verification evidence

See `ai-dlc/evidence/LIN-123.yaml`.
```

### 7.4 Generated template contract

The generated templates must already contain enough structure that the next controller session can continue without inventing missing metadata.

#### Plan template requirements

Every generated plan must contain:

```txt
- issue id and issue url
- workspace root and root-system path
- embedded repo list
- base ref and issue branch
- root-export target branch
- output files owned by each role
- current active item / next action / next agent
- verifier and evaluator handoff expectations
```

Required frontmatter shape:

```yaml
schema: ai-dlc.plan.v2
id: LIN-123
title: reservation validation fix
status: planning
issue:
  tracker: linear
  id: LIN-123
  url: https://linear.app/acme/issue/LIN-123
workspace_ref: workspace.yaml
overlay_ref: ai-dlc/overlay/LIN-123.yaml
bootstrap_ref: ai-dlc/bootstrap/LIN-123.yaml
work_items_ref: ai-dlc/work-items/LIN-123.yaml
evidence_ref: ai-dlc/evidence/LIN-123.yaml
handoff_ref: ai-dlc/handoff/LIN-123.md
root_export:
  target_repo: root-system
  target_remote: origin
  target_ref: main
target_repos:
  - web
  - backend
controller:
  no_direct_edits: true
  substantive_work_requires_subagent: true
current:
  active_item: null
  next_action_type: delegate
  next_agent: dlc_scope_manager
  next_action: create initial work items, verification gates, and assignments
  stop_condition: plan, work-items, and bootstrap are ready for repo workers
```

#### Handoff template requirements

Every generated handoff must contain:

```txt
- issue id and url
- workspace root and current branch map
- active assignments and lease sessions
- per-repo current branch, dirty state, and do-not-touch paths
- next best action and required next agent
- root-export status
- pending verifier/evaluator obligations
```

#### Work-items template requirements

Each work item must contain:

```txt
- id, title, status, repo ownership
- writable scopes
- verifier gate
- evaluator gate
- source Linear/plan reference
- expected deliverables and blocked-by links
```

#### Bootstrap template requirements

Every generated bootstrap file must contain:

```txt
- issue id and url
- workspace_ref
- repo inventory
- repo-wise base_ref / base_sha / head_sha
- root_export target structure
- overlay readiness
- hooks readiness
- child repo readiness
- blocking issues
- next_agent and next_action
```

#### Evidence template requirements

Every generated evidence file must contain:

```txt
- work_item id
- repo
- issue branch
- verified HEAD sha
- verified tree/index clean state
- command
- expected outcome
- actual result
- log_ref
- artifact_refs
- verdict
- recorded_by role
```

Verifier evidence is append-only. Evaluator must not mutate verifier evidence entries.

#### Overlay template requirements

Every generated overlay file must contain:

```txt
- workspace_id
- issue id
- issue branch
- root-system base ref
- per-repo base_ref / base_sha / head_sha
- tracked_files_ref or tracked manifest location
- baseline commit
- baseline creation status
- recovery metadata for temporary .git pointer moves
```

#### Decisions template requirements

Every generated decisions file must contain:

```txt
- issue id
- workspace id
- decision timestamp
- actor role
- affected section or workflow stage
- rationale
- approval boundary if the decision bypasses default orchestration
```

#### Quality template requirements

Every generated quality file must contain:

```txt
- issue id
- evaluator verdict
- evidence coverage summary
- residual risks
- finish recommendation
- blockers to ready_to_finish if any
```

#### Assignment template requirements

Each assignment must contain:

```txt
- workspace_id
- issue id/url
- agent role and agent name
- current phase
- target repo
- writable and forbidden path scopes
- deliverables
- report output path
- linked work item
- branch expectations
```

No generated template may leave the implementer to infer:

```txt
- which repo is authoritative
- which branch to work on
- where to write outputs
- which subagent should run next
- how the result maps back to the issue tracker
```

---

## 8. Subagent system

### 8.1 Agent roles

| Agent | Role | Write scope |
|---|---|---|
| `dlc_initializer` | Bootstrap and local readiness | `ai-dlc/bootstrap/**`, `../.local/**` |
| `dlc_explorer` | Read-only code/context exploration | none |
| `dlc_plan_writer` | Plan and decisions | `ai-dlc/plans/**`, `ai-dlc/decisions/**` |
| `dlc_scope_manager` | Work-item creation/update | `ai-dlc/work-items/**` |
| `dlc_repo_worker` | Implementation in exactly one child repo | lease-scoped paths under `web/**` or `backend/**` |
| `dlc_verifier` | Run verification commands and record evidence | `ai-dlc/evidence/**`, `../.local/ai-dlc/logs/**` |
| `dlc_evaluator` | Independent review/evaluation | `ai-dlc/evidence/**`, optional read-only reports |
| `dlc_handoff_writer` | Session handoff | `ai-dlc/handoff/**` |
| `dlc_repairer` | Local env/worktree repair | `../.local/**`, safe env symlinks |
| `dlc_git_operator` | Commit/merge/export/cleanup | explicit user approval only |

### 8.2 Role constraints

#### `dlc_explorer`

```txt
- read-only
- may inspect source and docs
- must not edit files
- must not run tests that write source
- returns code path map and risk report
```

#### `dlc_plan_writer`

```txt
- may write ai-dlc/plans/** and ai-dlc/decisions/** only
- may not edit web/** or backend/**
- may not run implementation commands
- must include next_action and stop_condition
```

#### `dlc_scope_manager`

```txt
- may write ai-dlc/work-items/** only
- may create/update active item
- may not mark an item passing
- must enforce WIP=1
```

#### `dlc_repo_worker`

```txt
- must claim an assignment before editing
- may edit only one assigned repo
- may edit only lease-scoped paths
- may not edit plans, work-items, evidence, handoff, or other repos
- may not commit/merge/push
- must write an assignment report
```

#### `dlc_verifier`

```txt
- runs assigned verification commands
- records evidence
- writes logs under ../.local/ai-dlc/logs
- must not fix failures directly
- must not modify tracked source files
```

#### `dlc_evaluator`

```txt
- independent from repo worker
- reviews diffs, plan alignment, evidence, risks
- may recommend returning to executing/verifying/needs_decision
- does not edit source
```

#### `dlc_git_operator`

```txt
- invoked only by $workflow-finish or explicit user request
- handles child repo commit/push if approved
- handles root-export and overlay-cleanup if approved
- never performs destructive operations without explicit approval
```

#### `dlc_initializer`

```txt
- may write only bootstrap, overlay, and ../.local runtime state
- may run overlay-init, validate-overlay, install-project-hooks, overlay-repair
- must not edit web/** or backend/** source files
- must emit readiness outputs and recovery metadata
```

#### `dlc_handoff_writer`

```txt
- may write handoff and optional summary docs only
- must not edit evidence entries produced by verifier
- must include assignment/lease/branch/export status snapshots
- must not advance finish state on its own
```

#### `dlc_repairer`

```txt
- may modify only ../.local, hook installation state, and overlay recovery artifacts
- may restore missing .git pointers and regenerate local controllers
- must not modify tracked source files
- destructive cleanup requires explicit approval boundary
```

### 8.3 Example custom agent file

```toml
# ~/.codex/agents/dlc-repo-worker.toml

name = "dlc_repo_worker"
description = "AI-DLC implementation worker. Use for scoped code changes in exactly one assigned embedded child repository."
sandbox_mode = "workspace-write"
model_reasoning_effort = "high"

developer_instructions = """
You are an AI-DLC repository worker.

You must claim your assignment before writing:
  ai-dlc agent-claim --assignment <id>

You may edit only the assigned repository and paths in your lease.
You must not edit root-system control-plane files.
You must not edit another child repository.
You must not commit, merge, push, reset, clean, restore, or remove worktrees.

Before editing:
- read workspace.yaml
- read the plan
- read the active work item
- read the target repo AGENTS.md if present
- inspect relevant source files

After editing:
- report files touched
- report commands run
- report blockers
- write the assignment report
- release the assignment
"""
```

### 8.4 Required controller orchestration contract

Subagent-first is not satisfied by merely defining agent files. The controller must follow a deterministic delegation sequence.

Required default sequence for implementation work:

```txt
1. controller validates workspace and overlay
2. controller spawns read-only explorers in parallel for each likely affected repo
3. controller spawns plan_writer if plan/body/current action is stale
4. controller spawns scope_manager if work-items or verification gates are stale
5. controller creates assignments from work-items
6. controller spawns exactly one repo_worker per active repo assignment
7. controller waits for reports, not raw diffs only
8. controller spawns verifier after repo_worker reports
9. controller spawns evaluator after verifier evidence exists
10. controller spawns handoff_writer before finish readiness
11. controller uses git_operator only for approved commit/export/cleanup steps
```

Parallelism rules:

```txt
- explorers may run in parallel
- one repo_worker per repo may run in parallel only if lock scopes do not overlap
- verifier must not overlap with an active writer on the same repo
- evaluator must be logically independent from the repo_worker that implemented the change
- handoff_writer runs after reports and evidence exist
```

The root controller is considered out of policy if it:

```txt
- edits tracked files itself
- skips explorer/plan/scope phases without recorded justification
- runs repo tests itself instead of through verifier or repo_worker
- commits child repos directly
- finishes without evaluator and handoff output
```

### 8.5 Spawn gating and stale-state definition

The controller may only skip or reorder the default orchestration if the exception is recorded in `ai-dlc/decisions/<issue>.md`.

Required skip record:

```txt
- timestamp
- previous state
- skipped agent or step
- exact reason
- evidence used
- who approved the deviation
```

A plan or workspace is considered stale if any of the following is true:

```txt
- `plan.current.next_agent` is missing
- `plan.current.next_action` is missing
- explorer reports predate the latest relevant repo diff
- work items lack verifier or evaluator gates
- active assignment does not match active work item
- handoff does not mention current assignments or branch map
- quality verdict predates the latest verifier evidence
```

The controller may spawn only:

```txt
- the agent named in `plan.current.next_agent`, or
- the agent named in a validated assignment/report `next_recommendation`, or
- `dlc_explorer` during initial exploration, or
- `dlc_repairer` after transition to `repairing`
```

---

## 9. Assignment, lease, and lock model

### 9.1 Assignment file

```yaml
# ../.local/ai-dlc/assignments/A004.yaml
schema: ai-dlc.assignment.v1
id: A004
workspace_id: LIN-123
role: dlc_repo_worker
agent: dlc_repo_worker
status: assigned
phase: executing
repo: backend
work_item: WI-001
writable:
  - backend/src/reservations/**
  - backend/tests/reservations/**
forbidden:
  - web/**
  - ai-dlc/**
  - workspace.yaml
  - .codex/**
deliverables:
  - source_changes
  - worker_report
issue:
  tracker: linear
  id: LIN-123
  url: https://linear.app/acme/issue/LIN-123
branch:
  issue: LIN-123-reservation-validation
  base_ref: origin/main
result_ref: ../.local/ai-dlc/reports/A004.json
expires_at: "2026-04-29T10:30:00+09:00"
```

### 9.2 Lease file

```json
{
  "schema": "ai-dlc.lease.v1",
  "session_id": "sess_...",
  "assignment_id": "A004",
  "role": "dlc_repo_worker",
  "repo": "backend",
  "work_item": "WI-001",
  "phase": "executing",
  "issue": {
    "tracker": "linear",
    "id": "LIN-123",
    "url": "https://linear.app/acme/issue/LIN-123"
  },
  "branch": {
    "issue": "LIN-123-reservation-validation",
    "base_ref": "origin/main"
  },
  "writable": [
    "backend/src/reservations/**",
    "backend/tests/reservations/**"
  ],
  "forbidden": [
    "web/**",
    "ai-dlc/**",
    "workspace.yaml"
  ],
  "created_at": "2026-04-29T10:00:00+09:00",
  "expires_at": "2026-04-29T10:30:00+09:00",
  "status": "claimed"
}
```

### 9.3 Lock files

```txt
../.local/ai-dlc/locks/
  repo-web.lock
  repo-backend.lock
  plan.lock
  work-items.lock
  evidence.lock
  handoff.lock
```

Rules:

```txt
- A repo worker must acquire a repo lock.
- Only one writer may hold a repo lock at a time.
- A plan writer must acquire plan.lock.
- A scope manager must acquire work-items.lock.
- A verifier may run only when no repo worker is actively writing the same repo.
- Expired locks require controller review before release.
```

Atomicity requirements:

```txt
- `agent-claim` must perform assignment validation, lock acquisition, and lease issuance as one transaction
- lock files must record owner session, nonce, created_at, expires_at, and target repo
- double-claim on the same repo must result in exactly one success
- stale lock takeover requires explicit controller review and a recorded decision
```

### 9.4 Assignment report

```json
{
  "assignment_id": "A004",
  "role": "dlc_repo_worker",
  "status": "reported",
  "repo": "backend",
  "work_item": "WI-001",
  "issue": {
    "tracker": "linear",
    "id": "LIN-123",
    "url": "https://linear.app/acme/issue/LIN-123"
  },
  "branch": {
    "issue": "LIN-123-reservation-validation",
    "base_ref": "origin/main"
  },
  "summary": "Updated reservation validation to return 422 with INVALID_RESERVATION.",
  "files_touched": [
    "backend/src/reservations/validation.ts",
    "backend/tests/reservations/validation.test.ts"
  ],
  "commands_run": [
    {
      "command": "pnpm test tests/reservations",
      "result": "pass",
      "log_ref": "../.local/ai-dlc/logs/A004-backend-test.log"
    }
  ],
  "blockers": [],
  "scope_requests": [],
  "next_recommendation": {
    "phase": "verifying",
    "assignment_role": "dlc_verifier",
    "reason": "Implementation completed; independent verification required."
  }
}
```

### 9.5 Assignment and report linkage rules

Assignments, leases, reports, evidence, and handoff must form a navigable chain.

Required linkage:

```txt
workspace.yaml
  -> plan
  -> work-items
  -> assignments
  -> leases
  -> reports
  -> evidence
  -> handoff
```

Every assignment and report must include:

```txt
- workspace_id
- issue id
- issue url
- target repo
- issue branch
- source work item
- output report path
- next recommended phase or next agent
```

This is mandatory so a resumed controller can reconstruct state without reading the entire conversation log.

---

## 10. Skills

### 10.1 `$workflow-start`

Primary skill. It must delegate rather than work directly.

```md
---
name: workflow-start
description: Start or continue an AI-DLC literal worktree overlay workflow. Use for root-system, workspace.yaml, embedded web/backend worktrees, plans, implementation, verification, or multi-repo tasks.
---

# AI-DLC workflow start

## Prime directive

The current root-system session is a controller, not a worker.

Do not directly edit files, implement code, run tests, debug servers, repair env, or generate source artifacts.

All substantive work must be delegated through AI-DLC assignments and subagents.

## Required sequence

1. Run `ai-dlc inspect`.
2. Run `ai-dlc validate-overlay`.
3. Validate bootstrap state.
4. Validate WIP=1.
5. Spawn `dlc_explorer` agents for likely affected repos.
6. Spawn `dlc_plan_writer` and `dlc_scope_manager` if plan/work-items are missing or stale.
7. Validate plan and work-items.
8. Create repo-worker assignments.
9. Spawn `dlc_repo_worker` agents, one repo per assignment.
10. Collect reports.
11. Spawn `dlc_verifier`.
12. Spawn `dlc_evaluator`.
13. Spawn `dlc_handoff_writer`.
14. Transition to `ready_to_finish`, `blocked`, or `needs_decision`.

## Prohibited controller actions

If you are about to edit a file directly, stop and create a subagent assignment instead.
```

### 10.2 `$workflow-bootstrap`

Used when initialization/local readiness is not complete.

Sequence:

```txt
inspect -> initializer assignment -> repairer if needed -> bootstrap evidence -> plan_ready or blocked
```

### 10.3 `$workflow-review`

Review without implementation.

Sequence:

```txt
validate-overlay -> status all -> child repo diffs -> evidence check -> evaluator -> handoff update
```

### 10.4 `$workflow-repair`

Repair local env or worktree problems.

Sequence:

```txt
transition repairing -> repairer assignment -> validate-overlay -> return previous state or blocked
```

### 10.5 `$workflow-finish`

Finish flow.

Sequence:

```txt
clean-state-check -> child repo commit/push if approved -> root-export -> overlay-cleanup if approved -> done
```

---

## 11. Codex hooks

### 11.1 `~/.codex/hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOME/.codex/ai-dlc/hooks/dispatcher.py",
            "timeout": 10,
            "statusMessage": "Loading AI-DLC controller policy"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOME/.codex/ai-dlc/hooks/dispatcher.py",
            "timeout": 10,
            "statusMessage": "Checking AI-DLC prompt"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|apply_patch|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOME/.codex/ai-dlc/hooks/dispatcher.py",
            "timeout": 10,
            "statusMessage": "Checking AI-DLC lease"
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "matcher": "Bash|apply_patch|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOME/.codex/ai-dlc/hooks/dispatcher.py",
            "timeout": 10,
            "statusMessage": "Checking AI-DLC permission"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash|apply_patch|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOME/.codex/ai-dlc/hooks/dispatcher.py",
            "timeout": 20,
            "statusMessage": "Validating AI-DLC side effects"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOME/.codex/ai-dlc/hooks/dispatcher.py",
            "timeout": 20,
            "statusMessage": "Checking AI-DLC completion gate"
          }
        ]
      }
    ]
  }
}
```

### 11.2 SessionStart policy

If `workspace.yaml` exists and layout is `literal_worktree_overlay`, inject context:

```txt
AI-DLC controller mode is active.
Root-system session is controller-only.
Do not edit files directly.
Use subagents for all substantive work.
Embedded child repo paths appear in root diff but must not be root-committed.
```

### 11.3 UserPromptSubmit policy

```txt
- If user asks for implementation from root-system, convert to subagent-first workflow.
- If bootstrap is not ready, direct to workflow-bootstrap.
- If more than one active work item exists, block.
- If user asks for destructive git operation, require workflow-finish and explicit approval.
```

### 11.4 PreToolUse policy

Deny when:

```txt
- controller uses apply_patch/Edit/Write
- controller runs write-like Bash commands
- unclaimed session writes files
- lease is expired
- lease role does not permit the path
- repo worker edits outside assigned repo
- repo worker edits ai-dlc/**
- plan writer edits web/** or backend/**
- verifier/reviewer/explorer writes tracked source
- any role attempts git reset --hard, git clean, git push, git merge, git worktree remove, rm -rf without approved workflow-finish
```

Additionally:

```txt
- unknown mutators are denied by default
- lease validation is based on normalized before/after diff scope, not only command strings
- rename/copy/generated files must still remain within lease scope
- expired leases are denied even if lock files still exist
```

Allow controller read-only commands:

```txt
pwd
ls
find
rg
grep
cat
sed -n
git status
git diff --name-only
git branch --show-current
git rev-parse
ai-dlc inspect
ai-dlc validate
ai-dlc validate-overlay
ai-dlc assignment list
```

Allow controller state commands:

```txt
ai-dlc assignment create
ai-dlc assignment accept
ai-dlc assignment reject
ai-dlc transition
ai-dlc deadlock-check
```

Controller write whitelist:

```txt
- controller may directly create/update runtime files under ../.local/ai-dlc/assignments/**, leases/**, locks/** only through ai-dlc commands
- controller may directly update plan frontmatter state only through ai-dlc transition/deadlock/state commands
- controller may not directly edit tracked `ai-dlc/**`, `workspace.yaml`, `.codex/**`, `web/**`, or `backend/**`
```

### 11.5 PermissionRequest policy

Deny by default:

```txt
git reset --hard
git clean
git push
git merge
git worktree remove
rm -rf
reading .env or secret files
writing outside workspace or ../.local
```

Only `dlc_git_operator` with explicit user approval may proceed with finish-stage Git operations.

### 11.6 PostToolUse policy

After a tool runs, validate:

```txt
- file diffs are within lease scope
- root controller did not create diffs
- embedded paths were not staged in root-system except baseline
- plan/work-items/evidence schemas remain valid
- no evidence-free passing state exists
- no verifier modified tracked source
- no same-repo concurrent writer conflict occurred
```

If invalid, stop continuation and report the exact violation.

### 11.7 Stop policy

Block completion when:

```txt
- active assignment is running/claimed
- assignment report is missing
- evidence is pending while status is verifying/evaluating
- handoff is missing or stale
- active work item lacks next_action
- root-system has unexpected controller-created diffs
- overlay validation fails
- clean-state check has not run before ready_to_finish
- root-system destructive-operation hardening is not active
```

Stop hook auto-continuation must occur at most once per turn. If the same progress signature repeats, transition to `blocked` or `needs_decision` rather than looping.

---

## 12. Git hooks

### 12.1 Root-system pre-commit

Purpose: root-system must not commit embedded subrepo paths except during overlay baseline.

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ "${AI_DLC_ALLOW_OVERLAY_BASELINE:-}" = "1" ]; then
  exit 0
fi

bad_paths="$(git diff --cached --name-only -- web backend || true)"

if [ -n "$bad_paths" ]; then
  echo "AI-DLC: root-system must not commit embedded subrepo paths after overlay baseline."
  echo "$bad_paths"
  echo
  echo "Commit these from the child repositories instead:"
  echo "  git -C web add ... && git -C web commit ..."
  echo "  git -C backend add ... && git -C backend commit ..."
  exit 1
fi

ai-dlc validate --pre-commit --repo root-system
```

### 12.2 Root-system pre-push

Purpose: overlay branches are local-only.

```bash
#!/usr/bin/env bash
set -euo pipefail

overlay_file="ai-dlc/overlay/$(ai-dlc workspace-id).yaml"

if [ -f "$overlay_file" ]; then
  echo "AI-DLC: root-system overlay branch is local-only and must not be pushed."
  echo "Use ai-dlc root-export to export root-only state."
  exit 1
fi
```

### 12.3 Child repo pre-commit

Purpose: child repo commits must be scoped to child repo and valid work item.

Checks:

```txt
- branch matches workspace.yaml
- repo is in target_repos
- active work item exists
- staged paths are within active work item scope or explicitly allowed
- no secret/env files staged
- no root-system files staged
```

Since `web` Git root is `root-system/web`, it cannot stage `root-system/ai-dlc/**` or `backend/**` unless path escape is used. Hook still validates scope.

### 12.4 Child repo pre-push

Checks:

```txt
- required verification is pass or explicitly skipped
- evidence exists
- active assignments are not running
- branch matches issue branch
```

### 12.5 Root-system destructive-operation hardening

`literal_worktree_overlay` mode requires root-level destructive-operation blocking as a mandatory guard, not an optional convenience.

Minimum requirement:

```txt
- root-system `git restore`
- root-system `git checkout -- <embedded path>`
- root-system `git clean`
- root-system `git reset --hard`
```

must be blocked or intercepted for embedded repo paths by one of:

```txt
- required git shim, or
- Orca-side integration that disables the action
```

If neither guard is active, `ai-dlc validate-overlay` must fail and the workspace must not be considered ready.

---

## 13. `ai-dlc` CLI commands

### 13.0 Metadata-bearing commands must be decision-complete

`ai-dlc init-project` and `ai-dlc init-workspace` must accept enough input to generate all required templates without follow-up guessing.

Required initialization inputs:

```txt
--issue LIN-123
--issue-url https://linear.app/acme/issue/LIN-123
--issue-title "reservation validation fix"
--branch LIN-123-reservation-validation
--base-ref origin/main
--root-export-target main
--root-export-remote origin
--repo-base-ref root-system=origin/main
--repo-base-ref web=origin/main
--repo-base-ref backend=origin/main
--workspace-root /abs/path/workspaces/LIN-123
--repo web=/abs/path/repos/web
--repo backend=/abs/path/repos/backend
--repo-url web=git@github.com:acme/web.git
--repo-url backend=git@github.com:acme/backend.git
```

If any of these are omitted, the command must either:

```txt
- derive them deterministically from local state, or
- refuse generation and report the missing metadata
```

### 13.1 Installation and initialization

```txt
ai-dlc install
ai-dlc init-project
ai-dlc init-workspace
ai-dlc overlay-init
ai-dlc validate-overlay
```

Expected future initialization surface:

```txt
ai-dlc init-project \
  --root-system . \
  --repo web=/abs/path/repos/web \
  --repo backend=/abs/path/repos/backend \
  --repo-url web=git@github.com:acme/web.git \
  --repo-url backend=git@github.com:acme/backend.git

ai-dlc init-workspace \
  --issue LIN-123 \
  --issue-url https://linear.app/acme/issue/LIN-123 \
  --issue-title "reservation validation fix" \
  --branch LIN-123-reservation-validation \
  --base-ref origin/main \
  --root-export-target main \
  --root-export-remote origin \
  --repo-base-ref root-system=origin/main \
  --repo-base-ref web=origin/main \
  --repo-base-ref backend=origin/main \
  --workspace-root /abs/path/workspaces/LIN-123 \
  --repo web=/abs/path/repos/web \
  --repo backend=/abs/path/repos/backend
```

### 13.2 State management

```txt
ai-dlc inspect
ai-dlc validate
ai-dlc transition --to <status>
ai-dlc deadlock-check
ai-dlc clean-state-check
```

### 13.3 Work items and evidence

```txt
ai-dlc work-item activate <id>
ai-dlc work-item block <id>
ai-dlc work-item cancel <id>
ai-dlc verify-gate <id>
ai-dlc invalidate <id>
ai-dlc evidence record
```

### 13.4 Assignments and subagents

```txt
ai-dlc assignment create
ai-dlc assignment list
ai-dlc assignment accept
ai-dlc assignment reject
ai-dlc agent-claim --assignment <id>
ai-dlc agent-report --assignment <id>
ai-dlc agent-release --assignment <id>
ai-dlc lock list
ai-dlc lock release
ai-dlc overlay-repair
```

### 13.5 Git and overlay lifecycle

```txt
ai-dlc status --all
ai-dlc diff --all
ai-dlc diff --repo web
ai-dlc root-export
ai-dlc overlay-cleanup
ai-dlc finish
```

### 13.6 `ai-dlc validate-overlay`

Required checks:

```txt
- workspace.yaml exists
- layout.mode = literal_worktree_overlay
- web/.git and backend/.git exist as gitdir pointer files
- git -C web rev-parse --is-inside-work-tree succeeds
- git -C backend rev-parse --is-inside-work-tree succeeds
- root-system tracks web/** and backend/** as normal files
- root-system does not record web/backend as gitlinks/submodules
- overlay baseline commit exists
- root pre-commit and pre-push hooks are installed
- child pre-commit hooks are installed
- root-system branch is marked local-only
- destructive-operation hardening is active
- overlay recovery metadata is present if .git pointers are being moved
```

Gitlink check:

```bash
if git ls-files -s web backend | awk '$1 == "160000" { found=1 } END { exit found ? 0 : 1 }'; then
  echo "Invalid overlay: embedded repos are recorded as gitlinks/submodules."
  exit 1
fi
```

---

## 14. Actual usage flow

### 14.1 Create workspace

```bash
# Orca creates root-system worktree first.
cd workspaces/LIN-123/root-system

ai-dlc init-workspace \
  --issue LIN-123 \
  --issue-url https://linear.app/acme/issue/LIN-123 \
  --issue-title "reservation validation fix" \
  --branch LIN-123-reservation-validation \
  --base-ref origin/main \
  --root-export-target main \
  --root-export-remote origin \
  --repo-base-ref root-system=origin/main \
  --repo-base-ref web=origin/main \
  --repo-base-ref backend=origin/main \
  --workspace-root /abs/path/workspaces/LIN-123 \
  --repo web=~/dev/repos/web \
  --repo backend=~/dev/repos/backend
```

### 14.2 Start Codex from root-system

User prompt:

```txt
$workflow-start ISSUE=LIN-123 REPOS=web,backend

予約作成時のvalidationを修正して。
backendはinvalid inputを422にし、webはそのエラーを表示する。
```

Expected Codex controller behavior:

```txt
1. inspect workspace
2. validate overlay
3. spawn explorers
4. spawn plan/scope agents if needed
5. create repo worker assignments
6. spawn repo workers
7. collect reports
8. spawn verifier
9. spawn evaluator
10. spawn handoff writer
11. reach ready_to_finish / blocked / needs_decision
```

### 14.3 Observe diffs in Orca

Orca root-system Source Control shows real file diffs:

```txt
modified: web/src/reservation/form.tsx
modified: backend/src/reservation/validation.ts
modified: ai-dlc/plans/LIN-123.md
modified: ai-dlc/work-items/LIN-123.yaml
modified: ai-dlc/evidence/LIN-123.yaml
```

Do not use root-system SCM commit for `web/**` or `backend/**`.

### 14.4 Commit child repo changes

Root-system controller does not directly perform child repo commits. Commits happen either:

```txt
- through `dlc_git_operator` under explicit approval, or
- as an out-of-band human operation outside the controller workflow
```

Example git-operator responsibility:

```bash
git -C web status
git -C web add src/reservation/form.tsx
git -C web commit -m "LIN-123: handle reservation validation error"

git -C backend status
git -C backend add src/reservations/validation.ts
git -C backend commit -m "LIN-123: return 422 for invalid reservation input"
```

### 14.5 Export root-system state

Root-system overlay branch must not be merged directly.

```bash
ai-dlc root-export --issue LIN-123
```

Exports only root control-plane paths:

```txt
workspace.yaml
ai-dlc/bootstrap/**
ai-dlc/plans/**
ai-dlc/work-items/**
ai-dlc/decisions/**
ai-dlc/evidence/**
ai-dlc/handoff/**
ai-dlc/quality/**
docs/**
```

Never exports:

```txt
web/**
backend/**
```

### 14.6 Finish and cleanup

```bash
$workflow-finish ISSUE=LIN-123 MODE=summary-only
```

If approved:

```bash
ai-dlc finish --issue LIN-123 --cleanup-worktrees
```

Cleanup checks:

```txt
- child repos committed or explicitly abandoned
- root-export completed or explicitly skipped
- no active assignments
- no expired locks requiring review
- no pending evidence for passing work items
```

---

## 15. Safety notes for Orca

### 15.1 Root-system diff is for review

In Orca, `web/**` and `backend/**` are intentionally shown as root-system diffs. Use this for review.

Do not use root-system commit for these paths.

### 15.2 Discard/Revert risk

If Orca executes a root-system discard/restore on `web/**` or `backend/**`, it can modify the real child repo files.

Git hooks cannot prevent `git restore` because there is no standard pre-restore hook.

Mitigations:

```txt
Required:
  use a git shim or Orca-side block so root-level destructive actions on embedded paths are denied

Additional:
  document root-system SCM as review-only for embedded paths

Optional stronger:
  patch Orca or add an Orca extension to disable destructive actions on embedded paths
```

The dotfiles implementation must include `ai-dlc git-shim install` or an equivalent mandatory hardening mechanism.

---

## 16. Documentation deliverables

### 16.1 Dotfiles repository docs

```txt
docs/
  README.md
  installation.md
  configuration.md
  skills.md
  hooks.md
  subagents.md
  assignment-lease-model.md
  literal-worktree-overlay.md
  git-hooks.md
  troubleshooting.md
  security.md
```

Required contents:

- what AI-DLC is
- why root-system is controller-only
- why subagents are required
- how literal worktree overlay works
- why root-system overlay branch is local-only
- how to install dotfiles
- how to install Codex hooks
- how to install Git hooks
- how to validate overlay
- how to troubleshoot locks, leases, and stale state
- how workspace metadata maps to Linear, branches, canonical repos, and export targets
- how generated templates encode next-agent and next-output decisions
- which files are root-system tracked outputs vs ../.local runtime outputs
- how controller write whitelist and git-operator boundaries work

### 16.2 Project-level docs

```txt
root-system/
  AGENTS.md
  docs/
    ai-dlc-project-setup.md
    ai-dlc-usage.md
    ai-dlc-finish.md
```

Keep these short and project-specific.

Do not duplicate generic workflow rules in project docs.

### 16.3 User quickstart

```md
# AI-DLC Quickstart

1. Create root-system worktree in Orca.
2. Run `ai-dlc init-workspace`.
3. Start Codex from root-system.
4. Use `$workflow-start`.
5. Review root-system diff in Orca.
6. Commit source changes from child repos only.
7. Run `$workflow-finish`.
```

---

## 17. Testing plan

### 17.1 Overlay tests

```txt
- init-workspace creates web/backend literal worktrees
- root-system git status shows embedded file changes
- child repo git status shows same changes relative to child root
- root-system does not record embedded repos as gitlinks
- root pre-commit blocks embedded paths
- root pre-push blocks overlay branch
- child repo commit does not include root files
- overlay baseline interruption still restores child `.git` pointers or can be repaired deterministically
```

### 17.2 Subagent enforcement tests

```txt
- controller apply_patch is denied
- controller write-like Bash is denied
- unclaimed repo worker edit is denied
- expired lease edit is denied
- repo worker cannot edit another repo
- repo worker cannot edit ai-dlc/**
- verifier cannot modify tracked source
- same-repo double claim races fail atomically
- Stop hook blocks missing assignment report
- Stop hook blocks missing handoff
- Stop hook does not auto-continue more than once
```

### 17.3 Workflow tests

```txt
- $workflow-start delegates rather than edits
- plan writer creates valid plan
- scope manager creates valid work-items
- repo worker edits only lease paths
- verifier records evidence
- evaluator rejects evidence-free completion
- verify-gate is the only command that marks passing
- finish exports root-only state
- finish fails if verified HEAD/tree no longer matches current repo state
```

### 17.4 Orca behavior tests

```txt
- root-system Source Control displays web/src/*.ts as normal file diffs
- syntax is preserved in diff view
- root-system commit of web/** is blocked
- child repo commit succeeds
- root-system discard/restore/reset/clean on embedded paths is blocked or strongly intercepted
```

---

## 18. Implementation phases

### Phase 0: Dotfiles base

Deliver:

```txt
- user config
- user AGENTS.md
- hooks.json
- ai-dlc CLI skeleton
- custom agent files
- skill skeletons
```

Acceptance:

```txt
- `ai-dlc self-test` passes
- Codex hooks load
- `$workflow-start` is discoverable
```

### Phase 1: Literal worktree overlay

Deliver:

```txt
- ai-dlc init-workspace
- ai-dlc overlay-init
- ai-dlc validate-overlay
- baseline tracking implementation
- root Git hooks
- child Git hooks
```

Acceptance:

```txt
- Orca root-system diff shows child source file diffs
- child repos can commit normally
- root-system cannot commit embedded paths after baseline
```

### Phase 2: AI-DLC state files

Deliver:

```txt
- workspace.yaml
- overlay yaml
- bootstrap yaml
- plan md
- work-items yaml
- evidence yaml
- handoff md
- schemas
```

Acceptance:

```txt
- ai-dlc validate passes
- invalid state transitions fail
- WIP=1 is enforced
```

### Phase 3: Subagent assignments and leases

Deliver:

```txt
- assignment create/list/accept/reject
- agent-claim/report/release
- lock management
- lease validator
```

Acceptance:

```txt
- write requires valid lease
- same repo concurrent writer is blocked
- controller cannot directly write
```

### Phase 4: Hooks enforcement

Deliver:

```txt
- SessionStart controller injection
- UserPromptSubmit workflow detection
- PreToolUse lease gate
- PermissionRequest danger gate
- PostToolUse side-effect validator
- Stop completion gate
```

Acceptance:

```txt
- direct controller edits are denied
- missing reports block stop
- stale/incomplete state cannot finish silently
```

### Phase 5: Verification and evaluator

Deliver:

```txt
- dlc_verifier
- dlc_evaluator
- evidence recording
- verify-gate
- clean-state-check
```

Acceptance:

```txt
- worker cannot mark passing
- evidence-free passing is invalid
- evaluator can force return to executing/verifying
```

### Phase 6: Finish lifecycle

Deliver:

```txt
- root-export
- child repo commit/push support through git operator
- overlay-cleanup
- finish summary
```

Acceptance:

```txt
- root-system main receives only root control-plane files
- web/backend changes remain in child repos only
- overlay branch is removed or left explicitly local-only
```

### Phase 7: Optional plugin packaging

Deliver:

```txt
- codex-ai-dlc plugin containing skills and references
- marketplace metadata
```

Acceptance:

```txt
- plugin installs skills
- dotfiles remain source of enforcement for hooks/CLI
```

### Phase 8: Required Orca hardening

Deliver one of:

```txt
- git shim that blocks root discard/restore/clean on embedded paths
- Orca extension/patch to mark embedded paths as review-only in root-system SCM
```

Acceptance:

```txt
- root-system destructive operations on embedded paths are blocked
```

---

## 19. Codex CLI implementation prompt

Use this when handing the plan to Codex CLI:

```txt
Implement AI-DLC literal worktree overlay v0.3.

Read this document fully.

Priorities:
1. Implement dotfiles AI-DLC CLI skeleton.
2. Implement literal worktree overlay initialization.
3. Implement validate-overlay.
4. Implement root/child Git hooks.
5. Implement controller-only/subagent-first enforcement through hooks.
6. Implement assignment and lease model.
7. Implement $workflow-start skill so the root-system session delegates all substantive work to subagents.

Non-negotiable constraints:
- No changeview patch projection.
- No double-write artifacts for diffs.
- root-system diff must show embedded child source files directly.
- root-system session must not perform direct implementation.
- Source edits require subagent assignment and lease.
- web/backend commits must happen from child repos only.
- root-system overlay branch must be local-only.

Deliver code plus tests for each phase.
```

---

## 20. Final acceptance criteria

The implementation is accepted only if all are true:

```txt
1. Orca opened at root-system shows web/backend source file diffs as normal nested files.
2. Those files preserve their real extensions and syntax.
3. No patch/stat/changeview projection exists.
4. AI edits each source file only once.
5. web/backend are real Git worktrees and can commit normally.
6. web/backend commits do not include root-system files.
7. root-system cannot commit embedded paths after baseline.
8. root-system cannot push overlay branch.
9. root-system Codex session acts as controller-only.
10. Direct controller edits are blocked by hooks.
11. Source edits require subagent assignment and lease.
12. Repo workers cannot edit outside assigned repo/path scope.
13. Verifier/evaluator are separate from repo worker.
14. Passing state requires verification evidence and verify-gate.
15. Finish exports only root control-plane state, never embedded child source snapshots.
16. Root-system destructive operations on embedded paths are blocked by mandatory hardening.
17. Verified evidence is tied to repo branch/HEAD/clean state and finish refuses drift.
```
