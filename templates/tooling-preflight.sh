#!/usr/bin/env bash
set -u

# Android Agent Orchestrator — Tooling Preflight
# Default: audit only. Does NOT install, update, delete, or rebuild anything.
# All checks run in parallel; results are collected and printed in order.
#
# Usage:
#   bash templates/tooling-preflight.sh                  # audit mode → markdown
#   bash templates/tooling-preflight.sh bootstrap        # bootstrap mode → markdown
#   bash templates/tooling-preflight.sh --json           # audit mode → JSON
#   bash templates/tooling-preflight.sh bootstrap --json # bootstrap mode → JSON

# ── Parse args ────────────────────────────────────────────────────────────────

JSON_MODE=0
MODE="audit"
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=1 ;;
    *)      MODE="$arg" ;;
  esac
done

# ── JSON mode — Python-driven, single pass ────────────────────────────────────

if [ "$JSON_MODE" = "1" ]; then
  MODE_FOR_PY="$MODE"
  python3 - << PYEOF
import json, os, subprocess, sys
from datetime import datetime, timezone

MODE = "$MODE_FOR_PY"

def cmd_ok(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return r.returncode == 0
    except Exception:
        return False

def command_help_text(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return (r.stdout or "") + "\n" + (r.stderr or "")
    except Exception:
        return ""

def support_from_help(help_text, *needles):
    if not help_text.strip():
        return "unknown"
    text = help_text.lower()
    return "supported" if all(n.lower() in text for n in needles) else "missing"

def yaml_section_key(content, section, key):
    """Return the string value of section.key in a 2-level YAML file.
    Returns '' if the key is present but empty, None if the key is absent.
    Skips blank lines and full-line comments; strips inline comments."""
    current_section = None
    for raw in content.splitlines():
        stripped = raw.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        # Top-level key: no leading whitespace
        if raw and not raw[0].isspace() and ':' in stripped:
            current_section = stripped.split(':', 1)[0].strip()
        # Nested key under the target section
        elif current_section == section and raw[0:1].isspace():
            kv = stripped.split(':', 1)
            if len(kv) == 2 and kv[0].strip() == key:
                val = kv[1].strip()
                # Drop inline comment (space + # outside the value)
                if ' #' in val:
                    val = val[:val.index(' #')].strip()
                return val.strip('"\'')   # '' means present-but-empty
    return None   # key not found

def tok_status(val):
    if val is None: return "missing_key"
    if val == "":   return "empty"
    return "set"

result = {
    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "mode": MODE,
    "ready_for_stage_0": False,
    "blocking_gaps": [],
    "non_blocking_gaps": [],
    "tools": {},
    "architecture_map": {},
    "cache": {}
}

t = result["tools"]
gaps_blocking = result["blocking_gaps"]
gaps_warn     = result["non_blocking_gaps"]

# ── Auth ──────────────────────────────────────────────────────────────────────
auth_present = os.path.isfile(".agent-auth.yaml")
t["auth_file"] = "present" if auth_present else "missing"
if auth_present:
    try:
        content = open(".agent-auth.yaml").read()
        t["atlassian_token"] = tok_status(yaml_section_key(content, "atlassian", "api_token"))
        t["figma_token"]     = tok_status(yaml_section_key(content, "figma",     "personal_access_token"))
        t["github_token"]    = tok_status(yaml_section_key(content, "github",    "personal_access_token"))
    except Exception:
        t["atlassian_token"] = "unknown"
        t["figma_token"]     = "unknown"
        t["github_token"]    = "unknown"
else:
    t["atlassian_token"] = "unknown"
    t["figma_token"]     = "unknown"
    t["github_token"]    = "unknown"
    gaps_warn.append("auth_file_missing")

# ── Android CLI ───────────────────────────────────────────────────────────────
android_ok = cmd_ok("command -v android")
t["android_cli"] = "present" if android_ok else "missing"
if not android_ok:
    gaps_warn.append("android_cli_missing")
android_help = command_help_text("android --help") if android_ok else ""
studio_help = command_help_text("android studio --help") if android_ok else ""
t["adb"] = "present" if cmd_ok("command -v adb") else "missing"
t["android_commands"] = {
    "docs_search": support_from_help(android_help, "docs", "search") if android_ok else "missing",
    "docs_fetch": support_from_help(android_help, "docs", "fetch") if android_ok else "missing",
    "screen_capture_annotate": support_from_help(android_help, "screen", "capture") if android_ok else "missing",
    "layout": support_from_help(android_help, "layout") if android_ok else "missing",
    "run": support_from_help(android_help, "run") if android_ok else "missing",
}
t["android_studio_commands"] = {
    "version_lookup": support_from_help(studio_help, "version-lookup") if android_ok else "missing",
    "render_compose_preview": support_from_help(studio_help, "render-compose-preview") if android_ok else "missing",
    "analyze_file": support_from_help(studio_help, "analyze-file") if android_ok else "missing",
    "find_declaration": support_from_help(studio_help, "find-declaration") if android_ok else "missing",
    "find_usages": support_from_help(studio_help, "find-usages") if android_ok else "missing",
}

# ── Understand-Anything (checked first for architecture-map lane) ─────────────
ua_plugin = False
plugins_dir = ".claude/plugins"
if os.path.isdir(plugins_dir):
    for root, dirs, files in os.walk(plugins_dir):
        if any("understand-anything" in name.lower() for name in dirs + files):
            ua_plugin = True
            break
ua_graph = os.path.isfile(".understand-anything/knowledge-graph.json")
t["understand_anything"] = "present" if ua_plugin else "missing"

# ── Graphify (fallback — only decides active_tool if Understand-Anything absent)
graphify_cli = cmd_ok("command -v graphify")
graphify_pkg = cmd_ok("python -m pip show graphifyy 2>/dev/null")
graph_report = os.path.isfile("graphify-out/GRAPH_REPORT.md")
graph_json   = os.path.isfile("graphify-out/graph.json")
t["graphify_cli"]     = "present" if graphify_cli else "missing"
t["graphify_package"] = "present" if graphify_pkg else "missing"

if ua_plugin or ua_graph:
    active_tool = "understand-anything"
elif graphify_cli or graphify_pkg or graph_report or graph_json:
    active_tool = "graphify"
else:
    active_tool = "none"

result["architecture_map"] = {
    "active_tool": active_tool,
    "understand_anything_graph_present": ua_graph,
    "graphify_report_present": graph_report,
    "graphify_json_present": graph_json,
}

if active_tool == "none":
    gaps_warn.append("architecture_map_missing")
elif active_tool == "understand-anything" and not ua_graph:
    gaps_warn.append("architecture_map_graph_missing")
elif active_tool == "graphify" and not graph_report:
    gaps_warn.append("architecture_map_graph_missing")

# ── Karpathy ──────────────────────────────────────────────────────────────────
karpathy = "missing"
if os.path.isfile("CLAUDE.md"):
    try:
        if "karpathy" in open("CLAUDE.md").read().lower():
            karpathy = "installed"
        else:
            karpathy = "manual"
    except Exception:
        pass
if not karpathy == "installed":
    # check .claude/plugins
    plugins_dir = ".claude/plugins"
    if os.path.isdir(plugins_dir):
        for root, dirs, files in os.walk(plugins_dir):
            for f in files:
                if "karpathy" in f.lower():
                    karpathy = "installed"
t["karpathy"] = karpathy
if karpathy == "missing":
    gaps_warn.append("karpathy_missing")

# ── Memory cache ──────────────────────────────────────────────────────────────
cache_path = ".project-orchestration/memory/tooling-cache.json"
cache_present = os.path.isfile(cache_path)
result["cache"]["present"] = cache_present
if cache_present:
    try:
        d = json.load(open(cache_path))
        valid_until  = d.get("valid_until")
        graph_commit = d.get("graph_commit")
        result["cache"]["valid_until"]  = valid_until
        result["cache"]["graph_commit"] = graph_commit

        # Freshness: compare valid_until with now
        cache_status = "unknown"
        if valid_until:
            try:
                exp = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                cache_status = "fresh" if datetime.now(timezone.utc) < exp else "stale"
            except Exception:
                cache_status = "unparseable"

        # Graph staleness: compare graph_commit with git HEAD
        try:
            head = subprocess.run("git rev-parse HEAD", shell=True,
                                  capture_output=True, text=True, timeout=5)
            if head.returncode == 0:
                head_sha = head.stdout.strip()
                result["cache"]["head_commit"] = head_sha
                if graph_commit and graph_commit != head_sha:
                    result["cache"]["graph_stale"] = True
                    if cache_status == "fresh":
                        cache_status = "graph_stale"
                else:
                    result["cache"]["graph_stale"] = False
        except Exception:
            pass

        result["cache"]["cache_status"] = cache_status
    except Exception:
        result["cache"]["readable"] = False

# ── Final decision ────────────────────────────────────────────────────────────
result["ready_for_stage_0"] = len(gaps_blocking) == 0

print(json.dumps(result, indent=2))
PYEOF
  exit $?
fi

# ── Markdown mode (default) ───────────────────────────────────────────────────

TMPDIR_PREFIX="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_PREFIX"' EXIT

echo "# Tooling Preflight"
echo
echo "## Mode"
echo "$MODE"
echo
echo "## Timestamp"
date -u +"%Y-%m-%dT%H:%M:%SZ"
echo
echo "## Working directory"
pwd

# ── Helpers ───────────────────────────────────────────────────────────────────

write_section() {
  local name="$1"
  local file="$TMPDIR_PREFIX/$2"
  echo
  echo "## $name"
  cat "$file" 2>/dev/null || echo "- (no output)"
}

# ── Parallel checks ───────────────────────────────────────────────────────────

# ① Auth
(
  out="$TMPDIR_PREFIX/auth"
  if [ -f ".agent-auth.yaml" ]; then
    echo "- .agent-auth.yaml: present" > "$out"
    python3 - <<'PYEOF' >> "$out" 2>/dev/null || echo "- token detection: unavailable (python3 missing)" >> "$out"
def yaml_section_key(content, section, key):
    """Return value of section.key; '' = present-but-empty; None = key absent."""
    current_section = None
    for raw in content.splitlines():
        stripped = raw.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        if raw and not raw[0].isspace() and ':' in stripped:
            current_section = stripped.split(':', 1)[0].strip()
        elif current_section == section and raw[0:1].isspace():
            kv = stripped.split(':', 1)
            if len(kv) == 2 and kv[0].strip() == key:
                val = kv[1].strip()
                if ' #' in val:
                    val = val[:val.index(' #')].strip()
                return val.strip('"\'')
    return None

def tok_status(v):
    if v is None: return 'missing_key'
    if v == '':   return 'empty'
    return 'set'

content = open('.agent-auth.yaml').read()
print('- atlassian.api_token:', tok_status(yaml_section_key(content, 'atlassian', 'api_token')))
print('- figma.personal_access_token:', tok_status(yaml_section_key(content, 'figma', 'personal_access_token')))
print('- github.personal_access_token:', tok_status(yaml_section_key(content, 'github', 'personal_access_token')))
PYEOF
  else
    echo "- .agent-auth.yaml: missing (will be auto-created on first run)" > "$out"
    echo "- atlassian.api_token: unknown" >> "$out"
    echo "- figma.personal_access_token: unknown" >> "$out"
    echo "- github.personal_access_token: unknown" >> "$out"
  fi
) &

# ② Android CLI
(
  out="$TMPDIR_PREFIX/androidcli"
  if command -v android >/dev/null 2>&1; then
    echo "- android CLI: present ($(command -v android))" > "$out"
    android info 2>&1 | head -5 | sed 's/^/  /' >> "$out" || true
    echo "- command discovery:" >> "$out"
    python3 - <<'PYEOF' >> "$out" 2>/dev/null || echo "  - discovery: unavailable" >> "$out"
import subprocess

def help_text(cmd):
  try:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    return (r.stdout or "") + "\n" + (r.stderr or "")
  except Exception:
    return ""

def support(text, *needles):
  if not text.strip():
    return "unknown"
  low = text.lower()
  return "supported" if all(n.lower() in low for n in needles) else "missing"

android = help_text("android --help")
studio = help_text("android studio --help")
commands = {
  "android docs search": support(android, "docs", "search"),
  "android docs fetch": support(android, "docs", "fetch"),
  "android screen capture --annotate": support(android, "screen", "capture"),
  "android layout": support(android, "layout"),
  "android run": support(android, "run"),
  "android studio version-lookup": support(studio, "version-lookup"),
  "android studio render-compose-preview": support(studio, "render-compose-preview"),
  "android studio analyze-file": support(studio, "analyze-file"),
  "android studio find-declaration": support(studio, "find-declaration"),
  "android studio find-usages": support(studio, "find-usages"),
}
for name, state in commands.items():
  print(f"  - {name}: {state}")
PYEOF
  else
    echo "- android CLI: missing" > "$out"
    [ "$MODE" = "audit" ] && echo "- action: report only (audit mode)" >> "$out"
  fi
  command -v adb >/dev/null 2>&1 \
    && echo "- adb: present ($(command -v adb))" >> "$out" \
    || echo "- adb: missing" >> "$out"
) &

# ④ Android skills
(
  out="$TMPDIR_PREFIX/skills"
  if command -v android >/dev/null 2>&1; then
    echo "- android skills list:" > "$out"
    android skills list --long 2>&1 | head -20 | sed 's/^/  /' >> "$out" || true
  else
    echo "- skipped: android CLI missing" > "$out"
  fi
) &

# ⑤ Understand-Anything (checked first for architecture-map lane)
(
  out="$TMPDIR_PREFIX/understand"
  found=0
  if [ -d ".claude/plugins" ]; then
    hits=$(find .claude/plugins -maxdepth 3 -iname "*understand-anything*" 2>/dev/null)
    if [ -n "$hits" ]; then
      echo "- plugin: present ($hits)" > "$out"
      found=1
    fi
  fi
  [ $found -eq 0 ] && echo "- plugin: missing" > "$out"
  [ -f ".understand-anything/knowledge-graph.json" ] \
    && echo "- .understand-anything/knowledge-graph.json: present" >> "$out" \
    || echo "- .understand-anything/knowledge-graph.json: missing" >> "$out"
  if [ $found -eq 1 ] || [ -f ".understand-anything/knowledge-graph.json" ]; then
    echo "- active architecture-map tool: understand-anything" >> "$out"
  else
    echo "- not active; falling back to Graphify check" >> "$out"
  fi
) &

# ⑥ Graphify (fallback — only active if Understand-Anything is unavailable)
(
  out="$TMPDIR_PREFIX/graphify"
  if command -v graphify >/dev/null 2>&1; then
    echo "- graphify CLI: present ($(command -v graphify))" > "$out"
  else
    echo "- graphify CLI: missing" > "$out"
  fi
  if python -m pip show graphifyy >/dev/null 2>&1; then
    ver=$(python -m pip show graphifyy 2>/dev/null | grep "^Version:" | awk '{print $2}')
    echo "- graphifyy package: present (v$ver)" >> "$out"
  else
    echo "- graphifyy package: missing" >> "$out"
  fi
  [ -f "graphify-out/GRAPH_REPORT.md" ] \
    && echo "- GRAPH_REPORT.md: present" >> "$out" \
    || echo "- GRAPH_REPORT.md: missing" >> "$out"
  [ -f "graphify-out/graph.json" ] \
    && echo "- graph.json: present" >> "$out" \
    || echo "- graph.json: missing" >> "$out"
) &

# ⑦ Karpathy
(
  out="$TMPDIR_PREFIX/karpathy"
  found=0
  if [ -f "CLAUDE.md" ]; then
    echo "- CLAUDE.md: present" > "$out"
    grep -qi "karpathy" CLAUDE.md 2>/dev/null \
      && { echo "- Karpathy in CLAUDE.md: found" >> "$out"; found=1; } \
      || echo "- Karpathy in CLAUDE.md: not found" >> "$out"
  else
    echo "- CLAUDE.md: missing" > "$out"
  fi
  if [ -d ".claude/plugins" ]; then
    hits=$(find .claude/plugins -maxdepth 3 -iname "*karpathy*" 2>/dev/null)
    [ -n "$hits" ] && { echo "- Plugin found: $hits" >> "$out"; found=1; } \
                   || echo "- .claude/plugins: no karpathy match" >> "$out"
  fi
  [ $found -eq 0 ] && echo "- Karpathy: not detected (will apply principles manually)" >> "$out" || true
) &

# ⑧ Memory cache
(
  out="$TMPDIR_PREFIX/memory"
  if [ -f ".project-orchestration/memory/tooling-cache.json" ]; then
    echo "- tooling-cache.json: present" > "$out"
    python3 - <<'PYEOF' >> "$out" 2>/dev/null || echo "- cache: python not available" >> "$out"
import json, subprocess
from datetime import datetime, timezone
try:
    d = json.load(open('.project-orchestration/memory/tooling-cache.json'))
    valid_until  = d.get('valid_until')
    graph_commit = d.get('graph_commit')
    print('- cached_at:', d.get('checked_at', '?'))
    print('- valid_until:', valid_until or '?')
    print('- graph_commit:', graph_commit or '?')

    # Freshness: compare valid_until with now
    cache_status = 'unknown'
    if valid_until:
        try:
            exp = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
            cache_status = 'fresh' if datetime.now(timezone.utc) < exp else 'stale'
        except Exception:
            cache_status = 'unparseable'

    # Graph staleness: compare graph_commit with HEAD
    head = subprocess.run('git rev-parse HEAD', shell=True, capture_output=True, text=True, timeout=5)
    if head.returncode == 0:
        head_sha = head.stdout.strip()
        if graph_commit and graph_commit != head_sha:
            print(f'- graph_commit vs HEAD: stale ({graph_commit[:8]} != {head_sha[:8]})')
            if cache_status == 'fresh':
                cache_status = 'graph_stale'
        else:
            print(f'- graph_commit vs HEAD: current')

    print(f'- cache_status: {cache_status}')
except Exception as e:
    print('- cache: unreadable:', e)
PYEOF
  else
    echo "- tooling-cache.json: missing (fresh check required)" > "$out"
  fi
  if [ -f ".project-orchestration/memory/session.json" ]; then
    echo "- session.json: present" >> "$out"
    python3 -c "
import json
try:
  d = json.load(open('.project-orchestration/memory/session.json'))
  print('- last_stage:', d.get('stage_reached','?'))
  print('- task_id:', d.get('task_id','?'))
except: print('- session: unreadable')
" 2>/dev/null >> "$out" || true
  else
    echo "- session.json: missing" >> "$out"
  fi
) &

wait  # ← all parallel checks complete here

# ── Print results in order ────────────────────────────────────────────────────

write_section "Auth"              auth
write_section "Android CLI"       androidcli
write_section "Android skills"    skills
write_section "Understand-Anything" understand
write_section "Graphify"          graphify
write_section "Karpathy"          karpathy
write_section "Memory cache"      memory

echo
echo "## Decision reminder"
echo "- Default mode is audit."
echo "- Do not install/update/rebuild unless user requested bootstrap, update, refresh-graph, or force-reinstall."
echo "- Tokens in .agent-auth.yaml are checked just-in-time when each source reader is activated."
echo "- For machine-readable output: bash templates/tooling-preflight.sh --json"
