#!/usr/bin/env python3
"""Android Agent Orchestrator — credential helper for `.agent-auth.yaml`.

The agent must never read `.agent-auth.yaml` into its context, and never write
a token into a command line (both end up in the transcript). This helper is
the only thing that opens the file:

  python3 templates/agent_auth.py init                       # create 0600 file from template, never overwrite
  python3 templates/agent_auth.py status [--project KEY] [--json] [--fix-permissions]
  python3 templates/agent_auth.py exec <service> [--project KEY] -- <command...>

`status` reports set / empty / missing_key per field — never values.
`exec` passes credentials to the child as environment variables (see ENV
below) and replaces every credential value in the child's stdout/stderr with
`[REDACTED:<service>.<field>]`. Reference them in the command, e.g.:

  python3 templates/agent_auth.py exec atlassian -- sh -c \
    'curl -sf -u "$AAO_ATLASSIAN_EMAIL:$AAO_ATLASSIAN_API_TOKEN" \
       "https://$AAO_ATLASSIAN_DOMAIN/rest/api/3/issue/CA-42"'

Exit codes: 0 ok (exec: child's code), 2 usage, 3 credential missing/empty,
4 auth file missing or unreadable.
"""
from __future__ import annotations

import base64
import json
import os
import stat
import subprocess
import sys
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

AUTH_FILE = ".agent-auth.yaml"
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent-auth.example.yaml")

# service → ordered (field, env var). Every field value is redacted by `exec`.
SERVICES: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "atlassian": (("domain", "AAO_ATLASSIAN_DOMAIN"),
                  ("email", "AAO_ATLASSIAN_EMAIL"),
                  ("api_token", "AAO_ATLASSIAN_API_TOKEN")),
    "figma": (("personal_access_token", "AAO_FIGMA_TOKEN"),),
    "github": (("personal_access_token", "AAO_GITHUB_TOKEN"),),
}
MIN_REDACT_LEN = 4

EXIT_USAGE, EXIT_MISSING_CREDENTIAL, EXIT_AUTH_FILE = 2, 3, 4


class AuthFileError(Exception):
    """Raised for unreadable/malformed auth files. Messages never quote content."""


# ── Minimal YAML subset parser ───────────────────────────────────────────────
# Supports exactly what agent-auth.example.yaml uses: nested mappings by
# indentation, lists of mappings ("- key: value"), quoted/unquoted scalars,
# `[]`, full-line and inline comments. Anything else raises AuthFileError.

class _Line(NamedTuple):
    no: int
    indent: int
    text: str
    dash: bool


def _strip_comment(line: str) -> str:
    quote: Optional[str] = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1].isspace()):
            return line[:i]
    return line


def _scalar(raw: str, no: int) -> Any:
    value = raw.strip()
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    if value[:1] in ("'", '"'):
        raise AuthFileError(f"line {no}: unterminated quoted value")
    return value


def _tokenize(text: str) -> List[_Line]:
    lines: List[_Line] = []
    for no, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise AuthFileError(f"line {no}: tabs are not allowed for indentation")
        body = _strip_comment(raw).rstrip()
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        content = body.strip()
        if content == "-" or content.startswith("- "):
            lines.append(_Line(no, indent, "", True))
            rest = content[1:].strip()
            if rest:
                lines.append(_Line(no, indent + 2, rest, False))
        else:
            lines.append(_Line(no, indent, content, False))
    return lines


