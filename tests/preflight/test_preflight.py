"""Black-box regression tests for templates/tooling-preflight.sh.

Each test builds a throwaway project directory plus a stub `bin/` that is put
first on PATH, so results never depend on what is installed on the host.

Run:  python3 -m unittest discover -s tests/preflight -v
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.environ.get("AAO_PREFLIGHT_SCRIPT") or os.path.join(REPO, "templates", "tooling-preflight.sh")
TEMPLATE_AUTH = os.path.join(REPO, "templates", "agent-auth.example.yaml")
BASH = shutil.which("bash") or "/bin/bash"

ANDROID_STUB = """\
#!/bin/sh
case "$1 $2" in
  "--help "*)      echo "commands: docs search fetch screen capture layout run" ;;
  "studio --help") echo "version-lookup render-compose-preview analyze-file" ;;
  "info "*)        echo "android info v1" ;;
  "skills list")   echo "skill-a"; echo "skill-b" ;;
esac
"""

GIT_STUB = """\
#!/bin/sh
case "$1 $2" in
  "rev-parse --is-inside-work-tree") echo "true"; exit 0 ;;
  "rev-parse HEAD")                  echo "fixturehead"; exit 0 ;;
esac
exit 1
"""

# Inside a work tree, but HEAD cannot be resolved (e.g. repo without commits).
GIT_NO_HEAD_STUB = """\
#!/bin/sh
case "$1 $2" in
  "rev-parse --is-inside-work-tree") echo "true"; exit 0 ;;
esac
exit 128
"""

GIT_FAIL_STUB = "#!/bin/sh\nexit 128\n"

# Bare repository: HEAD resolves, but there is no work tree.
GIT_BARE_STUB = """\
#!/bin/sh
case "$1 $2" in
  "rev-parse --is-inside-work-tree") echo "false"; exit 0 ;;
  "rev-parse HEAD")                  echo "fixturehead"; exit 0 ;;
