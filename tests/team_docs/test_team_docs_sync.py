"""Integration tests for templates/team_docs_sync.py against real git repos.

Each test builds a bare remote plus clones in a temp dir. Nothing touches the
network or the developer's own repositories.

Run:  python3 -m unittest discover -s tests/team_docs -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOL = os.path.join(REPO, "templates", "team_docs_sync.py")
GIT = shutil.which("git")
LOCKS = "active-tasks/app/locks.json"
TASK = "active-tasks/app/tasks/T-1.md"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}


@unittest.skipUnless(GIT, "git is required")
class TeamDocsFixture(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="aao-teamdocs-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.env = {**os.environ, **GIT_ENV}
        self.remote = os.path.join(self.root, "remote.git")
        self.git("init", "-q", "--bare", "-b", "team-trunk", self.remote, cwd=self.root)
        seed = os.path.join(self.root, "seed")
        self.git("clone", "-q", self.remote, seed, cwd=self.root)
        self.write(seed, LOCKS, '{"version": 1, "locks": []}\n')
        self.git("add", "-A", cwd=seed)
        self.git("commit", "-q", "-m", "seed", cwd=seed)
        self.git("push", "-q", "origin", "HEAD:team-trunk", cwd=seed)
        self.a = self.clone("a")
        self.b = self.clone("b")

    # ── helpers ──
    def git(self, *args, cwd):
        return subprocess.run([GIT, *args], cwd=cwd, env=self.env, check=True,
                              capture_output=True, text=True).stdout.strip()

    def clone(self, name):
        path = os.path.join(self.root, name)
        self.git("clone", "-q", "-b", "team-trunk", self.remote, path, cwd=self.root)
        return path

    def write(self, repo, rel, content):
        p = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

    def read_file(self, repo, rel):
        with open(os.path.join(repo, rel), encoding="utf-8") as f:
            return f.read()

    def tool(self, *args):
        return subprocess.run([sys.executable, TOOL, *args], env=self.env,
                              capture_output=True, text=True, timeout=60)

    def snapshot(self, repo):
        return (self.git("rev-parse", "HEAD", cwd=repo),
                self.git("status", "--porcelain", "--untracked-files=all", cwd=repo),
                self.git("rev-parse", "--abbrev-ref", "HEAD", cwd=repo))

    def push_from_b(self, rel, content, msg="b change"):
        self.write(self.b, rel, content)
        self.git("add", "--", rel, cwd=self.b)
        self.git("commit", "-q", "-m", msg, cwd=self.b)
        self.git("push", "-q", cwd=self.b)


class ReadTests(TeamDocsFixture):
    def test_reads_upstream_without_touching_dirty_checkout(self):
        self.write(self.a, "notes-local.txt", "untracked work in progress\n")
        self.write(self.a, LOCKS, '{"local": "edit not committed"}\n')
        before = self.snapshot(self.a)
        self.push_from_b(LOCKS, '{"version": 1, "locks": [{"file": "X.kt"}]}\n')
        r = self.tool("read", self.a, LOCKS, TASK)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["sync"], "fresh")
        self.assertEqual(data["lock_freshness"], "fresh")
        self.assertEqual(data["upstream"], "origin/team-trunk")
        self.assertIn("X.kt", data["files"][LOCKS]["content"])
        self.assertFalse(data["files"][TASK]["present"])
        self.assertEqual(self.snapshot(self.a), before)
        self.assertIn("edit not committed", self.read_file(self.a, LOCKS))

    def test_no_upstream_means_lock_data_unknown(self):
        self.git("checkout", "-q", "-b", "local-only", cwd=self.a)
        data = json.loads(self.tool("read", self.a, LOCKS).stdout)
        self.assertEqual(data["sync"], "no_upstream")
        self.assertEqual(data["lock_freshness"], "unknown")
        self.assertTrue(data["files"][LOCKS]["present"])

    def test_fetch_failure_means_lock_data_unknown(self):
        self.git("remote", "set-url", "origin", os.path.join(self.root, "missing.git"), cwd=self.a)
        before = self.snapshot(self.a)
        data = json.loads(self.tool("read", self.a, LOCKS).stdout)
        self.assertEqual(data["sync"], "fetch_failed")
        self.assertEqual(data["lock_freshness"], "unknown")
        self.assertTrue(data["files"][LOCKS]["present"])
        self.assertEqual(self.snapshot(self.a), before)

    def test_reports_unpushed_local_commits(self):
        self.write(self.a, TASK, "mine\n")
        self.git("add", "--", TASK, cwd=self.a)
        self.git("commit", "-q", "-m", "local", cwd=self.a)
        data = json.loads(self.tool("read", self.a, LOCKS).stdout)
        self.assertEqual(data["local_ahead"], 1)


class WriteTests(TeamDocsFixture):
    def test_begin_refuses_pre_existing_dirty_tree(self):
        self.write(self.a, "someone-else.md", "not mine\n")
        before = self.snapshot(self.a)
        r = self.tool("begin", self.a)
        self.assertEqual(r.returncode, 3)
        self.assertIn("someone-else.md", json.loads(r.stdout)["dirty"])
        self.assertEqual(self.snapshot(self.a), before)

    def test_begin_syncs_clean_tree(self):
        self.push_from_b(TASK, "from b\n")
        r = self.tool("begin", self.a)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.read_file(self.a, TASK), "from b\n")

    def test_full_stage_0_lifecycle_commits_only_task_paths(self):
        self.assertEqual(self.tool("begin", self.a).returncode, 0)
        self.write(self.a, LOCKS, '{"version": 1, "locks": [{"file": "A.kt", "task": "T-1"}]}\n')
        self.write(self.a, TASK, "# T-1\n")
        r = self.tool("commit-push", self.a, "-m", "team-docs: T-1 stage 0 planning locks",
                      "--", LOCKS, TASK)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.git("status", "--porcelain", cwd=self.a), "")
        self.git("fetch", "-q", cwd=self.b)
        files = self.git("show", "--name-only", "--format=", "origin/team-trunk", cwd=self.b).split()
        self.assertEqual(sorted(files), sorted([LOCKS, TASK]))

    def test_unrelated_change_blocks_commit(self):
        self.write(self.a, LOCKS, '{"version": 1, "locks": [{"file": "A.kt"}]}\n')
        self.write(self.a, "unrelated.md", "appeared meanwhile\n")
        head = self.git("rev-parse", "HEAD", cwd=self.a)
        r = self.tool("commit-push", self.a, "-m", "x", "--", LOCKS)
        self.assertEqual(r.returncode, 3)
        self.assertIn("unrelated.md", json.loads(r.stdout)["unrelated"])
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.a), head)
        self.assertEqual(self.git("diff", "--cached", "--name-only", cwd=self.a), "")

    def test_rejected_push_is_retried_once_after_rebase(self):
        self.push_from_b("active-tasks/app/tasks/T-2.md", "other task\n")
        self.write(self.a, TASK, "# T-1\n")
        r = self.tool("commit-push", self.a, "-m", "team-docs: T-1", "--", TASK)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["push_attempts"], 2)
        self.git("fetch", "-q", cwd=self.b)
        tree = self.git("ls-tree", "-r", "--name-only", "origin/team-trunk", cwd=self.b).split()
        self.assertIn(TASK, tree)
        self.assertIn("active-tasks/app/tasks/T-2.md", tree)

    def test_rebase_conflict_aborts_and_asks(self):
        self.push_from_b(LOCKS, '{"version": 1, "locks": [{"file": "B.kt"}]}\n')
        self.write(self.a, LOCKS, '{"version": 1, "locks": [{"file": "A.kt"}]}\n')
        r = self.tool("commit-push", self.a, "-m", "team-docs: T-1 locks", "--", LOCKS)
        self.assertEqual(r.returncode, 4)
        self.assertIn(LOCKS, json.loads(r.stdout)["conflicts"])
        rebase_dir = os.path.join(self.a, ".git", "rebase-merge")
        self.assertFalse(os.path.exists(rebase_dir))
        self.assertEqual(self.git("status", "--porcelain", cwd=self.a), "")

    def test_path_outside_repo_is_rejected(self):
        r = self.tool("commit-push", self.a, "-m", "x", "--", "../escape.md")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
