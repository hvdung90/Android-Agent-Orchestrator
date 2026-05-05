#!/usr/bin/env bash
set -u

# Android Agent Orchestrator — Tooling Preflight
# Default: audit only. Does NOT install, update, delete, or rebuild anything.
# All checks run in parallel; results are collected and printed in order.
#
# Usage:
#   bash templates/tooling-preflight.sh            # audit mode (default)
#   bash templates/tooling-preflight.sh bootstrap  # report what would be installed

MODE="${1:-audit}"
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

wait  # ← all parallel checks complete here

# ── Print results in order ────────────────────────────────────────────────────

write_section "Auth"       auth
write_section "AI DevKit"  aidevkit
write_section "Android CLI" androidcli
write_section "Android skills" skills
write_section "Graphify"   graphify
write_section "Karpathy"   karpathy
write_section "Memory cache" memory

echo
echo "## Decision reminder"
echo "- Default mode is audit."
echo "- Do not install/update/rebuild unless user requested bootstrap, update, refresh-graph, or force-reinstall."
echo "- Tokens in .agent-auth.yaml are checked just-in-time when each source reader is activated."
