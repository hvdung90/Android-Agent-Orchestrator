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

result = {
    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "mode": MODE,
    "ready_for_stage_0": False,
    "blocking_gaps": [],
    "non_blocking_gaps": [],
    "tools": {},
    "graph": {},
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
        t["atlassian_token"] = "set" if ("api_token:" in content and len([l for l in content.splitlines() if "api_token:" in l and l.split("api_token:")[-1].strip().strip("\"'")]) > 0) else "empty"
        t["figma_token"] = "set" if ("personal_access_token:" in content and len([l for l in content.splitlines() if "personal_access_token:" in l and l.split("personal_access_token:")[-1].strip().strip("\"'")]) > 0) else "empty"
    except Exception:
        t["atlassian_token"] = "unknown"
        t["figma_token"] = "unknown"
else:
    t["atlassian_token"] = "unknown"
    t["figma_token"] = "unknown"
    gaps_warn.append("auth_file_missing")

# ── AI DevKit ─────────────────────────────────────────────────────────────────
ai_devkit_ok = cmd_ok("command -v ai-devkit")
t["ai_devkit"] = "present" if ai_devkit_ok else "missing"
t["ai_devkit_config"] = "present" if os.path.isfile(".ai-devkit.json") else "missing"
if not ai_devkit_ok:
    gaps_blocking.append("ai_devkit_missing")

# ── Android CLI ───────────────────────────────────────────────────────────────
android_ok = cmd_ok("command -v android")
t["android_cli"] = "present" if android_ok else "missing"
if not android_ok:
    gaps_warn.append("android_cli_missing")

# ── Graphify ──────────────────────────────────────────────────────────────────
graphify_cli = cmd_ok("command -v graphify")
graphify_pkg = cmd_ok("python -m pip show graphifyy 2>/dev/null")
graph_report = os.path.isfile("graphify-out/GRAPH_REPORT.md")
graph_json   = os.path.isfile("graphify-out/graph.json")
t["graphify_cli"]     = "present" if graphify_cli else "missing"
t["graphify_package"] = "present" if graphify_pkg else "missing"
result["graph"]["report_present"] = graph_report
result["graph"]["json_present"]   = graph_json
if not graphify_cli and not graphify_pkg:
    gaps_warn.append("graphify_missing")
elif not graph_report:
    gaps_warn.append("graph_report_missing")

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

# ── Serena ────────────────────────────────────────────────────────────────────
uv_ok = cmd_ok("command -v uv")
t["uv"] = "present" if uv_ok else "missing"
if uv_ok:
    serena_ok = cmd_ok("uvx serena --version 2>/dev/null")
    t["serena"] = "present" if serena_ok else "missing"
    if not serena_ok:
        gaps_warn.append("serena_missing")
else:
    t["serena"] = "missing"
    gaps_warn.append("serena_missing")

# ── Memory cache ──────────────────────────────────────────────────────────────
cache_path = ".project-orchestration/memory/tooling-cache.json"
cache_present = os.path.isfile(cache_path)
result["cache"]["present"] = cache_present
if cache_present:
    try:
        d = json.load(open(cache_path))
        result["cache"]["valid_until"]  = d.get("valid_until")
        result["cache"]["graph_commit"] = d.get("graph_commit")
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
    grep -q "api_token:.*[^\"' ]" .agent-auth.yaml 2>/dev/null \
      && echo "- atlassian.api_token: set" >> "$out" \
      || echo "- atlassian.api_token: empty" >> "$out"
    grep -q "personal_access_token:.*[^\"' ]" .agent-auth.yaml 2>/dev/null \
      && echo "- figma.personal_access_token: set" >> "$out" \
      || echo "- figma.personal_access_token: empty" >> "$out"
  else
    echo "- .agent-auth.yaml: missing (will be auto-created on first run)" > "$out"
    echo "- atlassian.api_token: unknown" >> "$out"
    echo "- figma.personal_access_token: unknown" >> "$out"
  fi
) &

# ② AI DevKit
(
  out="$TMPDIR_PREFIX/aidevkit"
  if command -v ai-devkit >/dev/null 2>&1; then
    echo "- ai-devkit: present ($(command -v ai-devkit))" > "$out"
  else
    echo "- ai-devkit: missing" > "$out"
    [ "$MODE" = "audit" ] && echo "- action: report only (audit mode)" >> "$out"
  fi
  [ -f ".ai-devkit.json" ] \
    && echo "- .ai-devkit.json: present" >> "$out" \
    || echo "- .ai-devkit.json: missing" >> "$out"
) &

# ③ Android CLI
(
  out="$TMPDIR_PREFIX/androidcli"
  if command -v android >/dev/null 2>&1; then
    echo "- android CLI: present ($(command -v android))" > "$out"
    android info 2>&1 | head -5 | sed 's/^/  /' >> "$out" || true
  else
    echo "- android CLI: missing" > "$out"
    [ "$MODE" = "audit" ] && echo "- action: report only (audit mode)" >> "$out"
  fi
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

# ⑤ Graphify
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

# ⑥ Karpathy
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

# ⑦ Memory cache
(
  out="$TMPDIR_PREFIX/memory"
  if [ -f ".project-orchestration/memory/tooling-cache.json" ]; then
    echo "- tooling-cache.json: present" > "$out"
    python3 -c "
import json, sys
try:
  d = json.load(open('.project-orchestration/memory/tooling-cache.json'))
  print('- cached_at:', d.get('checked_at','?'))
  print('- valid_until:', d.get('valid_until','?'))
  print('- graph_commit:', d.get('graph_commit','?'))
except: print('- cache: unreadable')
" 2>/dev/null >> "$out" || echo "- cache: python not available" >> "$out"
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

# ⑧ Serena
(
  out="$TMPDIR_PREFIX/serena"
  if command -v uv >/dev/null 2>&1; then
    echo "- uv: present ($(command -v uv))" > "$out"
    ver=$(uvx serena --version 2>/dev/null | head -1)
    if [ -n "$ver" ]; then
      echo "- serena: $ver" >> "$out"
    else
      echo "- serena: not installed (uvx serena unavailable)" >> "$out"
      [ "$MODE" = "audit" ] && echo "- action: report only (audit mode); non-blocking" >> "$out"
    fi
  else
    echo "- uv: missing" > "$out"
    echo "- serena: unavailable (uv not installed); non-blocking" >> "$out"
  fi
  echo "- backend: lsp (default) — JetBrains is dev opt-in, not auto-detected" >> "$out"
  echo "- kotlin-ls: pre-alpha — diagnostics disabled unless dev confirms stable" >> "$out"
) &

wait  # ← all parallel checks complete here

# ── Print results in order ────────────────────────────────────────────────────

write_section "Auth"           auth
write_section "AI DevKit"      aidevkit
write_section "Android CLI"    androidcli
write_section "Android skills" skills
write_section "Graphify"       graphify
write_section "Karpathy"       karpathy
write_section "Serena"         serena
write_section "Memory cache"   memory

echo
echo "## Decision reminder"
echo "- Default mode is audit."
echo "- Do not install/update/rebuild unless user requested bootstrap, update, refresh-graph, or force-reinstall."
echo "- Tokens in .agent-auth.yaml are checked just-in-time when each source reader is activated."
echo "- For machine-readable output: bash templates/tooling-preflight.sh --json"
