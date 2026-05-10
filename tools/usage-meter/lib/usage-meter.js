#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const provider = process.env.USAGE_METER_PROVIDER || "agent";
const providerDefaults = {
  codex: {
    contextLimit: 128000,
    dailyTokenLimit: 200000,
  },
  claude: {
    contextLimit: 200000,
    dailyTokenLimit: 2000000,
  },
};

const root = path.join(os.homedir(), ".usage-meter");
const configPath = path.join(root, `${provider}.config.json`);
const usagePath = path.join(root, `${provider}.usage.json`);

function ensureRoot() {
  fs.mkdirSync(root, { recursive: true, mode: 0o700 });
}

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return fallback;
  }
}

function writeJson(file, value) {
  ensureRoot();
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
}

function config() {
  return {
    ...providerDefaults[provider],
    warnAtPercent: 80,
    ...readJson(configPath, {}),
  };
}

function usage() {
  return readJson(usagePath, { sessions: [] });
}

function todayKey(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

function currentSessionId() {
  return process.env.USAGE_METER_SESSION || todayKey();
}

function parseIntArg(args, name, fallback = 0) {
  const index = args.indexOf(name);
  if (index === -1 || index + 1 >= args.length) return fallback;
  const parsed = Number.parseInt(args[index + 1], 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function flagValue(args, name) {
  const index = args.indexOf(name);
  if (index === -1 || index + 1 >= args.length) return undefined;
  return args[index + 1];
}

function estimateTokens(text) {
  if (!text) return 0;
  return Math.ceil(text.length / 4);
}

function extractUsage(text) {
  const result = {
    inputTokens: 0,
    outputTokens: 0,
    cacheCreationInputTokens: 0,
    cacheReadInputTokens: 0,
  };

  const usageObjectMatches = text.match(/\{[\s\S]*?"usage"\s*:\s*\{[\s\S]*?\}[\s\S]*?\}/g) || [];
  for (const match of usageObjectMatches) {
    try {
      const parsed = JSON.parse(match);
      const usage = parsed.usage || {};
      result.inputTokens += usage.input_tokens || usage.inputTokens || usage.prompt_tokens || 0;
      result.outputTokens += usage.output_tokens || usage.outputTokens || usage.completion_tokens || 0;
      result.cacheCreationInputTokens += usage.cache_creation_input_tokens || 0;
      result.cacheReadInputTokens += usage.cache_read_input_tokens || 0;
    } catch {
      // Fall through to regex extraction below.
    }
  }

  const pairs = [
    ["inputTokens", /(?:input_tokens|inputTokens|prompt_tokens)\D+(\d+)/gi],
    ["outputTokens", /(?:output_tokens|outputTokens|completion_tokens)\D+(\d+)/gi],
    ["cacheCreationInputTokens", /cache_creation_input_tokens\D+(\d+)/gi],
    ["cacheReadInputTokens", /cache_read_input_tokens\D+(\d+)/gi],
  ];

  for (const [key, regex] of pairs) {
    let match;
    while ((match = regex.exec(text)) !== null) {
      result[key] += Number.parseInt(match[1], 10) || 0;
    }
  }

  return result;
}

function addRecord(record) {
  const store = usage();
  store.sessions.push({
    provider,
    sessionId: currentSessionId(),
    day: todayKey(),
    timestamp: new Date().toISOString(),
    inputTokens: record.inputTokens || 0,
    outputTokens: record.outputTokens || 0,
    cacheCreationInputTokens: record.cacheCreationInputTokens || 0,
    cacheReadInputTokens: record.cacheReadInputTokens || 0,
    note: record.note || "",
  });
  writeJson(usagePath, store);
}

function sum(records) {
  return records.reduce(
    (acc, item) => {
      acc.inputTokens += item.inputTokens || 0;
      acc.outputTokens += item.outputTokens || 0;
      acc.cacheCreationInputTokens += item.cacheCreationInputTokens || 0;
      acc.cacheReadInputTokens += item.cacheReadInputTokens || 0;
      return acc;
    },
    {
      inputTokens: 0,
      outputTokens: 0,
      cacheCreationInputTokens: 0,
      cacheReadInputTokens: 0,
    },
  );
}

function printStatus(scope) {
  const cfg = config();
  const all = usage().sessions.filter((item) => item.provider === provider);
  const day = todayKey();
  const sessionId = currentSessionId();
  const records = scope === "session"
    ? all.filter((item) => item.sessionId === sessionId)
    : all.filter((item) => item.day === day);
  const totals = sum(records);
  const totalTokens = totals.inputTokens + totals.outputTokens + totals.cacheCreationInputTokens;
  const contextRemaining = Math.max(0, cfg.contextLimit - totalTokens);
  const dailyRecords = all.filter((item) => item.day === day);
  const dailyTotals = sum(dailyRecords);
  const dailyUsed = dailyTotals.inputTokens + dailyTotals.outputTokens + dailyTotals.cacheCreationInputTokens;
  const quotaRemaining = Math.max(0, cfg.dailyTokenLimit - dailyUsed);
  const usedPercent = cfg.dailyTokenLimit > 0 ? ((dailyUsed / cfg.dailyTokenLimit) * 100).toFixed(1) : "0.0";

  console.log(`${provider} usage meter`);
  console.log("");
  console.log(scope === "session" ? "Session" : "Today");
  console.log(`Input tokens:        ${totals.inputTokens}`);
  console.log(`Output tokens:       ${totals.outputTokens}`);
  if (provider === "claude") {
    console.log(`Cache write tokens:  ${totals.cacheCreationInputTokens}`);
    console.log(`Cache read tokens:   ${totals.cacheReadInputTokens}`);
  }
  console.log(`Total used:          ${totalTokens}`);
  console.log(`Context limit:       ${cfg.contextLimit}`);
  console.log(`Context remaining:   ${contextRemaining}`);
  console.log("");
  console.log("Quota");
  console.log(`Daily limit:         ${cfg.dailyTokenLimit}`);
  console.log(`Used today:          ${dailyUsed}`);
  console.log(`Remaining:           ${quotaRemaining}`);
  console.log(`Used:                ${usedPercent}%`);
}

function usageText() {
  return [
    `${provider}-usage-meter`,
    "",
    "Commands:",
    "  status                 Show today usage, context estimate, quota remaining",
    "  today                  Alias for status",
    "  session                Show current session usage",
    "  record [options]       Manually add usage",
    "  run -- <command...>    Run a command and record usage found in output",
    "  config [options]       Update local limits",
    "  reset-session          Remove records for the current session",
    "",
    "Options:",
    "  --input-tokens N",
    "  --output-tokens N",
    "  --cache-write-tokens N",
    "  --cache-read-tokens N",
    "  --note TEXT",
    "  --context-limit N",
    "  --daily-token-limit N",
    "",
    `Data: ${usagePath}`,
    `Config: ${configPath}`,
  ].join("\n");
}

function commandRecord(args) {
  const record = {
    inputTokens: parseIntArg(args, "--input-tokens"),
    outputTokens: parseIntArg(args, "--output-tokens"),
    cacheCreationInputTokens: parseIntArg(args, "--cache-write-tokens"),
    cacheReadInputTokens: parseIntArg(args, "--cache-read-tokens"),
    note: flagValue(args, "--note") || "",
  };
  addRecord(record);
  console.log("Recorded usage.");
}

function commandRun(args) {
  const delimiter = args.indexOf("--");
  const command = delimiter === -1 ? args : args.slice(delimiter + 1);
  if (command.length === 0) {
    console.error("Missing command after --");
    process.exit(2);
  }
  const child = spawnSync(command[0], command.slice(1), { encoding: "utf8" });
  if (child.stdout) process.stdout.write(child.stdout);
  if (child.stderr) process.stderr.write(child.stderr);

  const combined = `${child.stdout || ""}\n${child.stderr || ""}`;
  const extracted = extractUsage(combined);
  const total = extracted.inputTokens + extracted.outputTokens + extracted.cacheCreationInputTokens + extracted.cacheReadInputTokens;
  if (total > 0) {
    extracted.note = `run: ${command.join(" ")}`;
    addRecord(extracted);
  }
  process.exit(child.status || 0);
}

function commandConfig(args) {
  const next = config();
  const contextLimit = parseIntArg(args, "--context-limit", next.contextLimit);
  const dailyTokenLimit = parseIntArg(args, "--daily-token-limit", next.dailyTokenLimit);
  const warnAtPercent = parseIntArg(args, "--warn-at-percent", next.warnAtPercent);
  writeJson(configPath, { contextLimit, dailyTokenLimit, warnAtPercent });
  console.log(`Updated ${provider} config.`);
}

function commandResetSession() {
  const store = usage();
  const sessionId = currentSessionId();
  store.sessions = store.sessions.filter((item) => !(item.provider === provider && item.sessionId === sessionId));
  writeJson(usagePath, store);
  console.log("Reset current session.");
}

function main() {
  const args = process.argv.slice(2);
  const command = args[0] || "status";
  const rest = args.slice(1);

  if (["help", "--help", "-h"].includes(command)) {
    console.log(usageText());
    return;
  }
  if (command === "status" || command === "today") return printStatus("today");
  if (command === "session") return printStatus("session");
  if (command === "record") return commandRecord(rest);
  if (command === "run") return commandRun(rest);
  if (command === "config") return commandConfig(rest);
  if (command === "reset-session") return commandResetSession();

  console.error(`Unknown command: ${command}`);
  console.error("");
  console.error(usageText());
  process.exit(2);
}

main();
