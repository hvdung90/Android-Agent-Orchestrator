#!/usr/bin/env bash
set -u

# Android Agent Orchestrator — Tooling Preflight
# Default: audit only. Does NOT install, update, delete, or rebuild anything.
# Thin wrapper: all checks live in tooling_preflight.py (one implementation,
# rendered as Markdown or JSON so both formats report the same facts).
#
# Usage:
#   bash templates/tooling-preflight.sh                  # audit mode → markdown
#   bash templates/tooling-preflight.sh bootstrap        # bootstrap mode → markdown
#   bash templates/tooling-preflight.sh --json           # audit mode → JSON
#   bash templates/tooling-preflight.sh bootstrap --json # bootstrap mode → JSON
#
# Requires: python3 (stdlib only). Run from the project root.

here="${BASH_SOURCE[0]%/*}"
[ "$here" = "${BASH_SOURCE[0]}" ] && here="."

if ! command -v python3 >/dev/null 2>&1; then
  echo "tooling-preflight: python3 is required but was not found on PATH" >&2
  exit 127
fi

exec python3 "$here/tooling_preflight.py" "$@"
