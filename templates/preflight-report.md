# Tooling Preflight

## Mode

`audit | bootstrap | update | refresh-graph | force-reinstall`

## Summary

- Ready for Stage 0:
- Blocking gaps:
- Non-blocking gaps:

## Auth

- `.agent-auth.yaml`: present | created-empty | missing
- `atlassian.api_token`: set | empty
- `figma.personal_access_token`: set | empty
- `github.personal_access_token`: set | empty
- Project overrides defined: <count>
- Notes:

## Android CLI

- CLI present:
- ADB present:
- `android info` result:
- Android commands discovered:
- Android Studio commands discovered:
- Action allowed:
- Action taken:
- Notes:

## Android skills

- Can list skills:
- Relevant skills searched:
- Relevant skills found:
- Relevant skills installed:
- Action allowed:
- Action taken:
- Notes:

## Understand-Anything

- Plugin/skill present:
- `.understand-anything/knowledge-graph.json`:
- Active architecture-map tool: yes | no (fallback to Graphify)
- Action allowed:
- Action taken:
- Notes:

## Graphify

- Active architecture-map tool (only if Understand-Anything unavailable): yes | no
- CLI present:
- Package present:
- `graphify-out/GRAPH_REPORT.md`:
- `graphify-out/graph.json`:
- Graph action:
- Action taken:
- Notes:

## Karpathy

- Plugin/guidance present:
- Detection method:
- Action allowed:
- Action taken:
- Notes:

## Decisions

- Proceed to Stage 0:
- Required human decisions:
- Required installs/updates:
- Required graph action:
- Tokens to request from user (just-in-time, when needed):
