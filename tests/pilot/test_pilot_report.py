"""Tests for scripts/pilot_report.py (PR8c telemetry + pilot comparison).

Run:  python3 -m unittest discover -s tests/pilot -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOL = os.path.join(REPO, "scripts", "pilot_report.py")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import pilot_report  # noqa: E402


def record(**over):
    base = {
        "schema": "aao-telemetry/1",
        "task_id": "T-1",
        "skill_version": "6.1.3",
        "skill_commit": None,
        "cohort": "candidate",
        "workflow_mode": "fast",
        "mode_upgrades": [],
        "ref_tier": "LIGHT",
        "approval_source": "jira:CA-1@2026-11-18T00:00:00Z",
        "policy_reads": [{"path": "workflows/fast.md", "section": None}],
        "human_interrupts": [],
        "started_at": "2026-11-18T09:00:00Z",
        "first_patch_at": "2026-11-18T09:30:00Z",
        "closed_at": "2026-11-18T10:00:00Z",
        "tokens": {"input": 1000, "output": 200, "cached": 500, "source": "host_usage"},
        "model_tiers": {"default": 9, "deep-reasoning": 0},
        "evidence": {"pass": 3, "fail": 0, "not_run": 0, "blocked": 0},
        "outcome": "closed",
        "review_iterations": 1,
        "escaped_defects": 0,
    }
    base.update(over)
    return base


class SkillRoot(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="aao-pilot-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.write("workflows/fast.md", "a" * 1000)
        self.write("refs/policy.md", "# Policy\n\n## Small\n" + "s" * 100 + "\n\n## Big\n" + "b" * 900 + "\n")

    def write(self, rel, content):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

    def write_log(self, records, name="retro-log.jsonl"):
        p = os.path.join(self.root, name)
        with open(p, "w", encoding="utf-8") as f:
            for r in records:
                f.write((r if isinstance(r, str) else json.dumps(r)) + "\n")
        return p


class ValidationTests(SkillRoot):
    def test_valid_record(self):
        self.assertEqual(pilot_report.validate(record()), [])

    def test_missing_field(self):
        r = record()
        del r["closed_at"]
        self.assertIn("missing field: closed_at", pilot_report.validate(r))

    def test_unknown_field_rejected_so_content_cannot_slip_in(self):
        errors = pilot_report.validate(record(task_brief="add a paywall button"))
        self.assertIn("unknown field: task_brief", errors)

    def test_bad_enum_and_timestamp(self):
        errors = pilot_report.validate(record(workflow_mode="micro", started_at="yesterday"))
        self.assertTrue(any("workflow_mode" in e for e in errors))
        self.assertTrue(any("started_at" in e for e in errors))

    def test_interrupt_kind_checked(self):
        errors = pilot_report.validate(record(human_interrupts=[{"stage_id": "2_requirements", "kind": "chat"}]))
        self.assertTrue(any("kind" in e for e in errors))

    def test_policy_read_path_must_stay_in_pack(self):
        errors = pilot_report.validate(record(policy_reads=[{"path": "../secrets.yaml", "section": None}]))
        self.assertTrue(any("policy_reads" in e for e in errors))


class PolicyBytesTests(SkillRoot):
    def test_whole_file_and_section(self):
        reads = [{"path": "workflows/fast.md", "section": None},
                 {"path": "refs/policy.md", "section": "Small"}]
        n = pilot_report.policy_bytes(reads, self.root, None)
        small = len("## Small\n" + "s" * 100 + "\n\n")
        self.assertEqual(n, 1000 + small)

    def test_repeated_reads_count_each_time(self):
        reads = [{"path": "workflows/fast.md", "section": None}] * 2
        self.assertEqual(pilot_report.policy_bytes(reads, self.root, None), 2000)

    def test_missing_path_is_reported_not_guessed(self):
        with self.assertRaises(pilot_report.UnknownPolicyFile):
            pilot_report.policy_bytes([{"path": "refs/gone.md", "section": None}], self.root, None)

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_reads_the_recorded_skill_commit(self):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        run = lambda *a: subprocess.run(["git", "-C", self.root, *a], check=True, env=env,
                                        capture_output=True, text=True).stdout.strip()
        run("init", "-q")
        run("add", "-A")
        run("commit", "-q", "-m", "baseline")
        old = run("rev-parse", "HEAD")
        self.write("workflows/fast.md", "a" * 10)      # pack shrank later
        reads = [{"path": "workflows/fast.md", "section": None}]
        self.assertEqual(pilot_report.policy_bytes(reads, self.root, old), 1000)
        self.assertEqual(pilot_report.policy_bytes(reads, self.root, None), 10)


class ReportTests(SkillRoot):
    def cohort(self, cohort, mode, n, minutes, tokens, kb_path="workflows/fast.md", defects=0):
        out = []
        for i in range(n):
            out.append(record(task_id=f"{cohort}-{mode}-{i}", cohort=cohort, workflow_mode=mode,
                              closed_at=f"2026-11-18T{9 + minutes // 60:02d}:{minutes % 60:02d}:00Z",
                              first_patch_at="2026-11-18T09:10:00Z",
                              tokens={"input": tokens, "output": 0, "cached": 0, "source": "host_usage"},
                              policy_reads=[{"path": kb_path, "section": None}],
                              escaped_defects=defects))
        return out

    def test_hypotheses_met(self):
        log = self.write_log(self.cohort("baseline", "fast", 5, 100, 10000, "refs/policy.md")
                             + self.cohort("candidate", "fast", 5, 60, 8000))
        report = pilot_report.build_report([log], self.root)
        fast = report["comparison"]["fast"]
        self.assertEqual(fast["lead_time"]["verdict"], "met")       # 40% lower >= 20%
        self.assertEqual(fast["cost"]["verdict"], "met")            # 20% lower >= 15%
        self.assertEqual(fast["policy_kb"]["verdict"], "met")       # 1 KB <= 15 KB
        self.assertEqual(fast["escaped_defects"]["verdict"], "met")

    def test_hypothesis_not_met_and_defects_regress(self):
        log = self.write_log(self.cohort("baseline", "fast", 5, 100, 10000)
                             + self.cohort("candidate", "fast", 5, 95, 9900, defects=1))
        fast = pilot_report.build_report([log], self.root)["comparison"]["fast"]
        self.assertEqual(fast["lead_time"]["verdict"], "not met")
        self.assertEqual(fast["escaped_defects"]["verdict"], "not met")

    def test_insufficient_samples(self):
        log = self.write_log(self.cohort("baseline", "governed", 2, 100, 10000)
                             + self.cohort("candidate", "governed", 3, 50, 5000))
        gov = pilot_report.build_report([log], self.root)["comparison"]["governed"]
        self.assertEqual(gov["lead_time"]["verdict"], "insufficient data")

    def test_unavailable_tokens_excluded_from_cost(self):
        rows = self.cohort("baseline", "fast", 5, 100, 10000) + self.cohort("candidate", "fast", 5, 60, 8000)
        rows[-1]["tokens"] = {"input": None, "output": None, "cached": None, "source": "unavailable"}
        report = pilot_report.build_report([self.write_log(rows)], self.root)
        self.assertEqual(report["groups"]["candidate/fast"]["tokens_n"], 4)
        self.assertEqual(report["comparison"]["fast"]["cost"]["verdict"], "insufficient data")

    def test_invalid_lines_listed_and_excluded(self):
        log = self.write_log([record(), "{not json", record(task_id="T-2", oops=1)])
        report = pilot_report.build_report([log], self.root)
        self.assertEqual(report["valid"], 1)
        self.assertEqual(len(report["invalid"]), 2)

    def test_cli_markdown_and_json(self):
        log = self.write_log(self.cohort("baseline", "fast", 5, 100, 10000)
                             + self.cohort("candidate", "fast", 5, 60, 8000))
        md = subprocess.run([sys.executable, TOOL, "--skill-root", self.root, log],
                            capture_output=True, text=True)
        self.assertEqual(md.returncode, 0, md.stderr)
        self.assertIn("| fast | lead time |", md.stdout)
        js = subprocess.run([sys.executable, TOOL, "--json", "--skill-root", self.root, log],
                            capture_output=True, text=True)
        self.assertEqual(json.loads(js.stdout)["comparison"]["fast"]["lead_time"]["verdict"], "met")


class ContractConsistencyTests(unittest.TestCase):
    def test_contract_schema_lists_every_field(self):
        with open(os.path.join(REPO, "refs", "contracts-and-artifacts.md"), encoding="utf-8") as f:
            text = f.read()
        start = text.index("### `retro-log.jsonl` (telemetry)")
        block = text[start:text.index("\n## ", start)]
        for field in pilot_report.FIELDS:
            self.assertIn(f'"{field}"', block, field)


    def test_pilot_readme_example_is_valid(self):
        with open(os.path.join(REPO, "docs", "pilot", "README.md"), encoding="utf-8") as f:
            text = f.read()
        start = text.index("```json\n") + len("```json\n")
        example = json.loads(text[start:text.index("\n```", start)])
        self.assertEqual(pilot_report.validate(example), [])
        self.assertEqual(example["cohort"], "baseline")

    def test_pilot_readme_baseline_reads_exist_at_baseline_commit(self):
        """The example's policy_reads must be measurable in a real checkout."""
        if not shutil.which("git"):
            self.skipTest("git required")
        code = subprocess.run(["git", "-C", REPO, "cat-file", "-e", "7711e6a^{commit}"],
                              capture_output=True).returncode
        if code != 0:
            self.skipTest("baseline commit not in this clone")
        reads = [{"path": "SKILL.md", "section": None}, {"path": "refs/stage-contracts.md", "section": None}]
        self.assertGreater(pilot_report.policy_bytes(reads, REPO, "7711e6a"), 20000)

if __name__ == "__main__":
    unittest.main()
