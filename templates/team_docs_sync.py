#!/usr/bin/env python3
"""Android Agent Orchestrator — git sync for the team-docs repo (TEAM_DOCS_PATH).

The read phase never changes the docs checkout; the write phase commits only
the paths the current step wrote. Every command prints one JSON object.

  python3 templates/team_docs_sync.py read <TEAM_DOCS_PATH> <path>...
      git fetch, then read each path from the checked-out branch's upstream
      (`git show <upstream>:<path>`). Worktree, index and HEAD are untouched.
      sync: fresh | no_upstream | fetch_failed. lock_freshness is "fresh"
      only when sync is fresh; otherwise "unknown" and files come from the
      local checkout.

  python3 templates/team_docs_sync.py begin <TEAM_DOCS_PATH>
      Before a write: the checkout must be clean (anything already dirty is
      not this task's to commit), then `git pull --rebase`.

  python3 templates/team_docs_sync.py commit-push <TEAM_DOCS_PATH> -m <message> -- <path>...
      After a write: every changed path must be one of <path>... (else stop),
      stage exactly those, commit, check clean, push. A rejected push gets one
      `pull --rebase` + retry. Never `git add .`, never stash/discard.

Exit codes: 0 ok, 2 usage, 3 dirty/unrelated changes (ask the human),
4 rebase conflict (aborted; ask the human), 5 push rejected twice,
6 git failure (no upstream for a write, network, ...).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

TIMEOUT_S = 60
EXIT_USAGE, EXIT_DIRTY, EXIT_CONFLICT, EXIT_PUSH, EXIT_GIT = 2, 3, 4, 5, 6


class Git:
    def __init__(self, repo: str) -> None:
        self.repo = repo

    def run(self, *args: str) -> Tuple[int, str]:
        try:
            proc = subprocess.run(["git", "-C", self.repo, *args], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT_S)
            return proc.returncode, proc.stdout
        except (OSError, subprocess.SubprocessError):
            return -1, ""

    def ok(self, *args: str) -> bool:
        return self.run(*args)[0] == 0

    def upstream(self) -> Optional[str]:
        code, out = self.run("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
        return out.strip() if code == 0 and out.strip() else None

    def changed_paths(self) -> List[str]:
        code, out = self.run("status", "--porcelain", "--untracked-files=all", "-z")
        if code != 0:
            raise RuntimeError("git status failed")
        entries = out.split("\0")
        paths: List[str] = []
        i = 0
        while i < len(entries):
            entry = entries[i]
            if len(entry) > 3:
                paths.append(entry[3:])
                if entry[0] in "RC":          # rename/copy: next entry is the source path
                    i += 1
                    if i < len(entries) and entries[i]:
                        paths.append(entries[i])
            i += 1
        return sorted(set(paths))

    def conflicts(self) -> List[str]:
        _, out = self.run("diff", "--name-only", "--diff-filter=U")
        return [p for p in out.splitlines() if p]

    def pull_rebase(self) -> Tuple[int, Dict[str, Any]]:
        if self.ok("pull", "--rebase", "--quiet"):
            return 0, {}
        conflicts = self.conflicts()
        if conflicts or os.path.isdir(os.path.join(self.repo, ".git", "rebase-merge")) \
                or os.path.isdir(os.path.join(self.repo, ".git", "rebase-apply")):
            self.run("rebase", "--abort")
            return EXIT_CONFLICT, {"conflicts": conflicts}
        return EXIT_GIT, {"error": "pull --rebase failed"}


def emit(code: int, payload: Dict[str, Any]) -> int:
    print(json.dumps(payload, indent=2))
    return code


def safe_rel(path: str) -> Optional[str]:
    norm = os.path.normpath(path)
    if os.path.isabs(norm) or norm == ".." or norm.startswith(".." + os.sep) or norm == ".":
        return None
    return norm.replace(os.sep, "/")


# ── read ─────────────────────────────────────────────────────────────────────

def read_local(repo: str, rel: str) -> Dict[str, Any]:
    full = os.path.join(repo, rel)
    if not os.path.isfile(full):
        return {"present": False, "content": None}
    with open(full, encoding="utf-8", errors="replace") as f:
        return {"present": True, "content": f.read()}


def cmd_read(repo: str, paths: Sequence[str]) -> int:
    git = Git(repo)
    upstream = git.upstream()
    if upstream is None:
        sync = "no_upstream"
    else:
        sync = "fresh" if git.ok("fetch", "--quiet") else "fetch_failed"
    files: Dict[str, Any] = {}
    for raw in paths:
        rel = safe_rel(raw)
        if rel is None:
            return emit(EXIT_USAGE, {"error": f"path outside the docs repo: {raw}"})
        if sync == "fresh":
            code, out = git.run("show", f"{upstream}:{rel}")
            files[rel] = {"present": code == 0, "content": out if code == 0 else None}
        else:
            files[rel] = read_local(repo, rel)
    ahead = 0
    if upstream is not None:
        code, out = git.run("rev-list", "--count", f"{upstream}..HEAD")
        ahead = int(out.strip()) if code == 0 and out.strip().isdigit() else 0
    return emit(0, {"sync": sync, "upstream": upstream, "local_ahead": ahead,
                    "lock_freshness": "fresh" if sync == "fresh" else "unknown",
                    "files": files})


# ── write ────────────────────────────────────────────────────────────────────

def cmd_begin(repo: str) -> int:
    git = Git(repo)
    dirty = git.changed_paths()
    if dirty:
        return emit(EXIT_DIRTY, {"clean": False, "dirty": dirty,
                                 "action": "ask the human; never stash, commit or discard these"})
    if git.upstream() is None:
        return emit(EXIT_GIT, {"clean": True, "error": "no upstream configured; cannot sync before write"})
    code, info = git.pull_rebase()
    return emit(code, {"clean": True, "synced": code == 0, **info})


def push_with_retry(git: Git) -> Tuple[int, Dict[str, Any]]:
    if git.ok("push", "--quiet"):
        return 0, {"pushed": True, "push_attempts": 1}
    code, info = git.pull_rebase()
    if code != 0:
        return code, {"pushed": False, "push_attempts": 1, **info}
    if git.ok("push", "--quiet"):
        return 0, {"pushed": True, "push_attempts": 2}
    return EXIT_PUSH, {"pushed": False, "push_attempts": 2, "action": "ask the human"}


def cmd_commit_push(repo: str, message: str, paths: Sequence[str]) -> int:
    allowed: Set[str] = set()
    for raw in paths:
        rel = safe_rel(raw)
        if rel is None:
            return emit(EXIT_USAGE, {"error": f"path outside the docs repo: {raw}"})
        allowed.add(rel)
    git = Git(repo)
    if git.upstream() is None:
        return emit(EXIT_GIT, {"error": "no upstream configured; cannot push"})
    changed = set(git.changed_paths())
    unrelated = sorted(changed - allowed)
    if unrelated:
        return emit(EXIT_DIRTY, {"committed": False, "unrelated": unrelated,
                                 "action": "ask the human; only this step's paths may be committed"})
    to_stage = sorted(changed & allowed)
    if not to_stage:
        return emit(0, {"committed": False, "reason": "no changes in the given paths"})
    if not git.ok("add", "--", *to_stage):
        return emit(EXIT_GIT, {"error": "git add failed"})
    _, staged_out = git.run("diff", "--cached", "--name-only")
    staged = sorted(p for p in staged_out.splitlines() if p)
    if staged != to_stage:
        git.run("reset", "-q", "--", *staged)
        return emit(EXIT_DIRTY, {"committed": False, "staged": staged, "expected": to_stage})
    if not git.ok("commit", "-q", "-m", message):
        return emit(EXIT_GIT, {"error": "git commit failed"})
    if git.changed_paths():
        return emit(EXIT_DIRTY, {"committed": True, "pushed": False,
                                 "error": "checkout not clean after commit"})
    code, info = push_with_retry(git)
    return emit(code, {"committed": True, "paths": to_stage, **info})


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: Sequence[str]) -> int:
    args = list(argv)
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print(__doc__)
        return EXIT_USAGE
    command, repo, rest = args[0], args[1], args[2:]
    if not os.path.isdir(repo):
        return emit(EXIT_USAGE, {"error": f"not a directory: {repo}"})
    if command == "read" and rest:
        return cmd_read(repo, rest)
    if command == "begin" and not rest:
        return cmd_begin(repo)
    if command == "commit-push" and len(rest) >= 4 and rest[0] == "-m" and rest[2] == "--":
        return cmd_commit_push(repo, rest[1], rest[3:])
    print(__doc__, file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
