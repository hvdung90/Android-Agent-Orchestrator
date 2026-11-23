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
  7. read-phase git       — no pull/rebase/merge/checkout/reset/stash in the
                            Stage -1 team-docs reads (AOO-013)
  8. TDD exemptions       — one table in compliance-policy; no "no exceptions" /
                            "CONFIRM-SKIP only" elsewhere; tiers and skip-log
                            reasons match the rows (AOO-007/017)
  9. delivery workflow    — ADR-0002: commit_policy default no_commit; no
                            Jira+Figma floor; Governed triggers + Team tiers;
                            Independent Reviewer at Stage 6; never push product repo
 10. version headers      — SKILL frontmatter == SKILL heading == README ==
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
                "refs/*.md", "templates/*.md", "examples/*.md", "workflows/*.md")
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


READ_PHASE_MUTATION = re.compile(r"\bgit\b[^`\n]*\b(pull|rebase|merge|checkout|reset|stash)\b")


def check_read_phase_git(root: str) -> Iterable[Finding]:
    """AOO-013: Stage -1 team-docs reads must not mutate the docs checkout.
    Lines that state the prohibition (contain 'never') are allowed."""
    rel_path = "refs/team-docs.md"
    for no, line in section(read_lines(os.path.join(root, rel_path)), "## Reads (Stage -1", "## "):
        if READ_PHASE_MUTATION.search(line) and "never" not in line.lower():
            yield Finding(rel_path, no, "read-phase-git: Stage -1 reads use `git fetch` + "
                          "`git show <upstream>:<path>`; pull/rebase/merge/checkout/reset/stash "
                          "belong to § Writes", line.strip())


RAW_GIT_WRITE = re.compile(r"`git (push|pull --rebase|add (\.|-A|--all))")


def check_team_docs_lifecycle(root: str) -> Iterable[Finding]:
    """PR7 review: team-docs writes go through team_docs_sync.py begin/commit-push
    (only the step's own paths), and an unverified lock source is `unknown`."""
    rel_path = "refs/team-docs.md"
    lines = read_lines(os.path.join(root, rel_path))
    for no, line in enumerate(lines, 1):
        low = line.lower()
        if RAW_GIT_WRITE.search(line) and "never" not in low and "begin" not in low \
                and "commit-push" not in low:
            yield Finding(rel_path, no, "write-lifecycle: use `team_docs_sync.py begin` / "
                          "`commit-push -- <paths>` instead of raw git", line.strip())
    for no, line in section(lines, "## Reads (Stage -1", "## "):
        if "no_upstream" in line and "unknown" not in line and "team_docs.sync" not in line:
            yield Finding(rel_path, no, "write-lifecycle: no_upstream must make lock data `unknown` "
                          "(like fetch_failed)", line.strip())


TDD_TABLE_HEADING = "### TDD exemption table"
TDD_ROW = re.compile(r"^\|\s*`([a-z-]+)`\s*\|\s*([^|]+?)\s*\|")
TDD_TIERS = {"AUTO-SKIP", "CONFIRM-SKIP"}


def check_tdd_exemptions(root: str) -> Iterable[Finding]:
    """AOO-007/017: exactly one exemption table (compliance-policy), every other
    file defers to it, and its rows, tiers and skip-log reasons agree."""
    canonical = "refs/compliance-policy.md"
    headings: List[Tuple[str, int]] = []
    for path in scanned_files(root):
        rel_path = rel(root, path)
        for no, line in enumerate(read_lines(path), 1):
            low = line.lower()
            if line.startswith(TDD_TABLE_HEADING):
                headings.append((rel_path, no))
            if "no exceptions" in low:
                yield Finding(rel_path, no, "tdd-exemption: say which § TDD exemption table rows apply "
                              "instead of 'no exceptions'", line.strip())
            if "confirm-skip only" in low:
                yield Finding(rel_path, no, "tdd-exemption: tiers come from § TDD exemption table "
                              "(some rows are AUTO-SKIP)", line.strip())
            if (rel_path == canonical and "never skippable" in low
                    and ("gate e.5" in low or "green evidence" in low)):
                yield Finding(rel_path, no, "tdd-exemption: RED/GREEN are mandatory *unless* a "
                              "§ TDD exemption table row applies", line.strip())
    for rel_path, no in headings:
        if rel_path != canonical:
            yield Finding(rel_path, no, f"tdd-exemption: the only exemption table lives in {canonical}", "")
    if (canonical, ) not in [(r,) for r, _ in headings]:
        yield Finding(canonical, 0, f"tdd-exemption: `{TDD_TABLE_HEADING}` missing", "")
        return
    table = section(read_lines(os.path.join(root, canonical)), TDD_TABLE_HEADING, "### ")
    rows = [(no, m.group(1), m.group(2)) for no, l in table for m in [TDD_ROW.match(l)]
            if m and m.group(2) != "Tier"]  # skip the header row
    for no, reason, tier in rows:
        if tier not in TDD_TIERS:
            yield Finding(canonical, no, f"tdd-exemption: tier of `{reason}` must be AUTO-SKIP or "
                          f"CONFIRM-SKIP, found {tier!r}", "")
    enum_line = next(((no, l) for no, l in table if '"reason":' in l), None)
    if enum_line is None:
        yield Finding(canonical, table[0][0], "tdd-exemption: exemption record has no reason enum", "")
        return
    listed = {r.strip() for r in enum_line[1].split('"reason":', 1)[1].strip(' ",').split("|")}
    if listed != {reason for _, reason, _ in rows}:
        yield Finding(canonical, enum_line[0], "tdd-exemption: skip-log reason enum must list exactly "
                      f"the table rows {sorted(r for _, r, _ in rows)}", "")


