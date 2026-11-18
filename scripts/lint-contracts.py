#!/usr/bin/env python3
"""Contract lint for the Android Agent Orchestrator skill pack.

Catches drift between SKILL.md, README, docs/FLOW.md, refs/ and templates/
that has already happened at least once (see docs review AOO-004/016/019/020):

  1. lock index path      — only per-repo `active-tasks/<repo>/locks.json`
  2. cross-repo board     — only `active-tasks/shared/README.md`
  3. readiness field      — only `ready_for_stage_0` (never `proceed_to_stage_0`)
  4. task session path    — only `tasks/{task_id}/session.json`; Stage -1 must
                            not write a task session (task_id is born in Stage 0):
                            its state persists to reports/preflight.md
  5. stage ids            — every state block sets stage_id/stage_reached of its
                            stage; § Stage order lists all stages (AOO-008)
  6. ref tier             — Stage 0 preliminary only, Stage 1 finalizes (AOO-015)
  7. version headers      — SKILL frontmatter == SKILL heading == README ==
                            FLOW == every refs/*.md header == latest CHANGELOG

A line may mention a retired path only when it also contains the word
"legacy" (migration guidance). CHANGELOG and docs/*Review* files are history
and are not scanned for rules 1–4.

Usage:  python3 scripts/lint-contracts.py [repo_root]   (exit 1 on findings)
"""
from __future__ import annotations

import glob
import os
import re
import sys
from typing import Callable, Iterable, List, NamedTuple, Optional, Tuple


class Finding(NamedTuple):
    path: str
    line: int
    rule: str
    text: str


RETIRED_PATTERNS: Tuple[Tuple[str, "re.Pattern[str]"], ...] = (
    ("lock-path: use active-tasks/<repo>/locks.json", re.compile(r"active-tasks/locks\.json")),
    ("board-path: use active-tasks/shared/README.md", re.compile(r"active-tasks/README\.md")),
    ("readiness-field: use ready_for_stage_0", re.compile(r"proceed_to_stage_0")),
    ("readiness-field: the script reports tooling_ready; only preflight.md has the final ready_for_stage_0",
     re.compile(r"same field name as `tooling-preflight\.sh --json`")),
    ("session-path: use .project-orchestration/tasks/{task_id}/session.json",
     re.compile(r"memory/session\.json")),
)


def scanned_files(root: str) -> List[str]:
    patterns = ("SKILL.md", "README.md", "QUICKSTART.md", "docs/FLOW.md",
                "refs/*.md", "templates/*.md", "examples/*.md")
    files = {p for pat in patterns for p in glob.glob(os.path.join(root, pat))}
    return sorted(p for p in files if os.path.isfile(p))


def read_lines(path: str) -> List[str]:
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


def rel(root: str, path: str) -> str:
    return os.path.relpath(path, root)


def check_retired(root: str) -> Iterable[Finding]:
    for path in scanned_files(root):
        for no, line in enumerate(read_lines(path), 1):
            if "legacy" in line.lower():
                continue
            for rule, pattern in RETIRED_PATTERNS:
                if pattern.search(line):
                    yield Finding(rel(root, path), no, rule, line.strip())


def section(lines: List[str], start: str, end: str) -> List[Tuple[int, str]]:
    out: List[Tuple[int, str]] = []
    inside = False
    for no, line in enumerate(lines, 1):
        if line.startswith(start):
            inside = True
        elif inside and line.startswith(end):
            break
        if inside:
            out.append((no, line))
    return out


STAGE_MINUS_ONE_SECTIONS: Tuple[Tuple[str, str, str], ...] = (
    # (file, section start, next section start)
    ("refs/stage-contracts.md", "## Stage -1", "## Stage 0"),
    ("refs/team-docs.md", "## Reads (Stage -1", "## "),
)
SESSION_HANDOFF_WORDS = ("stage 0", "never", "legacy")
PREFLIGHT_STATE = "persisted_to: .project-orchestration/reports/preflight.md"


def check_stage_minus_one_session(root: str) -> Iterable[Finding]:
    """Stage -1 has no task_id. Inside Stage -1 sections a line may mention
    session.json only to hand off to Stage 0, forbid the write, or describe
    legacy migration."""
    for rel_path, start, end in STAGE_MINUS_ONE_SECTIONS:
        path = os.path.join(root, rel_path)
        for no, line in section(read_lines(path), start, end):
            low = line.lower()
            if "session.json" in low and not any(w in low for w in SESSION_HANDOFF_WORDS):
                yield Finding(rel_path, no,
                              "stage-1-session: Stage -1 has no task session; record in "
                              "reports/preflight.md § Stage -1 state (Stage 0 copies it)",
                              line.strip())