def _parse(lines: List[_Line], i: int, indent: int) -> Tuple[Any, int]:
    if lines[i].dash:
        return _parse_list(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_map(lines: List[_Line], i: int, indent: int) -> Tuple[Dict[str, Any], int]:
    out: Dict[str, Any] = {}
    while i < len(lines) and lines[i].indent >= indent:
        line = lines[i]
        if line.indent > indent or line.dash:
            raise AuthFileError(f"line {line.no}: unexpected indentation")
        key, sep, rest = line.text.partition(":")
        if not sep or not key.strip():
            raise AuthFileError(f"line {line.no}: expected 'key: value'")
        i += 1
        if rest.strip():
            out[key.strip()] = _scalar(rest, line.no)
        elif i < len(lines) and lines[i].indent > indent:
            out[key.strip()], i = _parse(lines, i, lines[i].indent)
        elif i < len(lines) and lines[i].dash and lines[i].indent == indent:
            out[key.strip()], i = _parse_list(lines, i, indent)
        else:
            out[key.strip()] = ""
    return out, i


def _parse_list(lines: List[_Line], i: int, indent: int) -> Tuple[List[Any], int]:
    items: List[Any] = []
    while i < len(lines) and lines[i].dash and lines[i].indent == indent:
        i += 1
        if i < len(lines) and lines[i].indent > indent and not lines[i].dash:
            item, i = _parse_map(lines, i, lines[i].indent)
        else:
            item = None
        items.append(item)
    return items, i


def load_auth(text: str) -> Dict[str, Any]:
    lines = _tokenize(text)
    if not lines:
        return {}
    data, i = _parse_map(lines, 0, lines[0].indent)
    if i != len(lines):
        raise AuthFileError(f"line {lines[i].no}: unexpected indentation")
    return data


def read_auth_file(path: str = AUTH_FILE) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            return load_auth(f.read())
    except (OSError, UnicodeDecodeError) as exc:
        raise AuthFileError(f"cannot read {path}: {type(exc).__name__}") from None


# ── Resolution ───────────────────────────────────────────────────────────────

def field_state(value: Any) -> str:
    if value is None:
        return "missing_key"
    return "set" if isinstance(value, str) and value.strip() else "empty"


def resolve(data: Dict[str, Any], service: str, project: Optional[str] = None
            ) -> Tuple[Dict[str, Optional[str]], Dict[str, str]]:
    """Per-field Level 3 (project) override with Level 2 (default) fallback."""
    default = data.get(service) if isinstance(data.get(service), dict) else {}
    override: Dict[str, Any] = {}
    if project:
        for entry in data.get("projects") or []:
            if isinstance(entry, dict) and entry.get("jira_project_key") == project:
                block = entry.get(service)
                override = block if isinstance(block, dict) else {}
                break
    fields: Dict[str, Optional[str]] = {}
    sources: Dict[str, str] = {}
    for name, _ in SERVICES[service]:
        if name in override:
            fields[name], sources[name] = override[name], f"project:{project}"
        else:
            fields[name], sources[name] = default.get(name), "default"
    return fields, sources


def permission_state(path: str) -> str:
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode)
    except OSError:
        return "unknown"
    return "ok" if mode & 0o077 == 0 else "too_open"


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_init() -> int:
    try:
        fd = os.open(AUTH_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(f"{AUTH_FILE}: exists (left unchanged; permissions {permission_state(AUTH_FILE)})")
        return 0
    with os.fdopen(fd, "w", encoding="utf-8") as out, open(TEMPLATE, encoding="utf-8") as src:
        out.write(src.read())
    os.chmod(AUTH_FILE, 0o600)  # umask cannot widen it, but be explicit
    print(f"{AUTH_FILE}: created from template (permissions 0600); all tokens empty")
    return 0


def status_report(project: Optional[str]) -> Dict[str, Any]:
    if not os.path.exists(AUTH_FILE):
        return {"file": "missing"}
    perms = permission_state(AUTH_FILE)
    try:
        data = read_auth_file()
    except AuthFileError as exc:
        return {"file": "unreadable", "permissions": perms, "reason": str(exc)}
    services = {}
    for service in SERVICES:
        fields, sources = resolve(data, service, project)
        services[service] = {"fields": {k: field_state(v) for k, v in fields.items()},
                             "sources": sources}
    return {"file": "present", "permissions": perms, "project": project, "services": services}


def cmd_status(project: Optional[str], as_json: bool, fix_permissions: bool) -> int:
    if fix_permissions and os.path.isfile(AUTH_FILE):
        os.chmod(AUTH_FILE, 0o600)
    report = status_report(project)
    if as_json:
        print(json.dumps(report, indent=2))
        return 0
    if report["file"] != "present":
        print(f"{AUTH_FILE}: {report['file']}" + (f" ({report['reason']})" if "reason" in report else ""))
        return 0
    print(f"{AUTH_FILE}: present (permissions {report['permissions']})")
    if report["permissions"] == "too_open":
        print("  -> run: python3 templates/agent_auth.py status --fix-permissions")
    for service, info in report["services"].items():
        origin = sorted(set(info["sources"].values()))
        fields = " ".join(f"{k}={v}" for k, v in info["fields"].items())
        print(f"{service} ({', '.join(origin)}): {fields}")
    return 0


def redactions(service: str, fields: Dict[str, Optional[str]]) -> List[Tuple[str, str]]:
    pairs = [(v, f"[REDACTED:{service}.{k}]") for k, v in fields.items()
             if isinstance(v, str) and len(v) >= MIN_REDACT_LEN]
    if service == "atlassian" and fields.get("email") and fields.get("api_token"):
        raw = f"{fields['email']}:{fields['api_token']}".encode("utf-8")
        pairs.append((base64.b64encode(raw).decode("ascii"), "[REDACTED:atlassian.basic_auth]"))
    # longest first so a value containing another value is replaced whole
    return sorted(pairs, key=lambda p: len(p[0]), reverse=True)


def redact(text: str, pairs: Sequence[Tuple[str, str]]) -> str:
    for value, label in pairs:
        text = text.replace(value, label)
    return text


def cmd_exec(service: str, project: Optional[str], argv: List[str]) -> int:
    if service not in SERVICES:
        print(f"unknown service '{service}' (expected: {', '.join(SERVICES)})", file=sys.stderr)
        return EXIT_USAGE
    if not argv:
        print("usage: agent_auth.py exec <service> [--project KEY] -- <command...>", file=sys.stderr)
        return EXIT_USAGE
    if not os.path.exists(AUTH_FILE):
        print(f"{AUTH_FILE} is missing: run `python3 templates/agent_auth.py init`", file=sys.stderr)
        return EXIT_AUTH_FILE
    try:
        fields, _ = resolve(read_auth_file(), service, project)
    except AuthFileError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_AUTH_FILE
    missing = [k for k, v in fields.items() if field_state(v) != "set"]
    if missing:
        for name in missing:
            print(f"{service}.{name} is {field_state(fields[name])} in {AUTH_FILE}: ask the user "
                  f"to fill it in the file themselves — do not paste it in chat",
                  file=sys.stderr)
        return EXIT_MISSING_CREDENTIAL
    env = dict(os.environ)
    env.update({var: str(fields[name]) for name, var in SERVICES[service]})
    try:
        proc = subprocess.run(argv, env=env, capture_output=True)
    except OSError as exc:
        print(f"cannot run command: {type(exc).__name__}", file=sys.stderr)
        return 127
    pairs = redactions(service, fields)
    sys.stdout.write(redact(proc.stdout.decode("utf-8", "replace"), pairs))
    sys.stderr.write(redact(proc.stderr.decode("utf-8", "replace"), pairs))
    return proc.returncode


# ── CLI ──────────────────────────────────────────────────────────────────────

def take_option(args: List[str], name: str) -> Tuple[Optional[str], List[str]]:
    if name not in args:
        return None, args
    i = args.index(name)
    if i + 1 >= len(args):
        raise ValueError(f"{name} needs a value")
    return args[i + 1], args[:i] + args[i + 2:]


def main(argv: Sequence[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = list(argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else EXIT_USAGE
    command, rest = args[0], args[1:]
    child: List[str] = []
    if "--" in rest:
        i = rest.index("--")
        rest, child = rest[:i], rest[i + 1:]
    try:
        project, rest = take_option(rest, "--project")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE
    if command == "init" and not rest:
        return cmd_init()
    if command == "status":
        flags = set(rest)
        if flags - {"--json", "--fix-permissions"}:
            print("usage: agent_auth.py status [--project KEY] [--json] [--fix-permissions]",
                  file=sys.stderr)
            return EXIT_USAGE
        return cmd_status(project, "--json" in flags, "--fix-permissions" in flags)
    if command == "exec" and len(rest) == 1:
        return cmd_exec(rest[0], project, child)
    print("usage: agent_auth.py {init | status | exec <service> -- <command...>}", file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