MICRO_MODE = re.compile(r"\bmicro\b", re.I)
FAST_DOC = "workflows/fast.md"
FAST_DOC_MAX_BYTES = 12000
DOC_PATH = re.compile(r"`((?:refs|templates|scripts|workflows|docs)/[^`\s]+?)`")
REQUIRED_TRIGGERS = ("Ads SDK / mediation", "Paywall / subscription UI")


def bullets_after(lines: List[str], heading: str) -> Tuple[int, List[str]]:
    """(heading line no, bullet texts) of the first bullet list after `heading`."""
    for i, line in enumerate(lines):
        if line.strip() == heading:
            items: List[str] = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("- "):
                    items.append(nxt[2:].strip())
                elif nxt.strip() and items:
                    break
            return i + 1, items
    return 0, []


def check_fast_path(root: str) -> Iterable[Finding]:
    """PR8a / ADR-0001: micro folded into fast; two-layer never-skipped list; one
    escalation list mirrored in workflows/fast.md; Stage 2 approval source;
    workflows/fast.md stays light and only points at files that exist."""
    for path in scanned_files(root):
        for no, line in enumerate(read_lines(path), 1):
            if MICRO_MODE.search(line) and "legacy" not in line.lower():
                yield Finding(rel(root, path), no, "fast-path: `micro` was folded into `fast` "
                              "(ADR-0001); only legacy notes may mention it", line.strip())
    skill = read_lines(os.path.join(root, "SKILL.md"))
    text = "\n".join(skill)
    for label in ("**Safety invariants**", "**Process gates**"):
        if label not in text:
            yield Finding("SKILL.md", 0, f"fast-path: never-skipped list needs the {label} layer", "")
    for no, line in enumerate(skill, 1):
        if "reduce artifact depth only" in line.lower():
            yield Finding("SKILL.md", no, "fast-path: fast drops process gates; the "
                          "'depth only' rule is retired", line.strip())
    skill_no, skill_items = bullets_after(skill, "### Escalation triggers")
    if not skill_items:
        yield Finding("SKILL.md", 0, "fast-path: `### Escalation triggers` list missing", "")
    for item in REQUIRED_TRIGGERS:
        if item not in skill_items:
            yield Finding("SKILL.md", skill_no, f"fast-path: escalation list must include '{item}'", "")
    fast_path = os.path.join(root, FAST_DOC)
    if not os.path.isfile(fast_path):
        yield Finding(FAST_DOC, 0, "fast-path: workflows/fast.md missing", "")
        return
    fast = read_lines(fast_path)
    fast_no, fast_items = bullets_after(fast, "## Escalation triggers")
    if sorted(fast_items) != sorted(skill_items):
        yield Finding(FAST_DOC, fast_no, "fast-path: escalation list must match "
                      "SKILL.md § Escalation triggers exactly", "")
    size = os.path.getsize(fast_path)
    if size > FAST_DOC_MAX_BYTES:
        yield Finding(FAST_DOC, 0, f"fast-path: {size} bytes > {FAST_DOC_MAX_BYTES}; FAST must stay light", "")
    for no, line in enumerate(fast, 1):
        for ref in DOC_PATH.findall(line):
            if "{" in ref or "<" in ref:
                continue
            if not os.path.exists(os.path.join(root, ref)):
                yield Finding(FAST_DOC, no, f"fast-path: points at missing file {ref}", "")
    stage2 = section(read_lines(os.path.join(root, "refs/stage-contracts.md")),
                     "## Stage 2 — Requirements", "## Stage 2.5")
    if not any("approval_source" in l for _, l in stage2):
        yield Finding("refs/stage-contracts.md", stage2[0][0] if stage2 else 0,
                      "fast-path: Stage 2 must record approval_source", "")


SESSION_SCHEMA_HEADING = re.compile(r"^#+ .*`session\.json` schema")


def check_single_session_schema(root: str) -> Iterable[Finding]:
    """The session.json schema lives only in refs/contracts-and-artifacts.md."""
    for path in scanned_files(root):
        rel_path = rel(root, path)
        if rel_path == "refs/contracts-and-artifacts.md":
            continue
        for no, line in enumerate(read_lines(path), 1):
            if SESSION_SCHEMA_HEADING.match(line):
                yield Finding(rel_path, no, "session-schema: one schema only, in "
                              "refs/contracts-and-artifacts.md § session.json", line.strip())


