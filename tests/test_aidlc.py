from __future__ import annotations

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
from aidlc.git_hooks import install_project_hooks
from aidlc.overlay import overlay_init, overlay_repair, root_export, validate_overlay
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
from aidlc.workspace import init_project, scaffold_workspace


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

    def dispatch_with_payload(self, root: Path, payload: dict, extra_env: dict[str, str] | None = None) -> dict[str, str]:
        raw = json.dumps(payload)
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        with patch("builtins.input", return_value=raw), patch.dict(os.environ, env, clear=True):
            return hooks.dispatch(root)

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
        transition(root, "plan_ready")
        work_item_activate(root, "WI-001")

    def test_init_project_creates_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root-system"
            root.mkdir()
            init_project(root, repo_paths={"web": "/tmp/web"}, repo_urls={"web": "git@example.com:web.git"})
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / ".codex" / "config.toml").exists())
            self.assertTrue((root / "ai-dlc" / ".gitkeep").exists())
            self.assertTrue((root / "ai-dlc" / "project-metadata.yaml").exists())

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

            self.prepare_active_web_item(root)
            self.assertEqual(validate(root), [])
            state = bootstrap(root)
            self.assertEqual(state["status"], "ready")

            created = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            listed = assignment_list(root)
            self.assertEqual(created["id"], listed[0]["id"])
            self.assertEqual(created["workspace_id"], "LIN-123")
            self.assertEqual(created["branch"]["issue"], "LIN-123-branch")

            plan_assignment = assignment_create(root, "dlc_plan_writer", None, [], None)
            self.assertIn("ai-dlc/plans/**", plan_assignment["writable"])
            self.assertNotIn("ai-dlc/**", plan_assignment["forbidden"])
            self.assertEqual(plan_assignment["lock_scope"], "plan.lock")

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

    def test_hook_dispatch_blocks_without_claim_and_allows_claimed_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.create_workspace(Path(tmp))
            self.prepare_active_web_item(root)
            bootstrap(root)

            payload = {"tool_name": "Edit", "tool_input": {"file_path": str(root / "web" / "README.md")}}
            blocked = self.dispatch_with_payload(root, payload)
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("claimed lease", blocked["reason"])

            assignment = assignment_create(root, "dlc_repo_worker", "web", ["web/README.md"], "WI-001")
            lease = agent_claim(root, assignment["id"], session_id="sess-web")
            allowed = self.dispatch_with_payload(root, payload, {"CODEX_SESSION_ID": lease["session_id"]})
            self.assertEqual(allowed["decision"], "allow")

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
            self.assertIn("Workspace:", output["additionalContext"])

    def test_hook_dispatch_non_workspace_pret_tool_and_stop_are_schema_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp)

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
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            blocked_edit = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": str(repo / "README.md")}},
            )
            self.assertEqual(blocked_edit["decision"], "block")
            self.assertIn("delegate to a subagent", blocked_edit["reason"])

            blocked_bash = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "mkdir -p scratch"}},
            )
            self.assertEqual(blocked_bash["decision"], "block")
            self.assertIn("mutating Bash", blocked_bash["reason"])

            allowed_bash = self.dispatch_with_payload(
                repo,
                {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"cmd": "git status --short"}},
            )
            self.assertEqual(allowed_bash, {})

    def test_hook_dispatch_non_workspace_context_mentions_controller_only_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            codex_dir = repo / ".codex"
            codex_dir.mkdir()
            (codex_dir / "config.toml").write_text("[guardrails]\nsubagent_required = true\n", encoding="utf-8")

            result = self.dispatch_with_payload(repo, {"hook_event_name": "SessionStart"})
            output = result["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "SessionStart")
            self.assertIn("Controller-only repo", output["additionalContext"])

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

            allowed = self.dispatch_with_payload(root, {"tool_name": "spawn_agent", "tool_input": {"agent": "dlc_scope_manager"}})
            self.assertEqual(allowed["decision"], "allow")

            decisions = root / "ai-dlc" / "decisions" / "LIN-123.md"
            decisions.write_text(decisions.read_text(encoding="utf-8") + "\n- allow-next-agent: dlc_verifier\n", encoding="utf-8")
            override = self.dispatch_with_payload(root, {"tool_name": "spawn_agent", "tool_input": {"agent": "dlc_verifier"}})
            self.assertEqual(override["decision"], "allow")

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
