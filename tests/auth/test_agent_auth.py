"""Tests for templates/agent_auth.py — credential access without exposing secrets.

Run:  python3 -m unittest discover -s tests/auth -v
"""
import base64
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
TOOL = os.path.join(REPO, "templates", "agent_auth.py")
TEMPLATE = os.path.join(REPO, "templates", "agent-auth.example.yaml")

SECRET = "tok-SECRET-1234567890"
GH_SECRET = "ghp_SECRET_abcdef"

FILLED = textwrap.dedent(f"""\
    workspace:
      name: "team"
    atlassian:
      domain: "acme.atlassian.net"
      email: "dev@acme.test"
      api_token: "{SECRET}"   # inline comment
    figma:
      personal_access_token: ""
    github:
      personal_access_token: '{GH_SECRET}'
    projects:
      - name: "client-alpha"
        jira_project_key: "CA"
        atlassian:
          domain: "alpha.atlassian.net"
          api_token: "alpha-SECRET-999"
      - name: "plat"
        jira_project_key: "PLAT"
    """)


class AuthFixture(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="aao-auth-")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def write_auth(self, content, mode=0o600):
        path = os.path.join(self.dir, ".agent-auth.yaml")
        mode_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
        with open(path, "wb") as f:
            f.write(mode_bytes)
        os.chmod(path, mode)
        return path

    def run_tool(self, *args, env=None):
        full_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": self.dir}
        full_env.update(env or {})
        return subprocess.run([sys.executable, TOOL, *args], cwd=self.dir, env=full_env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=30)

    def assert_no_secret(self, result, *secrets):
        for value in secrets or (SECRET, GH_SECRET, "alpha-SECRET-999"):
            self.assertNotIn(value, result.stdout)
            self.assertNotIn(value, result.stderr)


# ── Parser ───────────────────────────────────────────────────────────────────

class ParserTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.dirname(TOOL))
        self.addCleanup(sys.path.remove, os.path.dirname(TOOL))
        import agent_auth
        self.mod = agent_auth

    def test_template_parses_with_all_tokens_empty(self):
        with open(TEMPLATE, encoding="utf-8") as f:
            data = self.mod.load_auth(f.read())
        self.assertEqual(data["atlassian"]["api_token"], "")
        self.assertEqual(data["figma"]["personal_access_token"], "")
        self.assertEqual(data["github"]["personal_access_token"], "")
        self.assertEqual(data["projects"], [])

    def test_nested_projects_and_quotes(self):
        data = self.mod.load_auth(FILLED)
        self.assertEqual(data["atlassian"]["api_token"], SECRET)
        self.assertEqual(data["github"]["personal_access_token"], GH_SECRET)
        self.assertEqual(data["projects"][0]["jira_project_key"], "CA")
        self.assertEqual(data["projects"][0]["atlassian"]["api_token"], "alpha-SECRET-999")
        self.assertEqual(data["projects"][1], {"name": "plat", "jira_project_key": "PLAT"})

    def test_hash_inside_quotes_is_kept(self):
        data = self.mod.load_auth('github:\n  personal_access_token: "a#b c"  # note\n')
        self.assertEqual(data["github"]["personal_access_token"], "a#b c")

    def test_commented_keys_are_ignored(self):
        data = self.mod.load_auth('atlassian:\n  api_token: ""\n# api_token: "x"\n')
        self.assertEqual(data["atlassian"], {"api_token": ""})

    def test_malformed_file_error_never_quotes_content(self):
        with self.assertRaises(self.mod.AuthFileError) as ctx:
            self.mod.load_auth(f'atlassian:\n  api_token: "{SECRET}"\n      stray: "{SECRET}"\n')
        self.assertNotIn(SECRET, str(ctx.exception))

    def test_project_override_is_per_field(self):
        data = self.mod.load_auth(FILLED)
        fields, sources = self.mod.resolve(data, "atlassian", "CA")
        self.assertEqual(fields["domain"], "alpha.atlassian.net")
        self.assertEqual(fields["email"], "dev@acme.test")          # falls back to Level 2
        self.assertEqual(sources["domain"], "project:CA")
        self.assertEqual(sources["email"], "default")

    def test_project_without_service_block_uses_default(self):
        data = self.mod.load_auth(FILLED)
        fields, sources = self.mod.resolve(data, "atlassian", "PLAT")
        self.assertEqual(fields["api_token"], SECRET)
        self.assertEqual(sources["api_token"], "default")


# ── init ─────────────────────────────────────────────────────────────────────

class InitTests(AuthFixture):
    def test_creates_owner_only_file_from_template(self):
        r = self.run_tool("init")
        self.assertEqual(r.returncode, 0, r.stderr)
        path = os.path.join(self.dir, ".agent-auth.yaml")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        with open(path, encoding="utf-8") as f, open(TEMPLATE, encoding="utf-8") as t:
            self.assertEqual(f.read(), t.read())
        self.assertIn("created", r.stdout)

    def test_never_overwrites(self):
        self.write_auth(FILLED)
        r = self.run_tool("init")
        self.assertEqual(r.returncode, 0)
        self.assertIn("exists", r.stdout)
        with open(os.path.join(self.dir, ".agent-auth.yaml"), encoding="utf-8") as f:
            self.assertEqual(f.read(), FILLED)


# ── status ───────────────────────────────────────────────────────────────────

