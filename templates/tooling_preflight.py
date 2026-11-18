#!/usr/bin/env python3
"""Android Agent Orchestrator — Tooling Preflight core.

Single implementation behind `templates/tooling-preflight.sh`. All checks are
collected once into a facts dict, then rendered as Markdown (default) or JSON
(`--json`), so both formats always report the same facts.

Audit only: never installs, updates, deletes, or rebuilds anything, and never
prints token values from `.agent-auth.yaml`.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from importlib import metadata
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

AUTH_FILE = ".agent-auth.yaml"
CACHE_PATH = ".project-orchestration/memory/tooling-cache.json"
TASKS_DIR = ".project-orchestration/tasks"
# Written by pre-6.1.x versions; reported as a resume candidate, never used.
LEGACY_SESSION_PATH = ".project-orchestration/memory/session.json"
PLUGINS_DIR = ".claude/plugins"
CMD_TIMEOUT_S = 10
PLUGIN_SEARCH_DEPTH = 3

Facts = Dict[str, Any]

# (json key, display name, help-text needles)
ANDROID_COMMANDS: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("docs_search", "android docs search", ("docs", "search")),
    ("docs_fetch", "android docs fetch", ("docs", "fetch")),
    ("screen_capture_annotate", "android screen capture --annotate", ("screen", "capture")),
    ("layout", "android layout", ("layout",)),
    ("run", "android run", ("run",)),
)
STUDIO_COMMANDS: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("version_lookup", "android studio version-lookup", ("version-lookup",)),
    ("render_compose_preview", "android studio render-compose-preview", ("render-compose-preview",)),
    ("analyze_file", "android studio analyze-file", ("analyze-file",)),
    ("find_declaration", "android studio find-declaration", ("find-declaration",)),
    ("find_usages", "android studio find-usages", ("find-usages",)),
)
TOKEN_KEYS: Tuple[Tuple[str, str, str], ...] = (
    # (json key, yaml section, yaml key)
    ("atlassian_token", "atlassian", "api_token"),
    ("figma_token", "figma", "personal_access_token"),
    ("github_token", "github", "personal_access_token"),
)


# ── Low-level helpers ────────────────────────────────────────────────────────

def run_command(argv: Sequence[str]) -> Tuple[int, str]:
    """Run argv without a shell. Returns (exit code, stdout+stderr); -1 on failure."""
    try:
        proc = subprocess.run(list(argv), capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=CMD_TIMEOUT_S)
        return proc.returncode, (proc.stdout or "") + "\n" + (proc.stderr or "")
    except (OSError, ValueError, subprocess.SubprocessError):
        return -1, ""


def first_lines(text: str, limit: int) -> List[str]:
    return [line for line in text.splitlines() if line.strip()][:limit]


def help_support(help_text: str, needles: Sequence[str]) -> str:
    if not help_text.strip():
        return "unknown"
    low = help_text.lower()
    return "supported" if all(n.lower() in low for n in needles) else "missing"


def find_named(root: str, needle: str, max_depth: int) -> List[str]:
    """Paths under root (≤ max_depth levels) whose basename contains needle."""
    if not os.path.isdir(root):
        return []
    hits: List[str] = []
    base_depth = root.rstrip(os.sep).count(os.sep)
    for current, dirs, files in os.walk(root):
        depth = current.count(os.sep) - base_depth
        if depth >= max_depth:
            dirs[:] = []
        for name in sorted(dirs + files):
            if needle in name.lower():
                hits.append(os.path.join(current, name))
    return hits


def read_json(path: str) -> Tuple[bool, Optional[dict]]:
    """(present, data). data is None when present but unreadable/not an object."""
    if not os.path.isfile(path):
        return False, None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return True, data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return True, None


# ── Auth ─────────────────────────────────────────────────────────────────────

def yaml_section_key(content: str, section: str, key: str) -> Optional[str]:
    """Value of section.key in a 2-level YAML file.

    Returns '' when present but empty, None when absent. Skips blank and
    comment lines and strips inline comments. Never returns the value to the
    caller's output — callers only map it through token_status().
    """
    current_section: Optional[str] = None
    for raw in content.splitlines():
        stripped = raw.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw[0].isspace():
            current_section = stripped.split(":", 1)[0].strip() if ":" in stripped else None
            continue
        if current_section != section:
            continue
        name, sep, value = stripped.partition(":")
        if sep and name.strip() == key:
            value = value.strip()
            if " #" in value:
                value = value[: value.index(" #")].strip()
            return value.strip("\"'")
    return None


def token_status(value: Optional[str]) -> str:
    if value is None:
        return "missing_key"
    return "set" if value else "empty"


def unknown_auth(file_state: str) -> Facts:
    return {"file": file_state, "tokens": {k: "unknown" for k, _, _ in TOKEN_KEYS}}


def check_auth() -> Facts:
    if not os.path.isfile(AUTH_FILE):
        return unknown_auth("missing")
    try:
        with open(AUTH_FILE, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        # Never surface the raw bytes or the decode error (it can quote content).
        return unknown_auth("unreadable")
    tokens = {k: token_status(yaml_section_key(content, sec, key)) for k, sec, key in TOKEN_KEYS}
    return {"file": "present", "tokens": tokens}


# ── Tools ────────────────────────────────────────────────────────────────────

def check_android() -> Facts:
    cli = shutil.which("android")
    adb = shutil.which("adb")
    if not cli:
        missing = {k: "missing" for k, _, _ in ANDROID_COMMANDS}
        studio_missing = {k: "missing" for k, _, _ in STUDIO_COMMANDS}
        return {"cli": None, "adb": adb, "info": [], "skills": [],
                "commands": missing, "studio_commands": studio_missing}
    _, android_help = run_command([cli, "--help"])
    _, studio_help = run_command([cli, "studio", "--help"])
    _, info = run_command([cli, "info"])
    _, skills = run_command([cli, "skills", "list", "--long"])
    return {
        "cli": cli,
        "adb": adb,
        "info": first_lines(info, 5),
        "skills": first_lines(skills, 20),
        "commands": {k: help_support(android_help, n) for k, _, n in ANDROID_COMMANDS},
        "studio_commands": {k: help_support(studio_help, n) for k, _, n in STUDIO_COMMANDS},
    }


def graphify_package_version() -> Optional[str]:
    try:
        return metadata.version("graphifyy")
    except metadata.PackageNotFoundError:
        return None


def check_architecture_map() -> Facts:
    ua_plugin = find_named(PLUGINS_DIR, "understand-anything", PLUGIN_SEARCH_DEPTH)
    ua_graph = os.path.isfile(".understand-anything/knowledge-graph.json")
    graphify_cli = shutil.which("graphify")
    graphify_pkg = graphify_package_version()
    report = os.path.isfile("graphify-out/GRAPH_REPORT.md")
    graph_json = os.path.isfile("graphify-out/graph.json")
    if ua_plugin or ua_graph:
        active = "understand-anything"
    elif graphify_cli or graphify_pkg or report or graph_json:
        active = "graphify"
    else:
        active = "none"
    return {"ua_plugin": ua_plugin, "ua_graph": ua_graph, "graphify_cli": graphify_cli,
            "graphify_pkg": graphify_pkg, "report": report, "graph_json": graph_json,
            "active": active}


def check_karpathy() -> Facts:
    claude_md = os.path.isfile("CLAUDE.md")
    in_claude_md = False
    if claude_md:
        try:
            with open("CLAUDE.md", encoding="utf-8", errors="replace") as f:
                in_claude_md = "karpathy" in f.read().lower()
        except OSError:
            pass
    plugin_hits = find_named(PLUGINS_DIR, "karpathy", PLUGIN_SEARCH_DEPTH)
    if in_claude_md or plugin_hits:
        status = "installed"
    elif claude_md:
        status = "manual"
    else:
        status = "missing"
    return {"claude_md": claude_md, "in_claude_md": in_claude_md,
            "plugin_hits": plugin_hits, "status": status}


# ── Memory ───────────────────────────────────────────────────────────────────

def git_state() -> Facts:
    """work_tree: inside a git work tree; head: HEAD sha or None."""
    git = shutil.which("git")
    if not git:
        return {"work_tree": False, "head": None}
    code, out = run_command([git, "rev-parse", "--is-inside-work-tree"])
    work_tree = code == 0 and out.strip().startswith("true")
    code, out = run_command([git, "rev-parse", "HEAD"])
    head = out.strip().splitlines()[0] if code == 0 and out.strip() else None
    return {"work_tree": work_tree, "head": head}


def cache_freshness(valid_until: Optional[str], now: datetime) -> str:
    if not valid_until:
        return "unknown"
    try:
        expiry = datetime.fromisoformat(str(valid_until).replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return "fresh" if now < expiry else "stale"
    except ValueError:
        return "unparseable"


def cache_status(freshness: str, graph_commit: Any, head: Optional[str]) -> str:
    """Only 'fresh' means reusable: valid TTL AND readable HEAD AND commit == HEAD."""
    if freshness != "fresh":
        return freshness
    if head is None:
        return "head_unavailable"
    if not graph_commit:
        return "no_commit"
    return "fresh" if graph_commit == head else "graph_stale"


def check_cache(now: datetime, head: Optional[str]) -> Facts:
    present, data = read_json(CACHE_PATH)
    if not present:
        return {"present": False, "cache_reusable": False}
    if data is None:
        return {"present": True, "readable": False, "cache_reusable": False}
    valid_until = data.get("valid_until")
    graph_commit = data.get("graph_commit")
    status = cache_status(cache_freshness(valid_until, now), graph_commit, head)
    facts: Facts = {"present": True, "checked_at": data.get("checked_at"),
                    "valid_until": valid_until, "graph_commit": graph_commit}
    if head is not None:
        facts = {**facts, "head_commit": head,
                 "graph_stale": bool(graph_commit) and graph_commit != head}
    return {**facts, "cache_status": status, "cache_reusable": status == "fresh"}


def session_summary(data: dict) -> Facts:
    return {"stage_reached": data.get("stage_reached"), "stage_status": data.get("stage_status")}


def check_sessions() -> Facts:
    """Every tasks/*/session.json is a candidate; never pick one here."""
    tasks: List[Facts] = []
    for path in sorted(glob.glob(os.path.join(TASKS_DIR, "*", "session.json"))):
        dir_id = os.path.basename(os.path.dirname(path))
        _, data = read_json(path)
        if data is None:
            tasks.append({"task_id": dir_id, "readable": False})
        else:
            tasks.append({"task_id": str(data.get("task_id") or dir_id), **session_summary(data)})
    present, data = read_json(LEGACY_SESSION_PATH)
    if not present:
        legacy: Facts = {"present": False}
    elif data is None:
        legacy = {"present": True, "readable": False}
    else:
        legacy = {"present": True, "task_id": data.get("task_id"), **session_summary(data)}
    in_progress = [t["task_id"] for t in tasks if t.get("stage_status") == "in_progress"]
    return {"tasks": tasks, "in_progress": in_progress, "legacy": legacy}


# ── Collection ───────────────────────────────────────────────────────────────

def fallback_android() -> Facts:
    return {"cli": None, "adb": None, "info": [], "skills": [],
            "commands": {k: "unknown" for k, _, _ in ANDROID_COMMANDS},
            "studio_commands": {k: "unknown" for k, _, _ in STUDIO_COMMANDS}}


# name → (check, fallback used when the check raises). A failing check must
# never take the other checks' results down with it.
CHECKS: Dict[str, Tuple[Callable[[], Any], Callable[[], Any]]] = {
    "auth": (check_auth, lambda: unknown_auth("unknown")),
    "android": (check_android, fallback_android),
    "arch": (check_architecture_map, lambda: {
        "ua_plugin": [], "ua_graph": False, "graphify_cli": None, "graphify_pkg": None,
        "report": False, "graph_json": False, "active": "unknown"}),
    "karpathy": (check_karpathy, lambda: {
        "claude_md": False, "in_claude_md": False, "plugin_hits": [], "status": "unknown"}),
    "git": (git_state, lambda: {"work_tree": False, "head": None}),
    "session": (check_sessions, lambda: {"tasks": [], "in_progress": [],
                                         "legacy": {"present": False}, "scan_failed": True}),
}


def guarded(name: str, check: Callable[[], Any], fallback: Callable[[], Any]
            ) -> Tuple[Any, Optional[str]]:
    """Run one check; on any exception return (fallback, error class name).
    Only the exception type is reported — messages may quote file contents."""
    try:
        return check(), None
    except Exception as exc:  # noqa: BLE001 — isolation boundary by design
        return fallback(), f"{name}: {type(exc).__name__}"


def collect(mode: str) -> Facts:
    now = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=len(CHECKS)) as pool:
        futures = {name: pool.submit(guarded, name, check, fallback)
                   for name, (check, fallback) in CHECKS.items()}
        outcomes = {name: fut.result() for name, fut in futures.items()}
    results = {name: value for name, (value, _) in outcomes.items()}
    errors = [err for _, err in outcomes.values() if err]
    cache, cache_err = guarded("cache", lambda: check_cache(now, results["git"]["head"]),
                               lambda: {"present": True, "readable": False, "cache_reusable": False})
    return {
        "mode": mode,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cwd": os.getcwd(),
        **results,
        "cache": cache,
        "check_errors": errors + ([cache_err] if cache_err else []),
    }


def gaps(facts: Facts) -> Tuple[List[str], List[str]]:
    """(blocking, non_blocking) at tooling scope.

    Blocking here covers only what the script can decide on its own. Task-level
    blocking rules (refs/provisioning-preflight.md § Blocking rules) are applied
    by the agent when it writes preflight.md — see readiness_scope.
    """
    blocking: List[str] = []
    if not facts["git"]["work_tree"]:
        blocking.append("not_a_git_work_tree")
    warn: List[str] = []
    if facts["auth"]["file"] in ("missing", "unreadable"):
        warn.append(f"auth_file_{facts['auth']['file']}")
    if not facts["android"]["cli"]:
        warn.append("android_cli_missing")
    arch = facts["arch"]
    if arch["active"] == "none":
        warn.append("architecture_map_missing")
    elif arch["active"] == "understand-anything" and not arch["ua_graph"]:
        warn.append("architecture_map_graph_missing")
    elif arch["active"] == "graphify" and not arch["report"]:
        warn.append("architecture_map_graph_missing")
    if facts["karpathy"]["status"] == "missing":
        warn.append("karpathy_missing")
    session = facts["session"]
    if len(session["in_progress"]) > 1:
        warn.append("multiple_in_progress_sessions")
    warn.extend(f"session_unreadable:{t['task_id']}" for t in session["tasks"]
                if t.get("readable") is False)
    if session["legacy"]["present"]:
        warn.append("legacy_session_path")
    warn.extend(f"check_failed:{err.split(':')[0]}" for err in facts["check_errors"])
    return blocking, warn


# ── Rendering ────────────────────────────────────────────────────────────────

def present(value: Any) -> str:
    return "present" if value else "missing"


def to_json(facts: Facts) -> Facts:
    blocking, warn = gaps(facts)
    android, arch, cache = facts["android"], facts["arch"], facts["cache"]
    cache_out = {k: v for k, v in cache.items() if k != "checked_at"}
    return {
        "timestamp": facts["timestamp"],
        "mode": facts["mode"],
        "ready_for_stage_0": not blocking,
        "readiness_scope": "tooling",
        "blocking_gaps": blocking,
        "non_blocking_gaps": warn,
        "tools": {
            "auth_file": facts["auth"]["file"],
            **facts["auth"]["tokens"],
            "android_cli": present(android["cli"]),
            "adb": present(android["adb"]),
            "android_commands": android["commands"],
            "android_studio_commands": android["studio_commands"],
            "understand_anything": present(arch["ua_plugin"]),
            "graphify_cli": present(arch["graphify_cli"]),
            "graphify_package": present(arch["graphify_pkg"]),
            "karpathy": facts["karpathy"]["status"],
        },
        "architecture_map": {
            "active_tool": arch["active"],
            "understand_anything_graph_present": arch["ua_graph"],
            "graphify_report_present": arch["report"],
            "graphify_json_present": arch["graph_json"],
        },
        "cache": cache_out,
        "session": facts["session"],
        "check_errors": facts["check_errors"],
    }


def md_auth(auth: Facts) -> List[str]:
    file_line = {
        "missing": "- .agent-auth.yaml: missing (will be auto-created on first run)",
        "unreadable": "- .agent-auth.yaml: unreadable (not valid UTF-8 or no read permission)",
    }.get(auth["file"], f"- .agent-auth.yaml: {auth['file']}")
    lines = [file_line]
    labels = {k: f"{sec}.{key}" for k, sec, key in TOKEN_KEYS}
    return lines + [f"- {labels[k]}: {v}" for k, v in auth["tokens"].items()]


def md_android(android: Facts, mode: str) -> List[str]:
    adb_line = f"- adb: present ({android['adb']})" if android["adb"] else "- adb: missing"
    if not android["cli"]:
        lines = ["- android CLI: missing"]
        if mode == "audit":
            lines.append("- action: report only (audit mode)")
        return lines + [adb_line]
    names = {k: name for k, name, _ in ANDROID_COMMANDS + STUDIO_COMMANDS}
    supported = {**android["commands"], **android["studio_commands"]}
    return ([f"- android CLI: present ({android['cli']})"]
            + [f"  {line}" for line in android["info"]]
            + ["- command discovery:"]
            + [f"  - {names[k]}: {v}" for k, v in supported.items()]
            + [adb_line])


def md_skills(android: Facts) -> List[str]:
    if not android["cli"]:
        return ["- skipped: android CLI missing"]
    return ["- android skills list:"] + [f"  {line}" for line in android["skills"]]


def md_understand(arch: Facts) -> List[str]:
    plugin = (f"- plugin: present ({', '.join(arch['ua_plugin'])})"
              if arch["ua_plugin"] else "- plugin: missing")
    return [plugin,
            f"- .understand-anything/knowledge-graph.json: {present(arch['ua_graph'])}",
            f"- active architecture-map tool: {arch['active']}"]


def md_graphify(arch: Facts) -> List[str]:
    cli = (f"- graphify CLI: present ({arch['graphify_cli']})"
           if arch["graphify_cli"] else "- graphify CLI: missing")
    pkg = (f"- graphifyy package: present (v{arch['graphify_pkg']})"
           if arch["graphify_pkg"] else "- graphifyy package: missing")
    return [cli, pkg,
            f"- GRAPH_REPORT.md: {present(arch['report'])}",
            f"- graph.json: {present(arch['graph_json'])}"]


def md_karpathy(k: Facts) -> List[str]:
    lines = [f"- CLAUDE.md: {present(k['claude_md'])}"]
    if k["claude_md"]:
        lines.append(f"- Karpathy in CLAUDE.md: {'found' if k['in_claude_md'] else 'not found'}")
    if k["plugin_hits"]:
        lines.append(f"- Plugin found: {', '.join(k['plugin_hits'])}")
    lines.append(f"- Karpathy: {k['status']}")
    if k["status"] != "installed":
        lines.append("- (principles will be applied manually)")
    return lines


def md_cache(cache: Facts) -> List[str]:
    if not cache["present"]:
        return ["- tooling-cache.json: missing (fresh check required)", "- cache_reusable: false"]
    if cache.get("readable") is False:
        return ["- tooling-cache.json: present", "- cache: unreadable", "- cache_reusable: false"]
    lines = ["- tooling-cache.json: present",
             f"- cached_at: {cache.get('checked_at') or '?'}",
             f"- valid_until: {cache.get('valid_until') or '?'}",
             f"- graph_commit: {cache.get('graph_commit') or '?'}"]
    if cache.get("head_commit") and cache.get("graph_commit"):
        verdict = (f"stale ({str(cache['graph_commit'])[:8]} != {cache['head_commit'][:8]})"
                   if cache["graph_stale"] else "current")
        lines.append(f"- graph_commit vs HEAD: {verdict}")
    return lines + [f"- cache_status: {cache['cache_status']}",
                    f"- cache_reusable: {str(cache['cache_reusable']).lower()}"]


def md_task(task: Facts) -> str:
    if task.get("readable") is False:
        return f"  - {task['task_id']}: unreadable"
    return f"  - {task['task_id']}: stage {task.get('stage_reached', '?')}, {task.get('stage_status') or '?'}"


def md_sessions(session: Facts) -> List[str]:
    tasks = session["tasks"]
    if not tasks:
        lines = ["- task sessions: none"]
    else:
        active = ", ".join(session["in_progress"]) or "none"
        lines = [f"- task sessions: {len(tasks)} (in_progress: {active})"] + [md_task(t) for t in tasks]
    if len(session["in_progress"]) > 1:
        lines.append("- several tasks are in progress: ask the human which one to resume")
    legacy = session["legacy"]
    if legacy["present"]:
        detail = ("unreadable" if legacy.get("readable") is False else
                  f"task {legacy.get('task_id')}, stage {legacy.get('stage_reached')}, "
                  f"{legacy.get('stage_status')}")
        lines.append(f"- legacy memory/session.json: present ({detail}) — resume candidate; "
                     "move to tasks/{task_id}/ after the human confirms the task id")
    return lines


def md_memory(cache: Facts, session: Facts) -> List[str]:
    return md_cache(cache) + md_sessions(session)


def md_summary(report: Facts) -> List[str]:
    blocking = ", ".join(report["blocking_gaps"]) or "none"
    warn = ", ".join(report["non_blocking_gaps"]) or "none"
    return [f"- `ready_for_stage_0`: {str(report['ready_for_stage_0']).lower()}",
            "- readiness_scope: tooling (combine with task-level blocking rules in "
            "refs/provisioning-preflight.md before writing preflight.md)",
            f"- Blocking gaps: {blocking}",
            f"- Non-blocking gaps: {warn}"]


def to_markdown(facts: Facts) -> str:
    sections: List[Tuple[str, List[str]]] = [
        ("Mode", [facts["mode"]]),
        ("Timestamp", [facts["timestamp"]]),
        ("Working directory", [facts["cwd"]]),
        ("Summary", md_summary(to_json(facts))),
        ("Auth", md_auth(facts["auth"])),
        ("Android CLI", md_android(facts["android"], facts["mode"])),
        ("Android skills", md_skills(facts["android"])),
        ("Understand-Anything", md_understand(facts["arch"])),
        ("Graphify", md_graphify(facts["arch"])),
        ("Karpathy", md_karpathy(facts["karpathy"])),
        ("Memory cache", md_memory(facts["cache"], facts["session"])),
        *([("Check errors", [f"- {e}" for e in facts["check_errors"]])]
          if facts["check_errors"] else []),
        ("Decision reminder", [
            "- Default mode is audit.",
            "- Do not install/update/rebuild unless user requested bootstrap, update, "
            "refresh-graph, or force-reinstall.",
            "- Tokens in .agent-auth.yaml are checked just-in-time when each source "
            "reader is activated.",
            "- For machine-readable output: bash templates/tooling-preflight.sh --json",
        ]),
    ]
    body = "\n\n".join(f"## {title}\n" + "\n".join(lines) for title, lines in sections)
    return f"# Tooling Preflight\n\n{body}\n"


# ── Entry point ──────────────────────────────────────────────────────────────

def parse_args(argv: Sequence[str]) -> Tuple[str, bool, bool]:
    mode, as_json, cache_only = "audit", False, False
    for arg in argv:
        if arg == "--json":
            as_json = True
        elif arg == "--cache-check":
            cache_only = True
        else:
            mode = arg
    return mode, as_json, cache_only


def cache_check() -> Facts:
    """Fast path for the Stage -1 cache decision: git + cache only (always JSON)."""
    now = datetime.now(timezone.utc)
    git, _ = guarded("git", git_state, lambda: {"work_tree": False, "head": None})
    cache, _ = guarded("cache", lambda: check_cache(now, git["head"]),
                       lambda: {"present": True, "readable": False, "cache_reusable": False})
    return {"timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "cache": {k: v for k, v in cache.items() if k != "checked_at"}}


def main(argv: Sequence[str]) -> int:
    mode, as_json, cache_only = parse_args(argv)
    # Explicit output encoding: never crash on a non-UTF-8 locale.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if cache_only:
        sys.stdout.write(json.dumps(cache_check(), indent=2) + "\n")
        return 0
    facts = collect(mode)
    output = json.dumps(to_json(facts), indent=2) + "\n" if as_json else to_markdown(facts)
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
