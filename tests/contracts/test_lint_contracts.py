"""Regression tests for scripts/lint-contracts.py.

Each test copies the skill pack's linted files into a temp dir, injects one
known regression (or one allowed exception), and checks the linter's verdict.

Run:  python3 -m unittest discover -s tests/contracts -v
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
lint = __import__("lint-contracts")  # hyphenated module name

COPIED = ("SKILL.md", "README.md", "QUICKSTART.md", "CHANGELOG.md",
          "docs", "refs", "templates", "examples")


class LintFixture(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="aao-lint-")
        self.addCleanup(shutil.rmtree, self.root, True)
        for name in COPIED:
            src = os.path.join(REPO, name)
            dst = os.path.join(self.root, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                shutil.copy2(src, dst)

    def path(self, rel):
        return os.path.join(self.root, rel)

    def read(self, rel):
        with open(self.path(rel), encoding="utf-8") as f:
            return f.read()

    def write(self, rel, content):
        os.makedirs(os.path.dirname(self.path(rel)), exist_ok=True)
        with open(self.path(rel), "w", encoding="utf-8") as f:
            f.write(content)

    def append(self, rel, line):
        self.write(rel, self.read(rel) + "\n" + line + "\n")

    def replace(self, rel, old, new):
        content = self.read(rel)
        self.assertIn(old, content, f"fixture anchor missing in {rel}")
        self.write(rel, content.replace(old, new, 1))

    def run_lint(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = lint.main(["lint-contracts", self.root])
        return code, out.getvalue()

    def assert_clean(self):
        code, out = self.run_lint()
        self.assertEqual(code, 0, out)

    def assert_flagged(self, rule_prefix, where):
        code, out = self.run_lint()
        self.assertEqual(code, 1, out)
        hits = [l for l in out.splitlines() if l.startswith(where) and rule_prefix in l]
        self.assertTrue(hits, f"expected {rule_prefix!r} at {where!r}, got:\n{out}")


class Baseline(LintFixture):
    def test_current_repo_is_clean(self):
        self.assert_clean()


class RetiredPathTests(LintFixture):
    def test_global_lock_path(self):
        self.append("SKILL.md", "Read `active-tasks/locks.json` at Stage -1.")
        self.assert_flagged("lock-path", "SKILL.md:")

    def test_global_board_path(self):
        self.append("refs/team-docs.md", "Append to `active-tasks/README.md`.")
        self.assert_flagged("board-path", "refs/team-docs.md:")

    def test_old_readiness_field(self):
        self.append("refs/sub-agents.md", "proceed_to_stage_0: true")
        self.assert_flagged("readiness-field", "refs/sub-agents.md:")

    def test_old_session_path(self):
        self.append("templates/preflight-report.md", "- read memory/session.json")
        self.assert_flagged("session-path", "templates/preflight-report.md:")

    def test_legacy_mention_is_allowed(self):
        self.append("refs/team-docs.md",
                    "If the legacy `active-tasks/locks.json` exists, migrate it.")
        self.append("refs/provisioning-preflight.md",
                    "A legacy `memory/session.json` is a resume candidate.")
        self.assert_clean()

    def test_history_files_are_not_scanned(self):
        self.append("CHANGELOG.md", "- old: read `active-tasks/locks.json`, proceed_to_stage_0")
        self.write("docs/Some-Review-2026.md",
                   "Old text: `active-tasks/README.md`, memory/session.json\n")
        self.assert_clean()


class VersionTests(LintFixture):
    def test_ref_header_mismatch(self):
        self.replace("refs/playbooks.md", "_Skill version: 6.1.3", "_Skill version: 6.1.1")
        self.assert_flagged("version:", "refs/playbooks.md:")

    def test_readme_header_mismatch(self):
        self.replace("README.md", "_Current skill version: 6.1.3_", "_Current skill version: 6.1.0_")
        self.assert_flagged("version:", "README.md:")

    def test_historical_versions_in_changelog_are_fine(self):
        self.assertIn("## v6.1.1", self.read("CHANGELOG.md"))
        self.assert_clean()

    def test_unreleased_section_does_not_count_as_version(self):
        content = self.read("CHANGELOG.md")
        if "## Unreleased" not in content:
            self.write("CHANGELOG.md",
                       content.replace("# Changelog\n", "# Changelog\n\n## Unreleased\n\n- x\n", 1))
        self.assert_clean()

    def test_changelog_ahead_of_skill_is_flagged(self):
        self.replace("CHANGELOG.md", "## v6.1.3", "## v6.2.0\n\n- x\n\n## v6.1.3")
        self.assert_flagged("version:", "CHANGELOG.md:")


class StageMinusOneStateTests(LintFixture):
    """Stage -1 has no task_id: its state lives in reports/preflight.md."""

    def test_task_session_output_in_stage_minus_one_contract(self):
        self.replace("refs/stage-contracts.md", "  - .project-orchestration/status.json",
                     "  - .project-orchestration/tasks/{task_id}/session.json (stage_reached: -1)\n"
                     "  - .project-orchestration/status.json")
        self.assert_flagged("stage-1-session", "refs/stage-contracts.md:")

    def test_team_docs_stage_minus_one_writes_session(self):
        self.replace("refs/team-docs.md", "7. `[C]` Read per-repo board",
                     "   - log `team_docs.x` in `session.json`.\n7. `[C]` Read per-repo board")
        self.assert_flagged("stage-1-session", "refs/team-docs.md:")

    def test_stage_minus_one_state_must_name_preflight_report(self):
        content = self.read("refs/stage-contracts.md")
        start, end = content.index("## Stage -1"), content.index("## Stage 0")
        block = content[start:end].replace(
            "persisted_to: .project-orchestration/reports/preflight.md", "persisted_to: somewhere")
        self.write("refs/stage-contracts.md", content[:start] + block + content[end:])
        self.assert_flagged("stage-1-state", "refs/stage-contracts.md:")



class StageIdTests(LintFixture):
    """AOO-008: every persisted state names its stage unambiguously."""

    def stage_section(self, header):
        content = self.read("refs/stage-contracts.md")
        start = content.index(header)
        end = content.index("\n## ", start + 1)
        return content, start, end

    def edit_section(self, header, old, new):
        content, start, end = self.stage_section(header)
        block = content[start:end]
        self.assertIn(old, block)
        self.write("refs/stage-contracts.md",
                   content[:start] + block.replace(old, new, 1) + content[end:])

    def test_missing_stage_id(self):
        self.edit_section("## Stage 2 — Requirements", '  stage_id: "2_requirements"\n', "")
        self.assert_flagged("stage-id", "refs/stage-contracts.md:")

    def test_wrong_stage_id_for_clarification(self):
        self.edit_section("## Stage 1.5", 'stage_id: "1.5_clarification"', 'stage_id: "1_discovery"')
        self.assert_flagged("stage-id", "refs/stage-contracts.md:")

    def test_clarification_back_to_stage_reached_1(self):
        self.edit_section("## Stage 1.5", "stage_reached: 1.5", "stage_reached: 1")
        self.assert_flagged("stage-id", "refs/stage-contracts.md:")

    def test_order_table_must_list_every_stage(self):
        self.replace("refs/stage-contracts.md", "| 5 | `2.5_decision_gate` | 2.5 |\n", "")
        self.assert_flagged("stage-order", "refs/stage-contracts.md:")


class RefTierTests(LintFixture):
    """AOO-015: Stage 0 only has a preliminary tier; Stage 1 finalizes it."""

    def test_final_tier_at_stage_0_is_flagged(self):
        self.replace("refs/stage-contracts.md", "  - preliminary_ref_tier",
                     "  - ref tier determined (LIGHT / MEDIUM / HEAVY / FULL)\n  - preliminary_ref_tier")
        self.assert_flagged("ref-tier", "refs/stage-contracts.md:")

    def test_stage_1_must_finalize_tier(self):
        self.replace("refs/stage-contracts.md", "  - ref_tier finalized", "  - tier maybe")
        self.assert_flagged("ref-tier", "refs/stage-contracts.md:")


class SourceModeInputTests(LintFixture):
    """AOO-014 (review): a Mode C task has no links and no local docs, so the
    Discovery input contract must name the recorded brief for C."""

    def test_stage_1_input_without_mode_c_is_flagged(self):
        content = self.read("refs/stage-contracts.md")
        start = content.index("## Stage 1 — Discovery")
        end = content.index("guard_conditions:", start)
        block = "\n".join(l for l in content[start:end].splitlines() if "task_brief" not in l)
        self.write("refs/stage-contracts.md", content[:start] + block + "\n" + content[end:])
        self.assert_flagged("source-mode-inputs", "refs/stage-contracts.md:")

    def test_stage_0_must_record_task_brief(self):
        content = self.read("refs/stage-contracts.md")
        start = content.index("## Stage 0")
        end = content.index("## Stage 1 ")
        block = "\n".join(l for l in content[start:end].splitlines() if "task_brief" not in l)
        self.write("refs/stage-contracts.md", content[:start] + block + "\n" + content[end:])
        self.assert_flagged("source-mode-inputs", "refs/stage-contracts.md:")


class SkippedStageMigrationTests(LintFixture):
    """AOO-008 (review): a skipped stage never becomes stage_id, legacy migration included."""

    def test_skip_mapped_to_skipped_stage_id_is_flagged(self):
        self.replace("refs/stage-contracts.md", "### Legacy sessions (no `stage_id`)\n",
                     "### Legacy sessions (no `stage_id`)\n\n"
                     "  - `skip-log.json` records a Stage 1.5 skip → `1.5_clarification`, complete;\n")
        self.assert_flagged("skipped-stage", "refs/stage-contracts.md:")

    def test_next_stage_rule_required(self):
        content = self.read("refs/stage-contracts.md")
        self.assertIn("**Next stage**", content)
        self.write("refs/stage-contracts.md", content.replace("**Next stage**", "**Later**", 1))
        self.assert_flagged("skipped-stage", "refs/stage-contracts.md:")


class ToolingReadinessNameTests(LintFixture):
    """PR2 review: only preflight.md carries the final ready_for_stage_0."""

    def test_same_field_name_claim_is_flagged(self):
        self.append("refs/stage-contracts.md",
                    "  - preflight.md must have ready_for_stage_0: true (same field name as `tooling-preflight.sh --json`)")
        self.assert_flagged("readiness-field", "refs/stage-contracts.md:")

    def test_tooling_auditor_must_not_emit_final_gate(self):
        self.append("refs/sub-agents.md", "ready_for_stage_0: true | false")
        self.assert_flagged("readiness-field", "refs/sub-agents.md:")


class TeamDocsReadPhaseTests(LintFixture):
    """AOO-013: Stage -1 team-docs reads must not mutate the docs checkout."""

    def inject_read_step(self, text):
        self.replace("refs/team-docs.md", "7. `[C]` Read per-repo board", text + "\n7. `[C]` Read per-repo board")

    def test_pull_rebase_in_read_phase_is_flagged(self):
        self.inject_read_step("8. `[both]` `git pull --rebase` on docs repo before reading any file.")
        self.assert_flagged("read-phase-git", "refs/team-docs.md:")

    def test_other_mutating_commands_are_flagged(self):
        for cmd in ("git -C $T checkout main", "git stash", "git -C $T reset --hard @{u}",
                    "git merge origin/main"):
            with self.subTest(cmd=cmd):
                self.setUp()
                self.inject_read_step(f"8. `[both]` run `{cmd}` first.")
                self.assert_flagged("read-phase-git", "refs/team-docs.md:")

    def test_prohibition_wording_is_allowed(self):
        self.inject_read_step("   - Never run `git pull`, `rebase`, `checkout` here.")
        self.assert_clean()

    def test_fetch_and_show_are_allowed(self):
        self.inject_read_step('8. `[both]` `git -C $T fetch --quiet` then `git -C $T show "$up:path"`.')
        self.assert_clean()

    def test_write_phase_may_rebase(self):
        content = self.read("refs/team-docs.md")
        self.assertIn("pull --rebase", content[content.index("## Writes"):])
        self.assert_clean()

if __name__ == "__main__":
    unittest.main()