class StatusTests(AuthFixture):
    def test_reports_states_without_values(self):
        self.write_auth(FILLED)
        r = self.run_tool("status", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assert_no_secret(r)
        self.assertNotIn("acme.atlassian.net", r.stdout)
        self.assertNotIn("dev@acme.test", r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["file"], "present")
        self.assertEqual(data["permissions"], "ok")
        self.assertEqual(data["services"]["atlassian"]["fields"]["api_token"], "set")
        self.assertEqual(data["services"]["figma"]["fields"]["personal_access_token"], "empty")
        self.assertEqual(data["services"]["github"]["fields"]["personal_access_token"], "set")

    def test_text_output_has_no_values(self):
        self.write_auth(FILLED)
        r = self.run_tool("status")
        self.assert_no_secret(r)
        self.assertIn("atlassian (default): domain=set email=set api_token=set", r.stdout)

    def test_project_resolution(self):
        self.write_auth(FILLED)
        data = json.loads(self.run_tool("status", "--project", "CA", "--json").stdout)
        self.assertEqual(data["services"]["atlassian"]["sources"]["api_token"], "project:CA")

    def test_permissions_too_open(self):
        self.write_auth(FILLED, mode=0o644)
        data = json.loads(self.run_tool("status", "--json").stdout)
        self.assertEqual(data["permissions"], "too_open")

    def test_fix_permissions(self):
        path = self.write_auth(FILLED, mode=0o644)
        r = self.run_tool("status", "--fix-permissions", "--json")
        self.assertEqual(json.loads(r.stdout)["permissions"], "ok")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_missing_file(self):
        data = json.loads(self.run_tool("status", "--json").stdout)
        self.assertEqual(data["file"], "missing")

    def test_unreadable_file_no_traceback_no_secret(self):
        self.write_auth(f'atlassian:\n  api_token: "{SECRET}\xff"\n'.encode("utf-8") + b"\xff\xfe")
        r = self.run_tool("status", "--json")
        self.assertEqual(json.loads(r.stdout)["file"], "unreadable")
        self.assertNotIn("Traceback", r.stderr)
        self.assert_no_secret(r)


# ── exec ─────────────────────────────────────────────────────────────────────

class ExecTests(AuthFixture):
    def test_injects_env_and_redacts_stdout_and_stderr(self):
        self.write_auth(FILLED)
        r = self.run_tool("exec", "github", "--", "sh", "-c",
                          'echo "out:$AAO_GITHUB_TOKEN"; echo "err:$AAO_GITHUB_TOKEN" >&2')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assert_no_secret(r, GH_SECRET)
        self.assertIn("out:[REDACTED:github.personal_access_token]", r.stdout)
        self.assertIn("err:[REDACTED:github.personal_access_token]", r.stderr)

    def test_env_actually_reaches_child(self):
        self.write_auth(FILLED)
        r = self.run_tool("exec", "atlassian", "--", "sh", "-c",
                          'test "$AAO_ATLASSIAN_API_TOKEN" = "$EXPECTED" && echo match',
                          env={"EXPECTED": SECRET})
        self.assertIn("match", r.stdout)

    def test_basic_auth_header_is_redacted(self):
        self.write_auth(FILLED)
        encoded = base64.b64encode(f"dev@acme.test:{SECRET}".encode()).decode()
        r = self.run_tool("exec", "atlassian", "--", "sh", "-c",
                          'printf "Authorization: Basic %s\\n" "$(printf "%s:%s" '
                          '"$AAO_ATLASSIAN_EMAIL" "$AAO_ATLASSIAN_API_TOKEN" | base64)"')
        self.assertNotIn(encoded, r.stdout)
        self.assertIn("[REDACTED:atlassian.basic_auth]", r.stdout)

    def test_project_override_used(self):
        self.write_auth(FILLED)
        r = self.run_tool("exec", "atlassian", "--project", "CA", "--", "sh", "-c",
                          'echo "$AAO_ATLASSIAN_DOMAIN"')
        self.assertIn("[REDACTED:atlassian.domain]", r.stdout)
        r2 = self.run_tool("exec", "atlassian", "--project", "CA", "--", "sh", "-c",
                           'test "$AAO_ATLASSIAN_DOMAIN" = alpha.atlassian.net && echo ok')
        self.assertIn("ok", r2.stdout)

    def test_exit_code_passthrough(self):
        self.write_auth(FILLED)
        self.assertEqual(self.run_tool("exec", "github", "--", "sh", "-c", "exit 7").returncode, 7)

    def test_empty_token_refuses_and_does_not_run(self):
        self.write_auth(FILLED)
        marker = os.path.join(self.dir, "ran")
        r = self.run_tool("exec", "figma", "--", "sh", "-c", f"touch {marker}")
        self.assertEqual(r.returncode, 3)
        self.assertFalse(os.path.exists(marker))
        self.assertIn("figma.personal_access_token is empty", r.stderr)
        self.assertIn("do not paste", r.stderr)

    def test_unknown_service(self):
        self.write_auth(FILLED)
        r = self.run_tool("exec", "slack", "--", "true")
        self.assertEqual(r.returncode, 2)

    def test_missing_command(self):
        self.write_auth(FILLED)
        self.assertEqual(self.run_tool("exec", "github").returncode, 2)


if __name__ == "__main__":
    unittest.main()
