#!/usr/bin/env python3
"""Contract lint for the Android Agent Orchestrator skill pack.

Catches drift between SKILL.md, README, docs/FLOW.md, refs/ and templates/
that has already happened at least once (see docs review AOO-004/016/019/020):

  1. lock index path      — only per-repo `active-tasks/<repo>/locks.json`
  2. cross-repo board     — only `active-tasks/shared/README.md`
  3. readiness field      — only `ready_for_stage_0` (never `proceed_to_stage_0`)
  4. task session path    — only `tasks/{task_id}/session.json`; Stage -1 must
                            not produce a task session (task_id is born in Stage 0)
  5. version headers      — SKILL frontmatter == SKILL heading == README ==
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


def check_stage_minus_one_session(root: str) -> Iterable[Finding]:
    path = os.path.join(root, "refs", "stage-contracts.md")
    stage = section(read_lines(path), "## Stage -1", "## Stage 0")
    for no, line in stage:
        if "tasks/{task_id}/session.json" in line and "legacy" not in line.lower():
            yield Finding(rel(root, path), no,
                          "stage-1-session: Stage -1 has no task_id; Stage 0 creates the session",
                          line.strip())


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
    check_retired, check_stage_minus_one_session, check_versions,
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
