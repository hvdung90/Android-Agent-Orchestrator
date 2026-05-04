# Tooling Preflight

## Mode

`audit`

## Summary

- Ready for Stage 0: yes, with caveats
- Blocking gaps: none for read-only analysis
- Non-blocking gaps:
  - Graphify graph missing
  - Karpathy plugin not detected

## AI DevKit

- CLI present: yes
- Project config `.ai-devkit.json`: present
- Action allowed: no update in audit mode
- Action taken: none

## Android CLI

- CLI present: yes
- `android info` result: Android SDK path printed
- Action allowed: no update in audit mode
- Action taken: none

## Android skills

- Can list skills: yes
- Relevant skills found:
  - edge-to-edge
  - performance
- Action allowed: no install in audit mode
- Action taken: none

## Graphify

- CLI present: no
- Package present: no
- `graphify-out/GRAPH_REPORT.md`: missing
- `graphify-out/graph.json`: missing
- Graph action: report missing; do not build in audit mode

## Karpathy

- Plugin/guidance present: not detected
- Action allowed: no install in audit mode
- Action taken: none

## Decisions

- Proceed to Stage 0: yes for read-only repo analysis
- Required human decisions:
  - Approve Graphify install/build if architecture graph is required
  - Approve Karpathy plugin or project guidance before code-touching work
