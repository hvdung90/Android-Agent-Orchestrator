# Usage Meter CLIs

Small local CLIs for tracking estimated Codex and Claude token usage.

## Commands

```bash
codex-usage-meter status
codex-usage-meter session
codex-usage-meter record --input-tokens 1000 --output-tokens 200
codex-usage-meter config --daily-token-limit 200000 --context-limit 128000

claude-usage-meter status
claude-usage-meter session
claude-usage-meter record --input-tokens 1000 --output-tokens 200 --cache-read-tokens 500
claude-usage-meter config --daily-token-limit 2000000 --context-limit 200000
```

The `run` command executes another command and records token usage if the output contains common usage fields:

```bash
claude-usage-meter run -- node call-anthropic.js
codex-usage-meter run -- codex exec "explain this repo"
```

## Data

Data is stored in:

```text
~/.usage-meter/codex.usage.json
~/.usage-meter/claude.usage.json
```

Config is stored in:

```text
~/.usage-meter/codex.config.json
~/.usage-meter/claude.config.json
```

`Remaining quota` is calculated from the configured local daily token limit. Provider account quota can only be shown exactly if the provider exposes that data to the CLI/API output.
