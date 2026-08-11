# Android CLI Compatibility

_Skill version: 6.1.1 — update this when SKILL.md bumps a minor or major version._

This ref makes Android CLI usage evidence-backed. Agents must discover command support before using optional `android` / `android studio` subcommands.

## Command discovery

Run at Stage -1 on the cache-miss path:

```bash
command -v android || true
android --help || true
android studio --help || true
adb version || true
```

For each command the task may need, record support as `supported | missing | unknown`:

```json
{
  "android_commands": {
    "docs_search": "supported | missing | unknown",
    "docs_fetch": "supported | missing | unknown",
    "screen_capture_annotate": "supported | missing | unknown",
    "layout": "supported | missing | unknown",
    "run": "supported | missing | unknown"
  },
  "android_studio_commands": {
    "version_lookup": "supported | missing | unknown",
    "render_compose_preview": "supported | missing | unknown",
    "analyze_file": "supported | missing | unknown",
    "find_declaration": "supported | missing | unknown",
    "find_usages": "supported | missing | unknown"
  },
  "adb": "present | missing"
}
```

Merge these fields into `.project-orchestration/memory/tooling-cache.json` alongside the existing top-level fields (`checked_at`, `valid_until`, `graph_commit`, `android_cli`, etc. — see `refs/contracts-and-artifacts.md § tooling-cache.json` for the full schema). TTL is the normal 24h. Later stages read from the cache; do not re-run help discovery unless the cache is expired or the command is not recorded.

## Use rule

An agent may call an Android command only when one of these is true:

- Stage -1 discovery recorded it as `supported`.
- Project docs, README, Makefile, Gradle task docs, or official Android CLI docs explicitly document it.
- The command is the listed fallback for a missing higher-level command.

If none apply, do not call the command. Use the fallback below or write an Unavailable-tool record from `refs/contracts-and-artifacts.md`.

## Fallback matrix

| Desired command | Fallback |
|---|---|
| `android docs search "<query>"` | Official Android docs by URL/search; record source URL in discovery output |
| `android docs fetch "<url>"` | Browser/fetch the official Android page; record source URL |
| `android studio version-lookup agp kotlin compose` | Read Gradle files, version catalogs, `gradle/libs.versions.toml`, `build.gradle*`, `settings.gradle*` |
| `android studio render-compose-preview <file>` | Repo-native screenshot/Paparazzi/Roborazzi/Compose preview test if present; otherwise Unavailable-tool record |
| `android studio analyze-file <file>` | Repo-native `lint`, `ktlint`, `detekt`, `spotless`, or Gradle static-analysis task; otherwise Unavailable-tool record |
| `android studio find-declaration <symbol>` | `rg`, IDE unavailable note, or architecture graph query |
| `android studio find-usages <symbol>` | `rg`, Gradle/module graph query, or architecture graph query |
| `android screen capture --annotate` | `adb exec-out screencap -p > evidence/screen.png`; annotate separately if an annotation tool exists |
| `android layout` | `adb shell uiautomator dump /sdcard/window.xml` then `adb exec-out cat /sdcard/window.xml > evidence/layout.xml` |
| `android run` | Gradle install task (`installDebug` or variant-specific install) plus `adb shell am start <package>/<activity>` |

## Evidence notes

- Fallback evidence is valid only when its detection command/output is recorded.
- If `adb devices` shows no attached device/emulator, use the degraded-evidence rule in `refs/contracts-and-artifacts.md`.
- A present command that fails is not "unavailable"; it blocks the relevant gate unless explicitly deferred by compliance policy.
