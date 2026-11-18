#!/usr/bin/env python3
"""Pilot report for the Android Agent Orchestrator (PR8c, ADR-0001 decision 7).

Reads telemetry records (`retro-log.jsonl`, schema `aao-telemetry/1`, defined in
refs/contracts-and-artifacts.md § retro-log.jsonl), validates them, computes the
policy bytes each task read from the skill pack (at the recorded skill commit
when possible), and compares the `baseline` and `candidate` cohorts per
workflow mode against the ADR-0001 pilot hypotheses.

  python3 scripts/pilot_report.py [--json] [--skill-root PATH] retro-log.jsonl...

Records with unknown fields are rejected, so task content (briefs, code,
diffs) cannot slip into the report. Nothing here reads or prints secrets.
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCHEMA = "aao-telemetry/1"
FIELDS = (
    "schema", "task_id", "skill_version", "skill_commit", "cohort", "workflow_mode",
    "mode_upgrades", "ref_tier", "approval_source", "policy_reads", "human_interrupts",
    "started_at", "first_patch_at", "closed_at", "tokens", "model_tiers", "evidence",
    "outcome", "review_iterations", "escaped_defects",
)
MODES = ("fast", "standard", "governed")
COHORTS = ("baseline", "candidate")
TIERS = ("LIGHT", "MEDIUM", "HEAVY", "FULL")
INTERRUPT_KINDS = ("approval", "scope_confirmation", "exemption_confirm", "escalation",
                   "clarification", "blocker", "other")
TOKEN_SOURCES = ("host_usage", "manual", "unavailable")
OUTCOMES = ("closed", "abandoned")

# ADR-0001 decision 7 — pilot hypotheses, not acceptance criteria.
MIN_SAMPLES = {"fast": 5, "standard": 5, "governed": 3}
LEAD_TIME_REDUCTION = 0.20
COST_REDUCTION = 0.15
FAST_POLICY_KB = 15.0


class UnknownPolicyFile(Exception):
    pass


# ── Validation ───────────────────────────────────────────────────────────────

def parse_ts(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def safe_rel(path: Any) -> bool:
    if not isinstance(path, str) or not path:
        return False
    norm = os.path.normpath(path)
    return not (os.path.isabs(norm) or norm == ".." or norm.startswith(".." + os.sep))


def is_int_or_none(value: Any) -> bool:
    return value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 0)


def validate(rec: Any) -> List[str]:
    if not isinstance(rec, dict):
        return ["record is not a JSON object"]
    errors = [f"missing field: {f}" for f in FIELDS if f not in rec]
    errors += [f"unknown field: {k}" for k in rec if k not in FIELDS]
    if errors:
        return errors
    checks: List[Tuple[bool, str]] = [
        (rec["schema"] == SCHEMA, f"schema must be {SCHEMA}"),
        (isinstance(rec["task_id"], str) and rec["task_id"], "task_id must be a non-empty string"),
        (rec["cohort"] in COHORTS + (None,), "cohort must be baseline, candidate or null"),
        (rec["workflow_mode"] in MODES, "workflow_mode must be fast, standard or governed"),
        (rec["ref_tier"] in TIERS, "ref_tier must be LIGHT, MEDIUM, HEAVY or FULL"),
        (rec["outcome"] in OUTCOMES, "outcome must be closed or abandoned"),
        (parse_ts(rec["started_at"]) is not None, "started_at must be an ISO timestamp"),
        (parse_ts(rec["closed_at"]) is not None, "closed_at must be an ISO timestamp"),
        (rec["first_patch_at"] is None or parse_ts(rec["first_patch_at"]) is not None,
         "first_patch_at must be an ISO timestamp or null"),
        (is_int_or_none(rec["review_iterations"]), "review_iterations must be a count or null"),
        (is_int_or_none(rec["escaped_defects"]), "escaped_defects must be a count or null"),
        (isinstance(rec["mode_upgrades"], list) and all(isinstance(x, str) for x in rec["mode_upgrades"]),
         "mode_upgrades must be a list of strings"),
    ]
    errors += [msg for ok, msg in checks if not ok]
    reads = rec["policy_reads"]
    if not isinstance(reads, list) or not all(
            isinstance(r, dict) and set(r) == {"path", "section"} and safe_rel(r["path"])
            and (r["section"] is None or isinstance(r["section"], str)) for r in reads):
        errors.append("policy_reads must be [{path (inside the pack), section|null}]")
    interrupts = rec["human_interrupts"]
    if not isinstance(interrupts, list) or not all(
            isinstance(i, dict) and set(i) == {"stage_id", "kind"} and isinstance(i["stage_id"], str)
            and i["kind"] in INTERRUPT_KINDS for i in interrupts):
        errors.append(f"human_interrupts must be [{{stage_id, kind}}] with kind in {INTERRUPT_KINDS}")
    tokens = rec["tokens"]
    if not (isinstance(tokens, dict) and set(tokens) == {"input", "output", "cached", "source"}
            and all(is_int_or_none(tokens[k]) for k in ("input", "output", "cached"))
            and tokens["source"] in TOKEN_SOURCES):
        errors.append("tokens must be {input, output, cached: count|null, source}")
    evidence = rec["evidence"]
    if not (isinstance(evidence, dict) and set(evidence) == {"pass", "fail", "not_run", "blocked"}
            and all(is_int_or_none(v) and v is not None for v in evidence.values())):
        errors.append("evidence must be {pass, fail, not_run, blocked} counts")
    tiers = rec["model_tiers"]
    if not (isinstance(tiers, dict) and set(tiers) <= {"default", "deep-reasoning"}
            and all(is_int_or_none(v) and v is not None for v in tiers.values())):
        errors.append("model_tiers must be {default, deep-reasoning} stage counts")
    for key in ("approval_source", "skill_version", "skill_commit"):
        if rec[key] is not None and not isinstance(rec[key], str):
            errors.append(f"{key} must be a string or null")
    return errors


# ── Policy bytes ─────────────────────────────────────────────────────────────

def read_pack_file(root: str, path: str, commit: Optional[str]) -> str:
    if commit:
        proc = subprocess.run(["git", "-C", root, "show", f"{commit}:{path}"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            return proc.stdout
    full = os.path.join(root, path)
    if not os.path.isfile(full):
        raise UnknownPolicyFile(f"{path} not found in the skill pack")
    with open(full, encoding="utf-8", errors="replace") as f:
        return f.read()


def heading_level(line: str) -> int:
    stripped = line.lstrip()
    level = len(stripped) - len(stripped.lstrip("#"))
    return level if level and stripped[level:level + 1] == " " else 0


def section_text(content: str, section: str, path: str) -> str:
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        level = heading_level(line)
        if level and line.strip().lstrip("#").strip() == section:
            out = [line]
            for nxt in lines[i + 1:]:
                nxt_level = heading_level(nxt)
                if nxt_level and nxt_level <= level:
                    break
                out.append(nxt)
            return "".join(out)
    raise UnknownPolicyFile(f"section '{section}' not found in {path}")


def policy_bytes(reads: Sequence[Dict[str, Any]], root: str, commit: Optional[str]) -> int:
    total = 0
    for read in reads:
        content = read_pack_file(root, read["path"], commit)
        if read["section"]:
            content = section_text(content, read["section"], read["path"])
        total += len(content.encode("utf-8"))
    return total


# ── Metrics and comparison ───────────────────────────────────────────────────

def hours_between(start: Any, end: Any) -> Optional[float]:
    a, b = parse_ts(start), parse_ts(end)
    return (b - a).total_seconds() / 3600 if a and b else None


def metrics(rec: Dict[str, Any], root: str) -> Dict[str, Any]:
    tokens = rec["tokens"]
    total = (tokens["input"] + tokens["output"]
             if tokens["source"] != "unavailable" and tokens["input"] is not None
             and tokens["output"] is not None else None)
    return {
        "cycle_h": hours_between(rec["started_at"], rec["closed_at"]),
        "ttfp_h": hours_between(rec["started_at"], rec["first_patch_at"]),
        "interrupts": len(rec["human_interrupts"]),
        "policy_kb": policy_bytes(rec["policy_reads"], root, rec["skill_commit"]) / 1000,
        "tokens": total,
        "escaped_defects": rec["escaped_defects"],
    }


def median(values: Sequence[Optional[float]]) -> Optional[float]:
    known = [v for v in values if v is not None]
    return round(statistics.median(known), 3) if known else None


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    defects = [r["escaped_defects"] for r in rows if r["escaped_defects"] is not None]
    return {
        "n": len(rows),
        "median_cycle_h": median([r["cycle_h"] for r in rows]),
        "median_ttfp_h": median([r["ttfp_h"] for r in rows]),
        "median_interrupts": median([r["interrupts"] for r in rows]),
        "median_policy_kb": median([r["policy_kb"] for r in rows]),
        "median_tokens": median([r["tokens"] for r in rows]),
        "tokens_n": sum(1 for r in rows if r["tokens"] is not None),
        "escaped_defects": sum(defects),
        "escaped_defects_n": len(defects),
    }


def reduction(base: Optional[float], cand: Optional[float]) -> Optional[float]:
    if base is None or cand is None or base == 0:
        return None
    return round(1 - cand / base, 3)


def verdict_reduction(base: Dict[str, Any], cand: Dict[str, Any], key: str, n_key: str,
                      minimum: int, target: float) -> Dict[str, Any]:
    delta = reduction(base[key], cand[key])
    if base[n_key] < minimum or cand[n_key] < minimum or delta is None:
        verdict = "insufficient data"
    else:
        verdict = "met" if delta >= target else "not met"
    return {"baseline": base[key], "candidate": cand[key], "reduction": delta,
            "target": f">= {int(target * 100)}% lower", "verdict": verdict}


def compare(mode: str, base: Dict[str, Any], cand: Dict[str, Any]) -> Dict[str, Any]:
    minimum = MIN_SAMPLES[mode]
    enough = base["n"] >= minimum and cand["n"] >= minimum
    out = {
        "lead_time": verdict_reduction(base, cand, "median_cycle_h", "n", minimum, LEAD_TIME_REDUCTION),
        "cost": verdict_reduction(base, cand, "median_tokens", "tokens_n", minimum, COST_REDUCTION),
    }
    if mode == "fast":
        kb = cand["median_policy_kb"]
        out["policy_kb"] = {"baseline": base["median_policy_kb"], "candidate": kb,
                            "target": f"<= {FAST_POLICY_KB:g} KB",
                            "verdict": "insufficient data" if not enough or kb is None
                            else ("met" if kb <= FAST_POLICY_KB else "not met")}
    defects_known = base["escaped_defects_n"] >= minimum and cand["escaped_defects_n"] >= minimum
    base_rate = base["escaped_defects"] / base["escaped_defects_n"] if base["escaped_defects_n"] else None
    cand_rate = cand["escaped_defects"] / cand["escaped_defects_n"] if cand["escaped_defects_n"] else None
    out["escaped_defects"] = {
        "baseline": base_rate, "candidate": cand_rate, "target": "not higher than baseline",
        "verdict": "insufficient data" if not defects_known or base_rate is None or cand_rate is None
        else ("met" if cand_rate <= base_rate else "not met")}
    return out


def load(paths: Sequence[str], root: str) -> Tuple[List[Tuple[Dict[str, Any], Dict[str, Any]]], List[Dict[str, Any]]]:
    good: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    bad: List[Dict[str, Any]] = []
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as f:
            for no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                where = f"{os.path.basename(path)}:{no}"
                try:
                    rec = json.loads(line)
                except ValueError:
                    bad.append({"line": where, "errors": ["not valid JSON"]})
                    continue
                errors = validate(rec)
                if not errors:
                    try:
                        good.append((rec, metrics(rec, root)))
                        continue
                    except UnknownPolicyFile as exc:
                        errors = [str(exc)]
                bad.append({"line": where, "task_id": rec.get("task_id") if isinstance(rec, dict) else None,
                            "errors": errors})
    return good, bad


def build_report(paths: Sequence[str], root: str) -> Dict[str, Any]:
    good, bad = load(paths, root)
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for rec, m in good:
        if rec["outcome"] != "closed":
            continue
        buckets.setdefault(f"{rec['cohort'] or 'none'}/{rec['workflow_mode']}", []).append(m)
    groups = {key: summarize(rows) for key, rows in sorted(buckets.items())}
    comparison = {mode: compare(mode, groups[f"baseline/{mode}"], groups[f"candidate/{mode}"])
                  for mode in MODES if f"baseline/{mode}" in groups and f"candidate/{mode}" in groups}
    return {"valid": len(good), "invalid": bad, "groups": groups, "comparison": comparison,
            "hypotheses": "ADR-0001 decision 7 — pilot hypotheses, not acceptance criteria"}


# ── Rendering ────────────────────────────────────────────────────────────────

def fmt(value: Any) -> str:
    if value is None:
        return "—"
    return f"{value:.3g}" if isinstance(value, float) else str(value)


def to_markdown(report: Dict[str, Any]) -> str:
    lines = ["# Pilot report", "", f"_{report['hypotheses']}_", "",
             f"Valid records: {report['valid']} · invalid: {len(report['invalid'])}", "",
             "## Groups (closed tasks)", "",
             "| cohort/mode | n | cycle h | first patch h | interrupts | policy KB | tokens (n) | escaped defects |",
             "|---|---|---|---|---|---|---|---|"]
    for key, g in report["groups"].items():
        lines.append(f"| {key} | {g['n']} | {fmt(g['median_cycle_h'])} | {fmt(g['median_ttfp_h'])} | "
                     f"{fmt(g['median_interrupts'])} | {fmt(g['median_policy_kb'])} | "
                     f"{fmt(g['median_tokens'])} ({g['tokens_n']}) | {g['escaped_defects']} |")
    lines += ["", "## Hypotheses (candidate vs baseline, medians)", "",
              "| mode | metric | baseline | candidate | target | verdict |", "|---|---|---|---|---|---|"]
    names = {"lead_time": "lead time", "cost": "cost (tokens)", "policy_kb": "policy KB read",
             "escaped_defects": "escaped defects / task"}
    for mode, metrics_ in report["comparison"].items():
        for key, row in metrics_.items():
            lines.append(f"| {mode} | {names[key]} | {fmt(row['baseline'])} | {fmt(row['candidate'])} | "
                         f"{row['target']} | {row['verdict']} |")
    if not report["comparison"]:
        lines.append("| — | no mode has both a baseline and a candidate cohort yet | | | | |")
    if report["invalid"]:
        lines += ["", "## Invalid records (excluded)", ""]
        lines += [f"- {b['line']}: {'; '.join(b['errors'])}" for b in report["invalid"]]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str]) -> int:
    args = list(argv)
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if "--skill-root" in args:
        i = args.index("--skill-root")
        if i + 1 >= len(args):
            print("--skill-root needs a path", file=sys.stderr)
            return 2
        root, args = os.path.abspath(args[i + 1]), args[:i] + args[i + 2:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    report = build_report(args, root)
    sys.stdout.write(json.dumps(report, indent=2) + "\n" if as_json else to_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