esac
exit 1
"""


class Fixture:
    """A temp project + stub bin directory."""

    def __init__(self, with_python3=True, git=GIT_STUB, system_path=True):
        self.root = tempfile.mkdtemp(prefix="aao-preflight-")
        self.bin = os.path.join(self.root, "bin")
        self.proj = os.path.join(self.root, "proj")
        os.makedirs(self.bin)
        os.makedirs(self.proj)
        self.extra_env = {}
        if with_python3:
            self.stub("python3", f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
        if git is not None:
            self.stub("git", git)
        # /usr/bin:/bin give coreutils but on macOS also git/python3 — the stubs
        # above shadow those. Tests that need "no python3" pass system_path=False.
        self.path = self.bin + (":/usr/bin:/bin" if system_path else "")

    def stub(self, name, body):
        p = os.path.join(self.bin, name)
        with open(p, "w") as f:
            f.write(body)
        os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def write(self, rel, content):
        p = os.path.join(self.proj, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)

    def write_bytes(self, rel, content):
        p = os.path.join(self.proj, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(content)

    def copy_template_auth(self, transform=None):
        with open(TEMPLATE_AUTH) as f:
            content = f.read()
        self.write(".agent-auth.yaml", transform(content) if transform else content)

    def run(self, *args):
        env = {"PATH": self.path, "HOME": self.root, "LANG": "C.UTF-8"}
        env.update(self.extra_env)
        return subprocess.run([BASH, SCRIPT, *args], cwd=self.proj, env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)

    def json(self, *args):
        r = self.run("--json", *args)
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)

    def markdown(self, *args):
        r = self.run(*args)
        assert r.returncode == 0, r.stderr
        return r.stdout

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


class Base(unittest.TestCase):
    def fixture(self, **kw):
        fx = Fixture(**kw)
        self.addCleanup(fx.cleanup)
        return fx


# ── Auth token detection (AOO-012a regression) ───────────────────────────────

class AuthTokenTests(Base):
    def assert_tokens(self, fx, atlassian, figma, github):
        t = fx.json()["tools"]
        self.assertEqual((t["atlassian_token"], t["figma_token"], t["github_token"]),
                         (atlassian, figma, github))
        md = fx.markdown()
        self.assertIn(f"- atlassian.api_token: {atlassian}", md)
        self.assertIn(f"- figma.personal_access_token: {figma}", md)
        self.assertIn(f"- github.personal_access_token: {github}", md)

    def test_empty_template_reports_all_empty(self):
        fx = self.fixture()
        fx.copy_template_auth()
        self.assert_tokens(fx, "empty", "empty", "empty")

    def test_github_only_does_not_mark_figma_set(self):
        fx = self.fixture()
        fx.write(".agent-auth.yaml", textwrap.dedent("""\
            atlassian:
              api_token: ""
            figma:
              personal_access_token: ""
            github:
              personal_access_token: "ghp_fake"
            """))
        self.assert_tokens(fx, "empty", "empty", "set")

    def test_real_value_with_inline_comment_is_set(self):
        fx = self.fixture()
        fx.copy_template_auth(lambda c: c.replace('api_token: ""', 'api_token: "fake-123"', 1))
        self.assert_tokens(fx, "set", "empty", "empty")

    def test_commented_out_value_is_ignored(self):
        fx = self.fixture()
        fx.write(".agent-auth.yaml", textwrap.dedent("""\
            atlassian:
              api_token: ""
            # api_token: "should-not-count"
            #   personal_access_token: "nope"
            figma:
              personal_access_token: ""
            """))
        self.assert_tokens(fx, "empty", "empty", "missing_key")

    def test_missing_auth_file(self):
        fx = self.fixture()
        data = fx.json()
        self.assertEqual(data["tools"]["auth_file"], "missing")
        self.assertEqual(data["tools"]["atlassian_token"], "unknown")
        self.assertIn("auth_file_missing", data["non_blocking_gaps"])
        self.assertIn("- .agent-auth.yaml: missing", fx.markdown())

    def test_token_values_never_printed(self):
        fx = self.fixture()
        fx.copy_template_auth(lambda c: c.replace('api_token: ""', 'api_token: "SECRET-XYZ"', 1))
        for args in (("--json",), ()):
            r = fx.run(*args)
            self.assertNotIn("SECRET-XYZ", r.stdout)
            self.assertNotIn("SECRET-XYZ", r.stderr)

    def test_secret_not_leaked_when_auth_file_is_not_utf8(self):
        """Decode failure must not dump the file (or a traceback quoting it)."""
        fx = self.fixture()
        fx.write_bytes(".agent-auth.yaml", b'atlassian:\n  api_token: "SECRET-XYZ\xff\xfe"\n')
        for args in (("--json",), ()):
            r = fx.run(*args)
            self.assertNotIn("SECRET-XYZ", r.stdout + r.stderr)
            self.assertNotIn("Traceback", r.stderr)

    def test_non_utf8_auth_file_is_unreadable_and_other_checks_survive(self):
        fx = self.fixture()
        fx.write_bytes(".agent-auth.yaml", b"atlassian:\n  api_token: \"\xff\xfe\"\n")
        fx.write(".project-orchestration/tasks/T-9/session.json",
                 json.dumps({"stage_reached": 3, "stage_status": "in_progress", "task_id": "T-9"}))
        data = fx.json()
        self.assertEqual(data["tools"]["auth_file"], "unreadable")
        self.assertEqual(data["tools"]["atlassian_token"], "unknown")
        self.assertIn("auth_file_unreadable", data["non_blocking_gaps"])
        self.assertEqual(data["session"]["in_progress"], ["T-9"])
        self.assertEqual(data["tools"]["android_cli"], "missing")
        md = fx.markdown()
        self.assertIn("- .agent-auth.yaml: unreadable", md)
        self.assertIn("- atlassian.api_token: unknown", md)
        self.assertIn("  - T-9: stage 3, in_progress", md)
        self.assertIn("## Android CLI", md)


# ── Android CLI discovery ────────────────────────────────────────────────────

class AndroidCliTests(Base):
    def test_cli_missing(self):
        fx = self.fixture()
        t = fx.json()["tools"]
        self.assertEqual(t["android_cli"], "missing")
        self.assertEqual(t["android_commands"]["docs_search"], "missing")
        self.assertIn("- android CLI: missing", fx.markdown())

    def test_non_utf8_command_output_does_not_crash(self):
        fx = self.fixture()
        fx.stub("android", ANDROID_STUB.replace(
            'echo "commands: docs search fetch screen capture layout run"',
            "printf 'commands: docs search fetch screen capture layout run \\377\\376\\n'"))
        data = fx.json()
        self.assertEqual(data["tools"]["android_commands"]["docs_search"], "supported")
        self.assertIn("  - android docs search: supported", fx.markdown())

    def test_cli_present_discovers_commands(self):
        fx = self.fixture()
        fx.stub("android", ANDROID_STUB)
        fx.stub("adb", "#!/bin/sh\n")
        t = fx.json()["tools"]
        self.assertEqual(t["android_cli"], "present")
        self.assertEqual(t["adb"], "present")
        self.assertEqual(t["android_commands"]["docs_search"], "supported")
        self.assertEqual(t["android_studio_commands"]["analyze_file"], "supported")
        self.assertEqual(t["android_studio_commands"]["find_usages"], "missing")
        md = fx.markdown()
        self.assertIn("  - android docs search: supported", md)
        self.assertIn("  - android studio find-usages: missing", md)
        self.assertIn("  skill-a", md)


# ── Graphify package detection (AOO-024) ─────────────────────────────────────

class GraphifyTests(Base):
    def test_package_detected_without_python_binary(self):
        """Host has only python3 (no `python`), package must still be found."""
        fx = self.fixture(system_path=False)
        for tool in ("sh", "cat"):
            src = shutil.which(tool)
            if src:
                os.symlink(src, os.path.join(fx.bin, tool))
        site = os.path.join(fx.root, "site")
        dist = os.path.join(site, "graphifyy-1.2.3.dist-info")
        os.makedirs(dist)
        with open(os.path.join(dist, "METADATA"), "w") as f:
            f.write("Metadata-Version: 2.1\nName: graphifyy\nVersion: 1.2.3\n")
        fx.extra_env["PYTHONPATH"] = site
        self.assertIsNone(shutil.which("python", path=fx.path))
        self.assertEqual(fx.json()["tools"]["graphify_package"], "present")
        self.assertIn("- graphifyy package: present (v1.2.3)", fx.markdown())

    def test_graph_report_selects_graphify(self):
        fx = self.fixture()
        fx.write("graphify-out/GRAPH_REPORT.md", "")
        self.assertEqual(fx.json()["architecture_map"]["active_tool"], "graphify")


# ── Cache reuse (AOO-018) ────────────────────────────────────────────────────

class CacheTests(Base):
    """Cache is reusable only with a valid TTL AND a readable HEAD AND
    graph_commit == HEAD. Every other case must say cache_reusable: false."""

    def write_cache(self, fx, **fields):
        fx.write(".project-orchestration/memory/tooling-cache.json", json.dumps(fields))

    def assert_cache(self, fx, status, reusable):
        cache = fx.json()["cache"]
        self.assertEqual((cache["cache_status"], cache["cache_reusable"]), (status, reusable))
        md = fx.markdown()
        self.assertIn(f"- cache_status: {status}", md)
        self.assertIn(f"- cache_reusable: {str(reusable).lower()}", md)

    def test_fresh_and_matching_is_reusable(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="2099-01-01T00:00:00Z", graph_commit="fixturehead")
        self.assert_cache(fx, "fresh", True)

    def test_expired(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="2000-01-01T00:00:00Z", graph_commit="fixturehead")
        self.assert_cache(fx, "stale", False)

    def test_commit_mismatch(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="2099-01-01T00:00:00Z", graph_commit="other")
        self.assert_cache(fx, "graph_stale", False)

    def test_missing_graph_commit(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="2099-01-01T00:00:00Z")
        self.assert_cache(fx, "no_commit", False)

    def test_empty_graph_commit(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="2099-01-01T00:00:00Z", graph_commit="")
        self.assert_cache(fx, "no_commit", False)

    def test_head_unavailable(self):
        fx = self.fixture(git=GIT_NO_HEAD_STUB)
        self.write_cache(fx, valid_until="2099-01-01T00:00:00Z", graph_commit="fixturehead")
        self.assert_cache(fx, "head_unavailable", False)

    def test_git_missing(self):
        fx = self.fixture(git=GIT_FAIL_STUB)
        self.write_cache(fx, valid_until="2099-01-01T00:00:00Z", graph_commit="fixturehead")
        self.assert_cache(fx, "head_unavailable", False)

    def test_unparseable_ttl(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="next tuesday", graph_commit="fixturehead")
        self.assert_cache(fx, "unparseable", False)

    def test_missing_ttl(self):
        fx = self.fixture()
        self.write_cache(fx, graph_commit="fixturehead")
        self.assert_cache(fx, "unknown", False)

    def test_unreadable(self):
        fx = self.fixture()
        fx.write(".project-orchestration/memory/tooling-cache.json", "{not json")
        cache = fx.json()["cache"]
        self.assertFalse(cache["readable"])
        self.assertFalse(cache["cache_reusable"])
        self.assertIn("- cache: unreadable", fx.markdown())

    def test_missing(self):
        fx = self.fixture()
        cache = fx.json()["cache"]
        self.assertFalse(cache["present"])
        self.assertFalse(cache["cache_reusable"])
        self.assertIn("- tooling-cache.json: missing", fx.markdown())


class FinalReadinessAuthorityTests(Base):
    """The script never emits the final gate: only preflight.md carries
    ready_for_stage_0 (= tooling_ready AND task-level rules, written by the agent)."""

    def test_script_does_not_emit_final_gate(self):
        fx = self.fixture()
        data = fx.json()
        self.assertNotIn("ready_for_stage_0", data)
        md = fx.markdown()
        self.assertNotRegex(md, r"`ready_for_stage_0`: (true|false)")
        self.assertIn("decided by the agent in preflight.md", md)

    def test_docs_name_preflight_md_as_the_only_gate(self):
        with open(os.path.join(REPO, "refs", "contracts-and-artifacts.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("Prefer `preflight.json` over `preflight.md` for any boolean gate", text)
        self.assertIn("only Stage 0 gate", text)


class BareRepoCacheTests(Base):
    """A bare repo has a HEAD but no work tree: cache must not be reusable,
    in the fast path and in the full run alike."""

    def write_matching_cache(self, fx):
        fx.write(".project-orchestration/memory/tooling-cache.json",
                 json.dumps({"valid_until": "2099-01-01T00:00:00Z", "graph_commit": "fixturehead"}))

    def test_cache_check_refuses_reuse_without_work_tree(self):
        fx = self.fixture(git=GIT_BARE_STUB)
        self.write_matching_cache(fx)
        cache = json.loads(fx.run("--cache-check").stdout)["cache"]
        self.assertEqual((cache["cache_status"], cache["cache_reusable"]), ("not_a_git_work_tree", False))
        full = fx.json()
        self.assertFalse(full["cache"]["cache_reusable"])
        self.assertIn("not_a_git_work_tree", full["blocking_gaps"])

    @unittest.skipUnless(shutil.which("git"), "real git required")
    def test_real_bare_repository(self):
        fx = self.fixture(git=None)          # use the host git
        git = shutil.which("git")
        src = os.path.join(fx.root, "src")
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        for cmd in (["init", "-q", src], ["-C", src, "commit", "-q", "--allow-empty", "-m", "c"]):
            subprocess.run([git, *cmd], check=True, env=env, capture_output=True)
        shutil.rmtree(fx.proj)
        subprocess.run([git, "clone", "-q", "--bare", src, fx.proj], check=True, capture_output=True)
        head = subprocess.run([git, "-C", fx.proj, "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
        fx.write(".project-orchestration/memory/tooling-cache.json",
                 json.dumps({"valid_until": "2099-01-01T00:00:00Z", "graph_commit": head}))
        fx.path = fx.bin + ":" + os.path.dirname(git) + ":/usr/bin:/bin"
        cache = json.loads(fx.run("--cache-check").stdout)["cache"]
        self.assertFalse(cache["cache_reusable"])
        self.assertEqual(cache["cache_status"], "not_a_git_work_tree")


class CacheCheckModeTests(Base):
    """--cache-check: cache verdict only, without probing Android tooling."""

    def test_cache_check_only_reports_cache_and_git(self):
        fx = self.fixture()
        fx.stub("android", "#!/bin/sh\necho called >> \"$HOME/android-calls\"\n")
        fx.write(".project-orchestration/memory/tooling-cache.json",
                 json.dumps({"valid_until": "2099-01-01T00:00:00Z", "graph_commit": "fixturehead"}))
        r = fx.run("--cache-check")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(set(data), {"timestamp", "cache"})
        self.assertTrue(data["cache"]["cache_reusable"])
        self.assertFalse(os.path.exists(os.path.join(fx.root, "android-calls")))

    def test_cache_check_not_reusable(self):
        fx = self.fixture()
        r = fx.run("--cache-check")
        self.assertFalse(json.loads(r.stdout)["cache"]["cache_reusable"])


# ── Task sessions (AOO-019) ──────────────────────────────────────────────────

class SessionTests(Base):
    def write_session(self, fx, task_id, **fields):
        fx.write(f".project-orchestration/tasks/{task_id}/session.json",
                 json.dumps({"task_id": task_id, **fields}))

    def test_single_task_at_canonical_path(self):
        fx = self.fixture()
        self.write_session(fx, "A-1", stage_reached=4, stage_status="in_progress")
        session = fx.json()["session"]
        self.assertEqual(session["tasks"], [
            {"task_id": "A-1", "stage_reached": 4, "stage_status": "in_progress"}])
        self.assertEqual(session["in_progress"], ["A-1"])
        md = fx.markdown()
        self.assertIn("- task sessions: 1 (in_progress: A-1)", md)
        self.assertIn("  - A-1: stage 4, in_progress", md)

    def test_multiple_in_progress_lists_all_and_never_picks(self):
        fx = self.fixture()
        self.write_session(fx, "A-1", stage_reached=2, stage_status="in_progress")
        self.write_session(fx, "B-2", stage_reached=5, stage_status="in_progress")
        self.write_session(fx, "C-3", stage_reached=7, stage_status="complete")
        data = fx.json()
        self.assertEqual(data["session"]["in_progress"], ["A-1", "B-2"])
        self.assertNotIn("resume", data["session"])
        self.assertIn("multiple_in_progress_sessions", data["non_blocking_gaps"])
        self.assertIn("- task sessions: 3 (in_progress: A-1, B-2)", fx.markdown())

    def test_legacy_session_is_reported_not_used(self):
        fx = self.fixture()
        fx.write(".project-orchestration/memory/session.json",
                 json.dumps({"task_id": "OLD-1", "stage_reached": 3, "stage_status": "in_progress"}))
        data = fx.json()
        self.assertEqual(data["session"]["tasks"], [])
        self.assertEqual(data["session"]["legacy"]["task_id"], "OLD-1")
        self.assertIn("legacy_session_path", data["non_blocking_gaps"])
        self.assertIn("- legacy memory/session.json: present (task OLD-1, stage 3, in_progress)",
                      fx.markdown())

    def test_unreadable_session_is_listed(self):
        fx = self.fixture()
        fx.write(".project-orchestration/tasks/X-9/session.json", "{broken")
        data = fx.json()
        self.assertEqual(data["session"]["tasks"], [{"task_id": "X-9", "readable": False}])
        self.assertIn("session_unreadable:X-9", data["non_blocking_gaps"])


# ── Readiness (AOO-022) ──────────────────────────────────────────────────────

class ReadinessTests(Base):
    def test_ready_in_git_work_tree(self):
        fx = self.fixture()
        data = fx.json()
        self.assertTrue(data["tooling_ready"])
        self.assertIn("- tooling_ready: true", fx.markdown())

    def test_not_ready_outside_git_work_tree(self):
        fx = self.fixture(git=GIT_FAIL_STUB)
        data = fx.json()
        self.assertFalse(data["tooling_ready"])
        self.assertIn("not_a_git_work_tree", data["blocking_gaps"])
        md = fx.markdown()
        self.assertIn("- tooling_ready: false", md)
        self.assertIn("- Blocking gaps: not_a_git_work_tree", md)

    def test_non_blocking_gaps_do_not_block(self):
        fx = self.fixture()  # no auth file, no android, no karpathy
        data = fx.json()
        self.assertTrue(data["tooling_ready"])
        self.assertIn("auth_file_missing", data["non_blocking_gaps"])


# ── Output contract & parity (AOO-023) ───────────────────────────────────────

class OutputContractTests(Base):
    def full_fixture(self):
        fx = self.fixture()
        fx.stub("android", ANDROID_STUB)
        fx.copy_template_auth()
        fx.write("CLAUDE.md", "karpathy rules\n")
        fx.write(".project-orchestration/memory/tooling-cache.json",
                 json.dumps({"valid_until": "2099-01-01T00:00:00Z", "graph_commit": "other"}))
        fx.write(".project-orchestration/tasks/T-1/session.json",
                 json.dumps({"stage_reached": 2, "stage_status": "in_progress", "task_id": "T-1"}))
        return fx

    def test_json_keeps_backward_compatible_keys(self):
        data = self.full_fixture().json()
        for key in ("timestamp", "mode", "tooling_ready", "blocking_gaps",
                    "non_blocking_gaps", "tools", "architecture_map", "cache"):
            self.assertIn(key, data)
        for key in ("auth_file", "atlassian_token", "figma_token", "github_token",
                    "android_cli", "adb", "android_commands", "android_studio_commands",
                    "understand_anything", "graphify_cli", "graphify_package", "karpathy"):
            self.assertIn(key, data["tools"])

    def test_markdown_keeps_sections(self):
        md = self.full_fixture().markdown()
        for section in ("# Tooling Preflight", "## Mode", "## Timestamp", "## Working directory",
                        "## Summary",
                        "## Auth", "## Android CLI", "## Android skills", "## Understand-Anything",
                        "## Graphify", "## Karpathy", "## Memory cache", "## Decision reminder"):
            self.assertIn(section, md)

    def test_both_formats_report_same_facts(self):
        fx = self.full_fixture()
        data = fx.json()
        md = fx.markdown()
        self.assertEqual(data["tools"]["karpathy"], "installed")
        self.assertIn("- Karpathy: installed", md)
        self.assertEqual(data["cache"]["cache_status"], "graph_stale")
        self.assertIn("- cache_status: graph_stale", md)
        self.assertEqual(data["session"]["in_progress"], ["T-1"])
        self.assertIn("  - T-1: stage 2, in_progress", md)
        self.assertEqual(data["cache"]["cache_reusable"], False)
        self.assertIn("- cache_reusable: false", md)
        self.assertIn(f"- tooling_ready: {str(data['tooling_ready']).lower()}", md)
        # active_tool depends on whether the host interpreter has graphifyy;
        # only parity between formats is asserted here.
        active = data["architecture_map"]["active_tool"]
        self.assertIn(f"- active architecture-map tool: {active}", md)
        for token_key, label in (("atlassian_token", "atlassian.api_token"),
                                 ("figma_token", "figma.personal_access_token"),
                                 ("github_token", "github.personal_access_token")):
            self.assertIn(f"- {label}: {data['tools'][token_key]}", md)
        names = {"docs_search": "android docs search", "layout": "android layout",
                 "run": "android run"}
        for key, name in names.items():
            self.assertIn(f"  - {name}: {data['tools']['android_commands'][key]}", md)
        studio = {"analyze_file": "android studio analyze-file",
                  "find_usages": "android studio find-usages"}
        for key, name in studio.items():
            self.assertIn(f"  - {name}: {data['tools']['android_studio_commands'][key]}", md)

    def test_parity_for_missing_states(self):
        fx = self.fixture()
        data, md = fx.json(), fx.markdown()
        self.assertEqual(data["tools"]["auth_file"], "missing")
        self.assertIn("- .agent-auth.yaml: missing", md)
        self.assertFalse(data["cache"]["present"])
        self.assertIn("- tooling-cache.json: missing", md)
        self.assertEqual(data["session"]["tasks"], [])
        self.assertIn("- task sessions: none", md)
        self.assertEqual(data["tools"]["android_cli"], "missing")
        self.assertIn("- android CLI: missing", md)

    def test_parity_for_unreadable_states(self):
        fx = self.fixture()
        fx.write_bytes(".agent-auth.yaml", b"\xff\xfe")
        fx.write(".project-orchestration/memory/tooling-cache.json", "{bad")
        fx.write(".project-orchestration/tasks/T-2/session.json", "[1, 2]")
        data, md = fx.json(), fx.markdown()
        self.assertEqual(data["tools"]["auth_file"], "unreadable")
        self.assertIn("- .agent-auth.yaml: unreadable", md)
        self.assertFalse(data["cache"]["readable"])
        self.assertIn("- cache: unreadable", md)
        self.assertEqual(data["session"]["tasks"], [{"task_id": "T-2", "readable": False}])
        self.assertIn("  - T-2: unreadable", md)

    def test_non_ascii_working_directory_with_c_locale(self):
        fx = self.fixture()
        target = os.path.join(fx.root, "dự-án")
        os.rename(fx.proj, target)
        fx.proj = target
        fx.extra_env.update({"LANG": "C", "LC_ALL": "C"})
        for args in (("--json",), ()):
            r = fx.run(*args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("dự-án", fx.markdown())

    def test_mode_argument(self):
        fx = self.fixture()
        self.assertEqual(fx.json("bootstrap")["mode"], "bootstrap")
        self.assertIn("## Mode\nbootstrap", fx.markdown("bootstrap"))

    def test_python3_missing_fails_clearly(self):
        fx = self.fixture(with_python3=False, system_path=False)
        r = fx.run("--json")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("python3", r.stderr)


if __name__ == "__main__":
    unittest.main()


# ── Check isolation (in-process; a raising check must not sink the others) ──

class CheckIsolationTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.dirname(SCRIPT))
        self.addCleanup(sys.path.remove, os.path.dirname(SCRIPT))
        import tooling_preflight
        self.core = tooling_preflight
        self.tmp = tempfile.mkdtemp(prefix="aao-isolation-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.cwd = os.getcwd()
        os.chdir(self.tmp)
        self.addCleanup(os.chdir, self.cwd)

    def boom(self):
        raise RuntimeError("SECRET-FROM-EXCEPTION-MESSAGE")

    def patch_check(self, name):
        original = self.core.CHECKS[name]
        self.core.CHECKS[name] = (self.boom, original[1])
        self.addCleanup(self.core.CHECKS.__setitem__, name, original)

    def test_failing_check_keeps_other_results(self):
        with open(".agent-auth.yaml", "w") as f:
            f.write('github:\n  personal_access_token: "x"\n')
        self.patch_check("android")
        facts = self.core.collect("audit")
        self.assertEqual(facts["check_errors"], ["android: RuntimeError"])
        self.assertEqual(facts["auth"]["tokens"]["github_token"], "set")
        out = self.core.to_json(facts)
        self.assertEqual(out["tools"]["android_commands"]["docs_search"], "unknown")
        self.assertIn("check_failed:android", out["non_blocking_gaps"])
        md = self.core.to_markdown(facts)
        self.assertIn("## Check errors\n- android: RuntimeError", md)
        for rendered in (json.dumps(out), md):
            self.assertNotIn("SECRET-FROM-EXCEPTION-MESSAGE", rendered)

    def test_every_check_has_a_renderable_fallback(self):
        for name in list(self.core.CHECKS):
            with self.subTest(check=name):
                self.patch_check(name)
                facts = self.core.collect("audit")
                self.core.to_json(facts)
                self.core.to_markdown(facts)
                self.assertIn(f"{name}: RuntimeError", facts["check_errors"])