PINNED_MODEL = re.compile(r"\bclaude-(?:haiku|sonnet|opus)[\w.-]*\d", re.I)
VERSIONED_MODEL = re.compile(r"\b(?:Haiku|Sonnet|Opus)\s*\d")
OTHER_HOST = re.compile(r"\b(?:Cursor|Codex)\b")
MODEL_TIERS = ("`default`", "`deep-reasoning`")


def check_model_routing(root: str) -> Iterable[Finding]:
    """PR8b / ADR-0001 decision 5: Claude Code only; no pinned IDs or versioned
    model names; `default` everywhere, `deep-reasoning` only for governed."""
    for path in scanned_files(root):
        rel_path = rel(root, path)
        for no, line in enumerate(read_lines(path), 1):
            low = line.lower()
            if PINNED_MODEL.search(line) or VERSIONED_MODEL.search(line):
                yield Finding(rel_path, no, "model-routing: use the `default` / `deep-reasoning` "
                              "tiers, not a model ID or versioned name", line.strip())
            if OTHER_HOST.search(line) and "not supported" not in low and "unsupported" not in low:
                yield Finding(rel_path, no, "model-routing: Claude Code only (ADR-0001); other hosts "
                              "may only be mentioned as not supported", line.strip())
    lines = read_lines(os.path.join(root, "SKILL.md"))
    routing = section(lines, "## Model routing", "## ")
    if not routing:
        yield Finding("SKILL.md", 0, "model-routing: `## Model routing` section missing", "")
        return
    text = "\n".join(l for _, l in routing)
    for tier in MODEL_TIERS:
        if tier not in text:
            yield Finding("SKILL.md", routing[0][0], f"model-routing: tier {tier} not defined", "")
    for no, line in routing:
        cells = [c.strip() for c in line.split("|")]
        is_stage_row = len(cells) > 4 and (cells[1][:1].isdigit() or cells[1].startswith("-1"))
        if is_stage_row:
            tier = cells[3]
            if "deep-reasoning" in tier:
                yield Finding("SKILL.md", no, "model-routing: the default tier column must be "
                              "`default`; step up only in the governed column", line.strip())
            step_up = cells[4]
            if "deep-reasoning" in step_up and "governed" not in step_up:
                yield Finding("SKILL.md", no, "model-routing: `deep-reasoning` only when `governed`",
                              line.strip())


OLD_COMMIT_DEFAULT = re.compile(r"default(?:s to)?\s+`?per_task", re.I)
FIGMA_FLOOR = re.compile(r"Jira (?:ticket )?\+ Figma.*(?:→|->)\s*(?:minimum|min)", re.I)


def check_delivery_workflow(root: str) -> Iterable[Finding]:
    """ADR-0002: aligned with the team Mobile AI Delivery Workflow v0.4 — the Dev
    commits (default no_commit), behaviour changes in sensitive areas are
    governed (no Jira+Figma floor), standard/governed get an Independent
    Reviewer at Stage 6, and the agent never pushes the product repo."""
    for path in scanned_files(root):
        rel_path = rel(root, path)
        for no, line in enumerate(read_lines(path), 1):
            if "commit_policy" in line and OLD_COMMIT_DEFAULT.search(line):
                yield Finding(rel_path, no, "delivery-workflow: commit_policy defaults to "
                              "`no_commit` (the Dev commits)", line.strip())
            if FIGMA_FLOOR.search(line):
                yield Finding(rel_path, no, "delivery-workflow: Jira + Figma is not a mode floor; "
                              "an S UI tweak with Figma may be `fast`", line.strip())
    schema = read_lines(os.path.join(root, "refs/contracts-and-artifacts.md"))
    if not any('"commit_policy"' in l and "default no_commit" in l for l in schema):
        yield Finding("refs/contracts-and-artifacts.md", 0,
                      "delivery-workflow: session schema must default commit_policy to no_commit", "")
    skill = "\n".join(read_lines(os.path.join(root, "SKILL.md")))
    for needle, why in (("### Governed triggers", "`### Governed triggers` section missing"),
                        ("### Team tiers", "S/M/L → mode mapping (`### Team tiers`) missing"),
                        ("**Never push the product repo.**", "hard rule 'Never push the product repo' missing"),
                        ("Independent Reviewer", "Stage 6 must name the Independent Reviewer")):
        if needle not in skill:
            yield Finding("SKILL.md", 0, f"delivery-workflow: {why}", "")
    stage6 = section(read_lines(os.path.join(root, "refs/stage-contracts.md")),
                     "## Stage 6 — QA Gate", "## Stage 7")
    if not any("Independent Reviewer" in l for _, l in stage6):
        yield Finding("refs/stage-contracts.md", stage6[0][0] if stage6 else 0,
                      "delivery-workflow: Stage 6 contract must run the Independent Reviewer", "")
    agents = "\n".join(read_lines(os.path.join(root, "refs/sub-agents.md")))
    if "### Independent Reviewer" not in agents:
        yield Finding("refs/sub-agents.md", 0,
                      "delivery-workflow: `### Independent Reviewer` worker missing", "")


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
    check_skipped_stage, check_read_phase_git, check_team_docs_lifecycle,
    check_tdd_exemptions, check_fast_path, check_single_session_schema, check_model_routing,
    check_delivery_workflow, check_versions,
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
