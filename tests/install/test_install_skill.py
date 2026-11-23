"""Tests for scripts/install_skill.py.

Run:  python3 -m unittest discover -s tests/install -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOL = os.path.join(REPO, "scripts", "install_skill.py")

SKILL_MD = "---\nname: x\nmetadata:\n  version: {v}\n---\n# X v{v}\n"


def run(*args):
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True)


class InstallSkillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        self.dest = os.path.join(self.tmp, "skills", "aao")
        os.makedirs(os.path.join(self.repo, "refs"))
        os.makedirs(os.path.join(self.repo, "tests"))
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        self.commit_version("6.1.3")
        self.old = self.head()
        self.commit_version("6.2.0")
        self.new = self.head()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        subprocess.run(["git", "-C", self.repo, *args], check=True, capture_output=True)

    def head(self):
        return subprocess.run(["git", "-C", self.repo, "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()

    def commit_version(self, v):
        with open(os.path.join(self.repo, "SKILL.md"), "w") as fh:
            fh.write(SKILL_MD.format(v=v))
        with open(os.path.join(self.repo, "refs", "a.md"), "w") as fh:
            fh.write(v)
        with open(os.path.join(self.repo, "tests", "t.py"), "w") as fh:
            fh.write("")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", v)

    def install(self, ref="HEAD"):
        return run("--repo", self.repo, "--dest", self.dest, "--ref", ref)

    def test_installs_ref_with_marker_and_without_tests(self):
        proc = self.install()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(os.path.join(self.dest, ".aao-install.json")) as fh:
            marker = json.load(fh)
        self.assertEqual(marker["commit"], self.new)
        self.assertEqual(marker["version"], "6.2.0")
        self.assertTrue(os.path.exists(os.path.join(self.dest, "refs", "a.md")))
        self.assertFalse(os.path.exists(os.path.join(self.dest, "tests")))

    def test_untracked_files_are_not_installed(self):
        with open(os.path.join(self.repo, ".agent-auth.yaml"), "w") as fh:
            fh.write("secret")
        self.assertEqual(self.install().returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.dest, ".agent-auth.yaml")))

    def test_existing_install_is_backed_up_not_deleted(self):
        os.makedirs(self.dest)
        with open(os.path.join(self.dest, "SKILL.md"), "w") as fh:
            fh.write(SKILL_MD.format(v="4.3.0"))
        proc = self.install()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        backup = json.loads(proc.stdout)["backup"]
        skills_dir = os.path.dirname(self.dest)
        self.assertNotEqual(os.path.dirname(backup), skills_dir,
                            "a backup inside the skills dir would load as a duplicate skill")
        self.assertEqual(os.listdir(skills_dir), ["aao"])
        with open(os.path.join(backup, "SKILL.md")) as fh:
            self.assertIn("4.3.0", fh.read())

    def test_older_ref_installs_that_version(self):
        self.assertEqual(self.install(self.old).returncode, 0)
        with open(os.path.join(self.dest, "refs", "a.md")) as fh:
            self.assertEqual(fh.read(), "6.1.3")

    def test_check_matches_and_mismatches(self):
        self.install(self.old)
        ok = run("--repo", self.repo, "--dest", self.dest, "--ref", self.old, "--check")
        self.assertEqual(ok.returncode, 0, ok.stdout)
        bad = run("--repo", self.repo, "--dest", self.dest, "--ref", self.new, "--check")
        self.assertEqual(bad.returncode, 1)
        self.assertFalse(json.loads(bad.stdout)["match"])

    def test_check_without_marker_reports_version_and_fails(self):
        os.makedirs(self.dest)
        with open(os.path.join(self.dest, "SKILL.md"), "w") as fh:
            fh.write(SKILL_MD.format(v="4.3.0"))
        proc = run("--repo", self.repo, "--dest", self.dest, "--check")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout)["installed_version"], "4.3.0")

    def test_symlink_dest_is_refused(self):
        os.makedirs(os.path.dirname(self.dest))
        os.symlink(self.repo, self.dest)
        proc = self.install()
        self.assertEqual(proc.returncode, 2)
        self.assertIn("symlink", proc.stderr)
        self.assertTrue(os.path.islink(self.dest))

    def test_unknown_ref_fails_without_touching_dest(self):
        proc = self.install("no-such-ref")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(os.path.exists(self.dest))
        leftovers = [n for n in os.listdir(os.path.dirname(self.dest))] \
            if os.path.isdir(os.path.dirname(self.dest)) else []
        self.assertFalse([n for n in leftovers if n.startswith(".aao-install-")])


if __name__ == "__main__":
    unittest.main()