def check_stage_minus_one_state(root: str) -> Iterable[Finding]:
    """Both Stage -1 states must say they persist to reports/preflight.md."""
    rel_path = "refs/stage-contracts.md"
    lines = section(read_lines(os.path.join(root, rel_path)), "## Stage -1", "## Stage 0")
    hits = [no for no, line in lines if PREFLIGHT_STATE in line]
    if len(hits) < 2:
        anchor = lines[0][0] if lines else 0
        yield Finding(rel_path, anchor,
                      "stage-1-state: state_on_complete and state_on_interrupt must both have "
                      f"`{PREFLIGHT_STATE}`", "")


STAGE_HEADER = re.compile(r"^## Stage ")
STAGE_DECL = re.compile(r'^stage: "([^"]+)"')
ORDER_ROW = re.compile(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*(-?[0-9.]+)\s*\|")


def stage_sections(lines: List[str]) -> List[Tuple[int, List[Tuple[int, str]]]]:
    """[(header line no, [(no, line), ...]), ...] for each '## Stage ...' section."""
    sections: List[Tuple[int, List[Tuple[int, str]]]] = []
    current: Optional[List[Tuple[int, str]]] = None
    for no, line in enumerate(lines, 1):
        if STAGE_HEADER.match(line):
            current = []
            sections.append((no, current))
        elif line.startswith("## "):
            current = None
        if current is not None:
            current.append((no, line))
    return sections


def state_blocks(section: List[Tuple[int, str]]) -> List[Tuple[int, str, List[str]]]:
    """[(line no, 'state_on_complete'|'state_on_interrupt', body lines), ...]"""
    blocks: List[Tuple[int, str, List[str]]] = []
    for i, (no, line) in enumerate(section):
        name = line.split(":", 1)[0]
        if name in ("state_on_complete", "state_on_interrupt"):
            body = []
            for _, nxt in section[i + 1:]:
                if nxt and not nxt[0].isspace():
                    break
                body.append(nxt.strip())
            blocks.append((no, name, body))
    return blocks


def check_stage_ids(root: str) -> Iterable[Finding]:
    """AOO-008: every state block carries stage_id == its section's stage and the
    matching stage_reached; the § Stage order table lists every stage in order."""
    rel_path = "refs/stage-contracts.md"
    lines = read_lines(os.path.join(root, rel_path))
    declared: List[str] = []
    for header_no, section in stage_sections(lines):
        stage = next((m.group(1) for _, l in section for m in [STAGE_DECL.match(l)] if m), None)
        if stage is None:
            continue
        declared.append(stage)
        reached = stage.split("_", 1)[0]
        for no, name, body in state_blocks(section):
            if f'stage_id: "{stage}"' not in body:
                yield Finding(rel_path, no, f"stage-id: {name} of {stage} must set stage_id: \"{stage}\"", "")
            if f"stage_reached: {reached}" not in body:
                yield Finding(rel_path, no, f"stage-id: {name} of {stage} must set stage_reached: {reached}", "")
    table = [(no, m.group(1), m.group(2)) for no, l in enumerate(lines, 1) for m in [ORDER_ROW.match(l)] if m]
    if [sid for _, sid, _ in table] != declared:
        anchor = table[0][0] if table else 0
        yield Finding(rel_path, anchor,
                      f"stage-order: § Stage order must list {declared} in that order", "")
    for no, sid, reached in table:
        if sid.split("_", 1)[0] != reached:
            yield Finding(rel_path, no, f"stage-order: {sid} must have stage_reached {sid.split('_', 1)[0]}", "")


def check_ref_tier(root: str) -> Iterable[Finding]:
    """AOO-015: Stage 0 records only a preliminary tier; Stage 1 finalizes it."""
    rel_path = "refs/stage-contracts.md"
    lines = read_lines(os.path.join(root, rel_path))
    stage0 = section(lines, "## Stage 0", "## Stage 1")
    stage1 = section(lines, "## Stage 1 ", "## Stage 1.5")
    for no, line in stage0:
        if re.search(r"\bref[ _]tier\b", line, re.I) and "preliminary" not in line.lower():
            yield Finding(rel_path, no, "ref-tier: Stage 0 may only set preliminary_ref_tier "
                          "(workflow_mode and graph_impact are final only after Stage 1)", line.strip())
    if not any("preliminary_ref_tier" in line for _, line in stage0):
        yield Finding(rel_path, stage0[0][0] if stage0 else 0,
                      "ref-tier: Stage 0 must record preliminary_ref_tier", "")
    if not any("ref_tier finalized" in line for _, line in stage1):
        yield Finding(rel_path, stage1[0][0] if stage1 else 0,
                      "ref-tier: Stage 1 output must include 'ref_tier finalized'", "")


def check_readiness_scope(root: str) -> Iterable[Finding]:
    """Sub-agents report tooling scope only; the parent owns the final gate."""
    rel_path = "refs/sub-agents.md"
    for no, line in enumerate(read_lines(os.path.join(root, rel_path)), 1):
        if line.strip().startswith("ready_for_stage_0:"):
            yield Finding(rel_path, no, "readiness-field: sub-agents report tooling_ready; the parent "
                          "writes the final ready_for_stage_0 into preflight.md", line.strip())


def check_source_mode_inputs(root: str) -> Iterable[Finding]:
    """A Mode C task has no links and no local docs: Stage 0 must record the brief
    and Stage 1 must accept it as its input."""
    rel_path = "refs/stage-contracts.md"
    lines = read_lines(os.path.join(root, rel_path))
    stage0 = section(lines, "## Stage 0", "## Stage 1 ")
    stage1 = section(lines, "## Stage 1 ", "## Stage 1.5")
    if not any("task_brief" in l for _, l in stage0):
        yield Finding(rel_path, stage0[0][0] if stage0 else 0,
                      "source-mode-inputs: Stage 0 must record session.json task_brief", "")
    if not any("C =" in l and "task_brief" in l for _, l in stage1):
        yield Finding(rel_path, stage1[0][0] if stage1 else 0,
                      "source-mode-inputs: Stage 1 input_requires must name the Mode C input "
                      "(C = session.json task_brief)", "")


SKIP_TO_SAME_STAGE = re.compile(r"Stage ([0-9.]+) skip.*→ `\1_")


def check_skipped_stage(root: str) -> Iterable[Finding]:
    """A skipped stage never becomes stage_id (legacy migration included), and
    § Stage order defines how the next stage is resolved past skips."""
    rel_path = "refs/stage-contracts.md"
    lines = read_lines(os.path.join(root, rel_path))
    for no, line in enumerate(lines, 1):
        if SKIP_TO_SAME_STAGE.search(line):
            yield Finding(rel_path, no, "skipped-stage: a skipped stage must not become stage_id; "
                          "keep the last stage that ran and resolve § Stage order Next stage", line.strip())
    if not any("**Next stage**" in l for _, l in section(lines, "### Stage order", "### ")):
        yield Finding(rel_path, 0, "skipped-stage: § Stage order must define **Next stage**", "")


def first_match(path: str, pattern: str) -> Tuple[Optional[str], int]:
    regex = re.compile(pattern)
    for no, line in enumerate(read_lines(path), 1):
        m = regex.search(line)
        if m:
            return m.group(1), no
    return None, 0


def check_versions(root: str) -> Iterable[Finding]:
    skill = os.path.join(root, "SKILL.md")
    canonical, _ = first_match(skill, r"^\s+version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$")
    if canonical is None:
        yield Finding("SKILL.md", 0, "version: frontmatter `version:` not found", "")
        return
    expected: List[Tuple[str, str]] = [
        (skill, r"^# Android Agent Orchestrator v([0-9.]+)"),
        (os.path.join(root, "README.md"), r"_Current skill version: ([0-9.]+)_"),
        (os.path.join(root, "docs", "FLOW.md"), r"_Reflects skill v([0-9.]+)\."),
        (os.path.join(root, "CHANGELOG.md"), r"^## v([0-9.]+)"),
    ] + [(p, r"^_Skill version: ([0-9.]+)") for p in sorted(glob.glob(os.path.join(root, "refs", "*.md")))]
    for path, pattern in expected:
        found, no = first_match(path, pattern)
        if found != canonical:
            yield Finding(rel(root, path), no,
                          f"version: expected {canonical} (SKILL.md frontmatter), found {found}", "")


CHECKS: Tuple[Callable[[str], Iterable[Finding]], ...] = (
    check_retired, check_stage_minus_one_session, check_stage_minus_one_state,
    check_stage_ids, check_ref_tier, check_readiness_scope, check_source_mode_inputs,
    check_skipped_stage, check_versions,
)


def main(argv: List[str]) -> int:
    root = os.path.abspath(argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
    findings = [f for check in CHECKS for f in check(root)]
    for f in findings:
        suffix = f" | {f.text}" if f.text else ""
        print(f"{f.path}:{f.line}: {f.rule}{suffix}")
    print(f"lint-contracts: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
