# Tooling Preflight

## Mode

`audit`

## Summary

- Ready for Stage 0: yes, with caveats
- Blocking gaps: none for read-only analysis
- Non-blocking gaps:
  - Graphify graph missing (will build if approved)
  - Karpathy plugin not detected (will apply principles manually)
  - `atlassian.api_token` empty (will request from user when Jira link provided)

## Auth

- `.agent-auth.yaml`: present
- `atlassian.api_token`: empty
- `figma.personal_access_token`: empty
- `github.personal_access_token`: set
- Project overrides defined: 1 (name: "client-alpha", key: "CA")
- Notes: Tokens for atlassian and figma will be requested just-in-time when a Jira or Figma link is provided by the developer. github token available for private repo access.

## AI DevKit

- CLI present: yes
- CLI evidence: `ai-devkit 2.1.0`
- Project config `.ai-devkit.json`: present
- Action allowed: no update in audit mode
- Action taken: none
- Notes: config exists and looks current

## Android CLI

- CLI present: yes
- `android info` result: Android SDK path printed; version 34
- Action allowed: no update in audit mode
- Action taken: none
- Notes: skills list available

## Android skills

- Can list skills: yes
- Relevant skills searched: compose, edge-to-edge, performance, agp
- Relevant skills found: edge-to-edge, performance
- Relevant skills installed: edge-to-edge, performance
- Action allowed: no install in audit mode
- Action taken: none
- Notes: compose skill not found; will use android advisory memo as fallback

## Graphify

- CLI present: no
- Package present: no
- `graphify-out/GRAPH_REPORT.md`: missing
- `graphify-out/graph.json`: missing
- Graph action: report missing; do not build in audit mode
- Action taken: none
- Notes: approve bootstrap or refresh-graph mode to build graph before Discovery

## Karpathy

- Plugin/guidance present: not detected
- Detection method: checked CLAUDE.md, .claude/plugins/, .agents/skills/
- Action allowed: no install in audit mode
- Action taken: none
- Notes: principles will be applied manually at Stage 6 QA gate

## Serena

- uv present: yes
- Serena runnable: yes (`oraios-serena 0.3.1`)
- Backend: lsp (default); JetBrains opt-in not configured
- Kotlin LS stable: unknown (dev has not confirmed; pre-alpha)
- Action allowed: no install in audit mode
- Action taken: none
- Notes: ready for symbol-level queries; `get_diagnostics_*` disabled until Kotlin LS stability confirmed; non-blocking

## Decisions

- Proceed to Stage 0: yes for read-only task analysis
- Required human decisions:
  - Approve Graphify install/build if architecture graph is required for this task
  - Approve Karpathy plugin install or confirm manual application is acceptable
- Required installs/updates: none in audit mode
- Required graph action: none in audit mode; request refresh-graph mode to build
- Tokens to request from user (just-in-time, khi cần):
  - `atlassian.api_token` — khi developer cung cấp Jira hoặc Confluence link
  - `figma.personal_access_token` — khi developer cung cấp Figma link
