#!/usr/bin/env bash
set -u

# Android Agent Orchestrator - Safe Tooling Preflight
# Default behavior: audit only.
# This script does NOT install, update, delete, or rebuild anything.

echo "# Tooling Preflight"
echo
echo "## Mode"
echo "audit"
echo
echo "## Timestamp"
date -u +"%Y-%m-%dT%H:%M:%SZ"
echo
echo "## Working directory"
pwd

section() {
  echo
  echo "## $1"
}

check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "- $cmd: present ($(command -v "$cmd"))"
    return 0
  else
    echo "- $cmd: missing"
    return 1
  fi
}

section "AI DevKit"
if check_cmd ai-devkit; then
  ai-devkit --help >/dev/null 2>&1 && echo "- ai-devkit help: usable" || echo "- ai-devkit help: failed"
else
  echo "- action: report missing; do not install in audit mode"
fi
[ -f ".ai-devkit.json" ] && echo "- .ai-devkit.json: present" || echo "- .ai-devkit.json: missing"

section "Android CLI"
if check_cmd android; then
  echo "- android info:"
  android info 2>&1 | sed 's/^/  /' || true
else
  echo "- action: report missing; do not install in audit mode"
fi

section "Android skills"
if command -v android >/dev/null 2>&1; then
  echo "- android skills list --long:"
  android skills list --long 2>&1 | sed 's/^/  /' || true
else
  echo "- skipped: android CLI missing"
fi

section "Graphify"
if check_cmd graphify; then
  graphify --help >/dev/null 2>&1 && echo "- graphify help: usable" || echo "- graphify help: unavailable or slash-command only"
else
  echo "- action: report missing; do not install in audit mode"
fi
if python -m pip show graphifyy >/dev/null 2>&1; then
  echo "- Python package graphifyy: present"
  python -m pip show graphifyy 2>/dev/null | sed 's/^/  /'
else
  echo "- Python package graphifyy: missing or not visible to current Python"
fi
[ -f "graphify-out/GRAPH_REPORT.md" ] && echo "- graphify-out/GRAPH_REPORT.md: present" || echo "- graphify-out/GRAPH_REPORT.md: missing"
[ -f "graphify-out/graph.json" ] && echo "- graphify-out/graph.json: present" || echo "- graphify-out/graph.json: missing"

section "Karpathy"
if [ -f "CLAUDE.md" ]; then
  echo "- CLAUDE.md: present"
  grep -i "karpathy" CLAUDE.md >/dev/null 2>&1 && echo "- Karpathy mention in CLAUDE.md: present" || echo "- Karpathy mention in CLAUDE.md: not found"
else
  echo "- CLAUDE.md: missing"
fi
[ -d ".claude/plugins" ] && find .claude/plugins -maxdepth 3 -iname "*karpathy*" 2>/dev/null | sed 's/^/  /' || echo "- .claude/plugins: missing"
[ -d ".agents/skills" ] && find .agents/skills -maxdepth 4 -iname "*karpathy*" 2>/dev/null | sed 's/^/  /' || echo "- .agents/skills: missing"

section "Decision reminder"
echo "- Default mode is audit."
echo "- Do not install/update/rebuild unless the user explicitly requested bootstrap, update, refresh-graph, or force-reinstall."
