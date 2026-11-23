#!/usr/bin/env python3
"""Install the skill pack at an exact git ref, or check which version is installed.

Why: a hand-copied skill directory goes stale silently (a machine was found
running 4.3.0 while the repo was at 6.x), and a pilot must run each cohort at a
known skill commit. This installs from `git archive <ref>`, so only tracked
files are copied (never `.agent-auth.yaml` or local settings), and records the
ref, commit and version in `.aao-install.json` inside the installed directory.

Usage:
  python3 scripts/install_skill.py [--ref REF] [--dest DIR]   # install (default ref HEAD)
  python3 scripts/install_skill.py --check [--ref REF] [--dest DIR]

Default DEST: ~/.claude/skills/android-agent-orchestrator
An existing install is moved to `<parent of DEST's dir>/.aao-skill-backups/<name>.bak-<UTC timestamp>`
(outside the skills directory, so Claude Code never loads a backup as a second
skill with the same name), never deleted.
`--check` exits 0 when the installed commit equals REF's commit, 1 otherwise.
Stdlib only.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from typing import Optional

MARKER = ".aao-install.json"
EXCLUDE_TOP = ("tests", ".github")
DEFAULT_DEST = os.path.join("~", ".claude", "skills", "android-agent-orchestrator")
VERSION_RE = re.compile(r"^\s+version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", re.M)


class InstallError(Exception):
    """A user-facing failure; the message says what to do."""


def git(repo: str, *args: str) -> bytes:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        raise InstallError(f"git {' '.join(args)} failed: {err}")
    return proc.stdout


def resolve_commit(repo: str, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()


def version_of(skill_md: str) -> Optional[str]:
    match = VERSION_RE.search(skill_md)
    return match.group(1) if match else None


def ref_version(repo: str, commit: str) -> Optional[str]:
    return version_of(git(repo, "show", f"{commit}:SKILL.md").decode("utf-8", "replace"))


def read_marker(dest: str) -> Optional[dict]:
    try:
        with open(os.path.join(dest, MARKER), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def installed_version(dest: str) -> Optional[str]:
    try:
        with open(os.path.join(dest, "SKILL.md"), encoding="utf-8", errors="replace") as fh:
            return version_of(fh.read())
    except OSError:
        return None


def _safe_members(tar: tarfile.TarFile):
    for member in tar.getmembers():
        parts = member.name.split("/")
        if member.name.startswith("/") or ".." in parts:
            raise InstallError(f"unsafe path in archive: {member.name}")
        if member.issym() or member.islnk():
            continue  # the skill pack needs no links; skip rather than follow
        if parts[0] in EXCLUDE_TOP:
            continue
        yield member


def extract(repo: str, commit: str, target: str) -> None:
    data = git(repo, "archive", "--format=tar", commit)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        extra = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
        tar.extractall(target, members=list(_safe_members(tar)), **extra)


def backup_dir(dest: str) -> str:
    skills_dir = os.path.dirname(dest)
    return os.path.join(os.path.dirname(skills_dir), ".aao-skill-backups")


def install(repo: str, ref: str, dest: str) -> dict:
    if os.path.islink(dest):
        raise InstallError(
            f"{dest} is a symlink; remove it yourself first (it may point at a working copy)")
    commit = resolve_commit(repo, ref)
    version = ref_version(repo, commit)
    if version is None:
        raise InstallError(f"SKILL.md at {ref} has no frontmatter version")

    parent = os.path.dirname(dest) or "."
    os.makedirs(parent, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=".aao-install-", dir=parent)
    try:
        extract(repo, commit, staging)
        info = {
            "ref": ref,
            "commit": commit,
            "version": version,
            "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with open(os.path.join(staging, MARKER), "w", encoding="utf-8") as fh:
            json.dump(info, fh, indent=2)
            fh.write("\n")
        backup = None
        if os.path.exists(dest):
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            os.makedirs(backup_dir(dest), exist_ok=True)
            backup = os.path.join(backup_dir(dest), f"{os.path.basename(dest)}.bak-{stamp}")
            os.rename(dest, backup)
        os.rename(staging, dest)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {**info, "dest": dest, "backup": backup}


def check(repo: str, ref: str, dest: str) -> dict:
    commit = resolve_commit(repo, ref)
    marker = read_marker(dest)
    return {
        "dest": dest,
        "installed_version": installed_version(dest),
        "installed_commit": marker.get("commit") if marker else None,
        "expected_ref": ref,
        "expected_commit": commit,
        "expected_version": ref_version(repo, commit),
        "match": bool(marker) and marker.get("commit") == commit,
    }


def worktree_dirty(repo: str) -> bool:
    return bool(git(repo, "status", "--porcelain", "--untracked-files=no").strip())


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ref", default="HEAD", help="git ref to install or check (default HEAD)")
    parser.add_argument("--dest", default=DEFAULT_DEST, help=f"install directory (default {DEFAULT_DEST})")
    parser.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--check", action="store_true", help="report the installed version; exit 1 on mismatch")
    args = parser.parse_args(argv)
    dest = os.path.abspath(os.path.expanduser(args.dest))

    try:
        if args.check:
            result = check(args.repo, args.ref, dest)
            print(json.dumps(result, indent=2))
            return 0 if result["match"] else 1
        if args.ref == "HEAD" and worktree_dirty(args.repo):
            print("note: uncommitted changes are not installed (git archive uses the commit)",
                  file=sys.stderr)
        result = install(args.repo, args.ref, dest)
        print(json.dumps(result, indent=2))
        return 0
    except InstallError as exc:
        print(f"install_skill: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
