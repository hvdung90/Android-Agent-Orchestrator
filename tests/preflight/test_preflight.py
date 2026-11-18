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
if [ "$1" = "rev-parse" ]; then echo "fixturehead"; exit 0; fi
exit 1
"""

GIT_FAIL_STUB = "#!/bin/sh\nexit 128\n"


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
        fx.write(".project-orchestration/memory/session.json",
                 json.dumps({"stage_reached": 3, "task_id": "T-9"}))
        data = fx.json()
        self.assertEqual(data["tools"]["auth_file"], "unreadable")
        self.assertEqual(data["tools"]["atlassian_token"], "unknown")
        self.assertIn("auth_file_unreadable", data["non_blocking_gaps"])
        self.assertEqual(data["session"]["task_id"], "T-9")
        self.assertEqual(data["tools"]["android_cli"], "missing")
        md = fx.markdown()
        self.assertIn("- .agent-auth.yaml: unreadable", md)
        self.assertIn("- atlassian.api_token: unknown", md)
        self.assertIn("- task_id: T-9", md)
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


# ── Cache (current behaviour; AOO-018 hardening lands in PR2) ───────────────

class CacheTests(Base):
    def write_cache(self, fx, **fields):
        fx.write(".project-orchestration/memory/tooling-cache.json", json.dumps(fields))

    def test_expired(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="2000-01-01T00:00:00Z", graph_commit="fixturehead")
        self.assertEqual(fx.json()["cache"]["cache_status"], "stale")
        self.assertIn("- cache_status: stale", fx.markdown())

    def test_commit_mismatch(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="2099-01-01T00:00:00Z", graph_commit="other")
        self.assertEqual(fx.json()["cache"]["cache_status"], "graph_stale")
        self.assertIn("- cache_status: graph_stale", fx.markdown())

    def test_fresh_and_matching(self):
        fx = self.fixture()
        self.write_cache(fx, valid_until="2099-01-01T00:00:00Z", graph_commit="fixturehead")
        self.assertEqual(fx.json()["cache"]["cache_status"], "fresh")

    def test_unreadable(self):
        fx = self.fixture()
        fx.write(".project-orchestration/memory/tooling-cache.json", "{not json")
        self.assertFalse(fx.json()["cache"]["readable"])
        self.assertIn("- cache: unreadable", fx.markdown())

    def test_missing(self):
        fx = self.fixture()
        self.assertFalse(fx.json()["cache"]["present"])
        self.assertIn("- tooling-cache.json: missing", fx.markdown())


# ── Output contract & parity (AOO-023) ───────────────────────────────────────

class OutputContractTests(Base):
    def full_fixture(self):
        fx = self.fixture()
        fx.stub("android", ANDROID_STUB)
        fx.copy_template_auth()
        fx.write("CLAUDE.md", "karpathy rules\n")
        fx.write(".project-orchestration/memory/tooling-cache.json",
                 json.dumps({"valid_until": "2099-01-01T00:00:00Z", "graph_commit": "other"}))
        fx.write(".project-orchestration/memory/session.json",
                 json.dumps({"stage_reached": 2, "task_id": "T-1"}))
        return fx

    def test_json_keeps_backward_compatible_keys(self):
        data = self.full_fixture().json()
        for key in ("timestamp", "mode", "ready_for_stage_0", "blocking_gaps",
                    "non_blocking_gaps", "tools", "architecture_map", "cache"):
            self.assertIn(key, data)
        for key in ("auth_file", "atlassian_token", "figma_token", "github_token",
                    "android_cli", "adb", "android_commands", "android_studio_commands",
                    "understand_anything", "graphify_cli", "graphify_package", "karpathy"):
            self.assertIn(key, data["tools"])

    def test_markdown_keeps_sections(self):
        md = self.full_fixture().markdown()
        for section in ("# Tooling Preflight", "## Mode", "## Timestamp", "## Working directory",
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
        self.assertEqual(data["session"]["task_id"], "T-1")
        self.assertIn("- task_id: T-1", md)
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
        self.assertFalse(data["session"]["present"])
        self.assertIn("- session.json: missing", md)
        self.assertEqual(data["tools"]["android_cli"], "missing")
        self.assertIn("- android CLI: missing", md)

    def test_parity_for_unreadable_states(self):
        fx = self.fixture()
        fx.write_bytes(".agent-auth.yaml", b"\xff\xfe")
        fx.write(".project-orchestration/memory/tooling-cache.json", "{bad")
        fx.write(".project-orchestration/memory/session.json", "[1, 2]")
        data, md = fx.json(), fx.markdown()
        self.assertEqual(data["tools"]["auth_file"], "unreadable")
        self.assertIn("- .agent-auth.yaml: unreadable", md)
        self.assertFalse(data["cache"]["readable"])
        self.assertIn("- cache: unreadable", md)
        self.assertFalse(data["session"]["readable"])
        self.assertIn("- session: unreadable", md)

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
